import sys
import pytz
from datetime import datetime, timedelta
from PyQt5.QtCore import Qt, QEvent, QTimer, QPoint
from PyQt5.QtGui import QIcon, QFont, QFontDatabase
from PyQt5.QtWidgets import QApplication, QWidget, QSystemTrayIcon, QLabel, QMenu, qApp

timezone = pytz.timezone("Asia/Tokyo")

pre_window_length = 2
window_length = 30

font = None

class EventWindow(object):
    def __init__(self, start):
        self.start = datetime.strptime(start, "%H:%M")
        self.pre = self.start - timedelta(minutes=pre_window_length)
        self.end = self.start + timedelta(minutes=window_length)

    def check(self, ct):
        s = self.start.replace(year=ct.year, month=ct.month, day=ct.day, tzinfo=timezone)
        e = self.end.replace(year=ct.year, month=ct.month, day=ct.day, tzinfo=timezone)
        
        return ct.time() >= s.time() and ct.time() < e.time()

    def check_pre(self, ct):
        p = self.pre.replace(year=ct.year, month=ct.month, day=ct.day, tzinfo=timezone)
        s = self.start.replace(year=ct.year, month=ct.month, day=ct.day, tzinfo=timezone)

        return ct.time() >= p.time() and ct.time() < s.time()

windows = [
    EventWindow("01:00"),
    EventWindow("07:30"),
    EventWindow("12:00"),
    EventWindow("19:30"),
    EventWindow("22:30")
]

class Notification(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.init()

    def init(self):
        self.setWindowFlags(Qt.FramelessWindowHint|Qt.WindowStaysOnTopHint)
        self.setWindowTitle("SINoALICE Event Window Status")
        self.setWindowIcon(QIcon("icon.png"))
        self.resize(300, 40)

        self.setStyleSheet("background-color: #3b3325;")

        self.label = QLabel("Default notification text", self, font=font)
        self.label.setStyleSheet("color: #ffffff;")
        
        sg = QApplication.desktop().availableGeometry().bottomRight()
        p = QPoint(sg.x() - self.rect().width(), sg.y() - self.rect().height())

        self.move(p)

    def show_regular(self):
        self.label.setText("Upgrade Fodder window open!")
        self.show()

    def show_pre(self):
        self.label.setText("A window is about to open!")
        self.show()

class Window(QWidget):
    notification = None
    timer = None

    def __init__(self):
        super().__init__()

        self.init()

    def init(self):
        self.setWindowTitle("SINoALICE Upgrade Fodder Event Alerter")
        self.setWindowIcon(QIcon("icon.png"))

        self.resize(250, 150)

        self.temp_label = QLabel("There'll be options here later", self, font=font)
        
        frame = self.frameGeometry()
        center_point = QApplication.desktop().availableGeometry().center()
        frame.moveCenter(center_point)

        self.move(center_point - self.rect().center())

        self.timer = QTimer(self)
        self.timer.setSingleShot(False)
        self.timer.timeout.connect(self.update)
        self.timer.start(1000 * 30)

        self.show()

        self.update()

    def update(self):
        ct = datetime.now(timezone)

        in_pre_window = False
        in_window = False

        for t in windows:
            if t.check_pre(ct):
                in_pre_window = True
                break

            if t.check(ct):
                in_window = True
                break

        if in_pre_window:
            self.showNotification(kind="pre")
        elif in_window:
            self.showNotification(kind="regular")
        else:
            self.hideNotification()

    def unhide(self):
        self.setWindowState(Qt.WindowActive)
        QTimer.singleShot(0, self.show)

    def showNotification(self, kind="regular"):
        if self.notification is None:
            self.notification = Notification()

        if kind == "regular":
            self.notification.show_regular()
        elif kind == "pre":
            self.notification.show_pre()

    def hideNotification(self):
        if self.notification is None:
            return

        self.notification.hide()

    def changeEvent(self, event):
        if event.type() == QEvent.WindowStateChange:
            if self.windowState() & Qt.WindowMinimized:
                QTimer.singleShot(0, self.hide)

        super().changeEvent(event)

class TrayIcon(QSystemTrayIcon):
    def __init__(self, icon, parent = None):
        super().__init__(icon, parent)

        self.setToolTip("SINoALICE Upgrade Fodder Event Alerter")

        menu = QMenu(parent)

        show_action = menu.addAction("Show")
        show_action.triggered.connect(parent.unhide)

        menu.addSeparator()

        exit_action = menu.addAction("Exit")
        exit_action.triggered.connect(qApp.quit)

        self.setContextMenu(menu)

if __name__ == "__main__":
    app = QApplication(sys.argv)

    QFontDatabase.addApplicationFont("./font.otf")
    font = QFont("FOT-Pearl Std L", 16)

    window = Window()

    tray_icon = TrayIcon(QIcon("icon.png"), window)
    tray_icon.show()

    sys.exit(app.exec_())