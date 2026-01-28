# Checks if official H3C Control Center is RUNNING.
# SystemControl.exe

import psutil
from loguru import logger
def is_official_h3c_control_center_running():
    logger.info("Checking for official H3C Control Center process...")
    for proc in psutil.process_iter(['name']):
        if proc.info['name'] == 'SystemControl.exe':
            logger.warning("Official H3C Control Center process found!")
            return True
    logger.info("Official H3C Control Center process not found.")
    return False