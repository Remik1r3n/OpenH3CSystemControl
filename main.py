# Open H3C System Control
# by Remik1r3n.
# This is Open Source software licensed under GPLv3.

import sys
import os
import keyboard
import ctypes
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QApplication, QSystemTrayIcon, QMenu, 
                             QMessageBox)
from PyQt6.QtGui import QIcon, QAction, QCursor
from PyQt6.QtCore import QObject, pyqtSignal, QTimer

from loguru import logger
from config import *
from _version import __version__
from languages.auto import apply_language
from modules.h3c_sound import start_h3c_sound, stop_h3c_sound
from modules.microphone_control import toggle_microphone, is_microphone_mute
from modules.check_official_h3ccc import is_official_h3c_control_center_running
from modules.switch_to_megaos import change_boot_order
from modules.single_instance import SingleInstance


def _set_safe_working_directory() -> None:
    """Set a stable working directory.

    When launched by Task Scheduler at logon, the working directory is often
    `C:\\Windows\\System32`, which can break relative file lookups.
    """
    try:
        if getattr(sys, "frozen", False):
            app_dir = os.path.dirname(sys.executable)
        else:
            app_dir = os.path.dirname(os.path.abspath(__file__))

        if app_dir:
            os.chdir(app_dir)
    except Exception:
        # Never block startup due to CWD issues.
        pass

# Load language constants based on system language.
_selected_language_module = apply_language(globals())
logger.info(f"Language module selected: {_selected_language_module}")

def show_startup_blocking_error(title: str, message: str) -> None:
    """Show a startup error in a way that is visible at logon on Windows."""
    if sys.platform == "win32":
        try:
            MB_OK = 0x00000000
            MB_ICONERROR = 0x00000010
            MB_SETFOREGROUND = 0x00010000
            MB_TOPMOST = 0x00040000
            ctypes.windll.user32.MessageBoxW(
                0,
                str(message),
                str(title),
                MB_OK | MB_ICONERROR | MB_SETFOREGROUND | MB_TOPMOST,
            )
            return
        except Exception:
            pass

    try:
        QMessageBox.critical(None, title, message)
    except Exception:
        # As a last resort, avoid crashing during error handling.
        print(f"{title}: {message}")

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

class KeySignal(QObject):
    """
    Helper class to emit signals from the background keyboard thread 
    to the main Qt UI thread.
    """
    mic_key_pressed = pyqtSignal()
    megaos_key_pressed = pyqtSignal()

class OpenH3CControlCenter:
    def __init__(self):
        logger.info("Initializing...")
        self.app = QApplication(sys.argv)
        if not IS_SKIP_H3CCC_CHECK:
            if is_official_h3c_control_center_running():
                show_startup_blocking_error(MSGBOX_ERROR_TITLE, MSG_H3CCC_RUNNING)
                sys.exit(1)
            else:
                logger.info("Official H3C Control Center not running, so continue.")
        else:
            logger.info("Skipping official H3C Control Center check.")

        # Prevent the app from exiting when the last window is closed 
        # (since we only use a tray icon)
        self.app.setQuitOnLastWindowClosed(False)

        # Signal bridge for thread safety
        self.signals = KeySignal()
        self.signals.mic_key_pressed.connect(self.handle_mic_key)
        self.signals.megaos_key_pressed.connect(self.handle_megaos_key)

        # State tracking
        self.sound_process = None

        # Setup UI
        self.setup_tray()

        # Setup Logic
        self.setup_hotkeys()

    def setup_tray(self):
        """Initialize the System Tray Icon and Menu."""
        self.tray_icon = QSystemTrayIcon()
        
        # Icon
        icon_path = resource_path("TrayIcon.png")
        if os.path.exists(icon_path):
            self.icon = QIcon(icon_path)
        else:
            # Fallback icon
            self.icon = QIcon.fromTheme("computer")
            
        self.tray_icon.setIcon(self.icon)
        self.tray_icon.setToolTip(MENU_TRAY_TOOLTIP)

        # Context Menu
        self.menu = QMenu()

        # Title Action (Disabled, just for info)
        title_action = QAction(MENU_TITLE, self.menu)
        title_action.setEnabled(False)
        self.menu.addAction(title_action)
        
        self.menu.addSeparator()

        # Toggle Microphone Trigger
        self.mic_action = QAction(MENU_TOGGLE_MIC, self.menu)
        self.mic_action.triggered.connect(self.handle_mic_key)
        self.menu.addAction(self.mic_action)

        # Switch to MegaOS Trigger
        self.mega_action = QAction(MENU_SWITCH_MEGAOS, self.menu)
        self.mega_action.triggered.connect(self.handle_megaos_key)
        self.menu.addAction(self.mega_action)

        # Start H3CSound Settings UI
        self.h3c_action = QAction(MENU_H3C_SOUND_SETTINGS, self.menu)
        self.h3c_action.triggered.connect(self.handle_h3c_sound)
        self.menu.addAction(self.h3c_action)

        self.menu.addSeparator()
        
        # About Action
        about_action = QAction(MENU_ABOUT, self.menu)
        about_action.triggered.connect(self.handle_about)
        self.menu.addAction(about_action)

        # Close Menu Action
        close_action = QAction(MENU_CLOSE, self.menu)
        close_action.triggered.connect(self.menu.close)
        self.menu.addAction(close_action)

        # Exit Action
        exit_action = QAction(MENU_EXIT, self.menu)
        exit_action.triggered.connect(self.quit_app)
        self.menu.addAction(exit_action)

        # Set the standard right-click context menu
        self.tray_icon.setContextMenu(self.menu)

        # Connect the activation signal to handle Left Clicks
        self.tray_icon.activated.connect(self.on_tray_activated)

        self.tray_icon.show()
        logger.info("Tray Icon initialized!")

    def on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            # Ensure the menu is on top
            self.menu.raise_()
            # Force popup and get input focus at current position
            self.menu.popup(QCursor.pos())
            # Focus capture patch for Windows
            if sys.platform == "win32":
                ctypes.windll.user32.SetForegroundWindow(int(self.menu.winId()))

    def setup_hotkeys(self):
        """
        Hooks global hotkeys using the keyboard library.
        We use callbacks to emit signals to keep the Qt Loop happy.
        """
        try:
            # F20: Microphone Toggle
            keyboard.on_press_key("f20", lambda _: self.signals.mic_key_pressed.emit())
            
            # F21: MegaOS Switch
            keyboard.on_press_key("f21", lambda _: self.signals.megaos_key_pressed.emit())
            
            logger.info("Global hotkeys hooked!")
        except ImportError:
            logger.error("Error: 'keyboard' library not found. Global keys won't work.")
        except Exception as e:
            logger.error(f"Failed to hook keys (Run as Admin?): {e}")

    def handle_h3c_sound(self):
        """Starts or stops the H3CSound Settings app."""
        start_h3c_sound()

    def handle_about(self):
        """Shows the About dialog."""
        msg_box = QMessageBox(self.menu) # Set parent to ensure icon shows in taskbar if needed, or just None.
        # But since we are tray only, let's just make it top most.
        msg_box.setWindowTitle(MSG_ABOUT_TITLE)
        msg_box.setText(MSG_ABOUT_TEXT_TEMPLATE.format(version=__version__))
        msg_box.setIcon(QMessageBox.Icon.Information)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        
        # Ensure it is on top
        msg_box.setWindowFlags(msg_box.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        msg_box.activateWindow()
        msg_box.raise_()
        msg_box.exec()

    def handle_mic_key(self):
        """Logic when F20 is pressed."""
        logger.info("Microphone Toggle Triggered")
        self.toggle_mic()

    def toggle_mic(self):
        """Toggle microphone on/off"""
        try:
            toggle_microphone()
            is_muted = is_microphone_mute()
            if is_muted:
                # Show notification
                self.tray_icon.showMessage(
                    MSG_MICROPHONE_TOGGLED_OFF,
                    MSG_MICROPHONE_TOGGLE,
                    QSystemTrayIcon.MessageIcon.Information,
                    2000
                )
            else:
                self.tray_icon.showMessage(
                    MSG_MICROPHONE_TOGGLED_ON,
                    MSG_MICROPHONE_TOGGLE,
                    QSystemTrayIcon.MessageIcon.Information,
                    2000
                )
        except Exception as e:
            print(f"Error toggling microphone: {e}")

    def handle_megaos_key(self):
        """Logic when F21 is pressed."""
        logger.info("MegaOS Switch Triggered!")
        msg_box = QMessageBox()
        
        # Set it to be always on top
        msg_box.setWindowFlags(msg_box.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        
        # Configure the message box
        msg_box.setWindowTitle(MSG_TITLE_SWITCH_MEGAOS)
        msg_box.setText(MSG_ARE_YOU_SURE_SWITCH_MEGAOS + "\n\n" + MSG_MEGAOS_SWITCH_WILL_REBOOT)
        msg_box.setIcon(QMessageBox.Icon.Question)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg_box.setDefaultButton(QMessageBox.StandardButton.No)  # Set default to No for safety
        
        # Show the message box and ensure it gets focus
        msg_box.activateWindow()
        msg_box.raise_()
        
        # Execute and get the result
        reply = msg_box.exec()
        
        if reply == QMessageBox.StandardButton.Yes:
            logger.info("User confirmed MegaOS switch.")
            boot_order_change_result = change_boot_order()
            if boot_order_change_result == 0:
                logger.info("Boot order changed successfully, rebooting...")
            else:
                logger.error(f"Failed to change boot order, error code: {boot_order_change_result}.")
                # Pop up an error message box
                error_box = QMessageBox()
                error_box.setWindowFlags(error_box.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
                error_box.setWindowTitle(MSGBOX_ERROR_TITLE)
                error_box.setText(MSG_FAILED_TO_SWITCH_MEGAOS + f"\nError code: {boot_order_change_result}")
                error_box.setIcon(QMessageBox.Icon.Critical)
                error_box.exec()
                return
            os.system("shutdown /r /t 0")
        else:
            logger.info("User canceled MegaOS switch.")

    def quit_app(self):
        """Clean up and exit."""
        logger.info("Exiting application...")
        try:
            keyboard.unhook_all()
        except Exception as e:
            logger.error(f"Error unhooking keyboard: {e}")

        # Kill the sound app
        try:
            stop_h3c_sound()
        except Exception as e:
            logger.error(f"Error stopping sound module: {e}")
        
        # Hide icon immediately so it doesn't linger in tray until mouseover
        self.tray_icon.hide() 
        self.app.quit()

    def run(self):
        sys.exit(self.app.exec())

if __name__ == "__main__":
    try:
        logger.info("Open H3C System Control starting...")

        _set_safe_working_directory()

        # Prevent multiple instances.
        _single_instance_lock = SingleInstance("OpenH3CSystemControl")
        if not _single_instance_lock.acquire():
            logger.warning("Another instance is already running; exiting.")
            try:
                msg = globals().get("MSG_ALREADY_RUNNING")
                title = globals().get("MSGBOX_ERROR_TITLE")
                if sys.platform == "win32":
                    ctypes.windll.user32.MessageBoxW(0, msg, title, 0x00000040)  # MB_ICONINFORMATION
                else:
                    print(msg)
            except Exception:
                pass
            sys.exit(0)

        control_center = OpenH3CControlCenter()
        control_center.run()
    except KeyboardInterrupt:
        sys.exit()