import sys
import pytz
from datetime import datetime, timedelta
from PyQt5.QtCore import Qt, QEvent, QTimer, QPoint
from PyQt5.QtGui import QIcon, QFont, QFontDatabase, QGuiApplication
from PyQt5.QtWidgets import QApplication, qApp, QWidget, QSystemTrayIcon, QLabel, QMenu, QHBoxLayout

#TODO: Save these in a settings file and expose them in the settings window
pre_window_length = 2
window_length = 30

timezone = pytz.timezone("Asia/Tokyo")
font = None

class EventWindow(object):
    pre = None

    def __init__(self, start):
        self.start = datetime.strptime(start, "%H:%M")
        self.end = self.start + timedelta(minutes=window_length)
        if pre_window_length > 0:
            self.pre = self.start - timedelta(minutes=pre_window_length)

    def check(self, ct):
        s = self.start.replace(year=ct.year, month=ct.month, day=ct.day, tzinfo=timezone)
        e = self.end.replace(year=ct.year, month=ct.month, day=ct.day, tzinfo=timezone)
        
        return ct.time() >= s.time() and ct.time() < e.time()

    def check_pre(self, ct):
        if self.pre is None:
            return False

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
    target_seconds = 0.5 # TODO: Expose this in settings window

    framerate = 60
    
    transition_complete = True
    visible = False
    
    frame = 0
    target_frames = 0
    transition_timer = None

    def __init__(self, parent=None):
        super().__init__(parent)

        self.init()

    def init(self):
        self.setWindowFlags(Qt.FramelessWindowHint|Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setWindowTitle("SINoALICE Event Window Status")
        self.setWindowIcon(QIcon("icon.png"))
        self.resize(300, 54)

        self.setStyleSheet("background-color: #3b3325;")

        layout = QHBoxLayout()

        self.label = QLabel("Default notification text", font=font)
        self.label.setStyleSheet("color: #ffffff;")

        layout.addWidget(self.label)

        self.setLayout(layout)

        # TODO: Let the user to pick which screen to display the notification on
        self.framerate = QGuiApplication.primaryScreen().refreshRate()
        self.target_frames = self.framerate * self.target_seconds

        # TODO: Let the user pick the corner that the notification shows up in
        desktop = QApplication.desktop()
        sg = desktop.availableGeometry().bottomRight()
        p = QPoint(sg.x() - self.width() - 1, sg.y() - self.height())

        self.move(p)

    def start_show_transition(self):
        self.fade_in = True

        self.setWindowOpacity(0)
        self.show()

        self._start_transition()

    def start_hide_transition(self):
        self.fade_in = False

        self.setWindowOpacity(1)

        self._start_transition()

    def _start_transition(self):
        self.transition_complete = False

        self.frame = 0

        self.transition_timer = QTimer(self)
        self.transition_timer.setSingleShot(False)
        self.transition_timer.timeout.connect(self.update_transition)
        self.transition_timer.start((1 / self.framerate) * 1000)

    def update_transition(self):
        self.frame += 1
        
        if self.fade_in:
            opacity = self.frame / self.target_frames
        else:
            opacity = (self.target_frames - self.frame) / self.target_frames

        self.setWindowOpacity(opacity)

        if self.frame == self.target_frames:
            self.transition_timer.stop()
            self.transition_complete = True

            if self.fade_in:
                self.visible = True
            else:
                self.visible = False
                super().hide()

    def show_regular(self):
        self.label.setText("Upgrade Fodder window open!")

        # TODO: Play sound?

        if self.visible:
            return

        self.start_show_transition()

    def show_pre(self):
        self.label.setText("A window is about to open!")

        #TODO: Play sound?

        if self.visible:
            return
        
        self.start_show_transition()

    def hide(self):
        self.start_hide_transition()

class Window(QWidget):
    notification = None
    timer = None

    def __init__(self):
        super().__init__()

        self.init()

        self.notification = Notification()

        self.tray_icon = TrayIcon(QIcon("icon.png"), self)
        self.tray_icon.show()

        self.update()

    def init(self):
        self.setWindowTitle("SINoALICE Upgrade Fodder Event Alerter")
        self.setWindowIcon(QIcon("icon.png"))

        self.resize(300, 75)

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
            self.notification.show_pre()
        elif in_window:
            self.notification.show_regular()
        else:
            self.notification.hide()

    def unhide(self):
        self.setWindowState(Qt.WindowActive)
        QTimer.singleShot(0, self.show)

    def changeEvent(self, event):
        if event.type() == QEvent.WindowStateChange:
            if self.windowState() & Qt.WindowMinimized:
                QTimer.singleShot(0, self.hide)

        super().changeEvent(event)

    def closeEvent(self, event):
        self.tray_icon.hide()

        if self.notification.isVisible():
            self.notification.close()

        event.accept()

class TrayIcon(QSystemTrayIcon):
    def __init__(self, icon, parent=None):
        super().__init__(icon, parent)

        self.setToolTip("SINoALICE Upgrade Fodder Event Alerter")

        menu = QMenu(parent)

        show_action = menu.addAction("Show")
        show_action.triggered.connect(parent.unhide)

        menu.addSeparator()

        exit_action = menu.addAction("Exit")
        exit_action.triggered.connect(parent.close)

        self.setContextMenu(menu)

        self.activated.connect(self.clicked)

    def clicked(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            self.parent().unhide()

if __name__ == "__main__":
    app = QApplication(sys.argv)

    QFontDatabase.addApplicationFont("./font.otf")
    font = QFont("FOT-Pearl Std L", 16)

    window = Window()

    sys.exit(app.exec_())