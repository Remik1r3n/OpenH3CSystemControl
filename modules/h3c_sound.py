import os
import subprocess
import psutil
from PyQt6.QtCore import QTimer
from loguru import logger

# This rarely changes. 
# But if it does, update this path accordingly.
H3C_SOUND_PATH = r"C:\Program Files\Megabook\H3CSound\App\H3CLauncher.exe"
H3C_SOUND_PROCESS_NAME = "H3CApoSetting.exe"

# Store timer reference to avoid garbage collection
_h3c_sound_timer = None

def start_h3c_sound():
    """Starts the H3CSound Settings app, kills if already running, auto-kill after 60s."""
    global _h3c_sound_timer
    # Kill if already running
    for proc in psutil.process_iter(['name']):
        if proc.info['name'] == H3C_SOUND_PROCESS_NAME:
            logger.info("H3CSound is already running. Killing it.")
            stop_h3c_sound()
            break

    if os.path.exists(H3C_SOUND_PATH):
        try:
            subprocess.Popen(H3C_SOUND_PATH)
            logger.info("H3CSound started.")

            # After 60s kill it to avoid orphan processes
            _h3c_sound_timer = QTimer()
            _h3c_sound_timer.setSingleShot(True)
            _h3c_sound_timer.timeout.connect(stop_h3c_sound)
            _h3c_sound_timer.start(60000)
        except Exception as e:
            logger.warning(f"Failed to start H3CSound: {e}")
    else:
        logger.error(f"H3CSound executable not found at {H3C_SOUND_PATH}")

def stop_h3c_sound():
    """Kills the H3CSound app."""
    global _h3c_sound_timer
    for proc in psutil.process_iter(['name']):
        if proc.info['name'] == H3C_SOUND_PROCESS_NAME:
            try:
                proc.kill()
                logger.info("H3CSound process killed.")
            except psutil.AccessDenied:
                logger.error("Access denied when trying to kill process.")
            except Exception as e:
                logger.error(f"Error killing process: {e}")
    # Stop timer if running
    if _h3c_sound_timer is not None:
        _h3c_sound_timer.stop()
        _h3c_sound_timer = None
