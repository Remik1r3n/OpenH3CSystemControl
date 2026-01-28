import keyboard
import comtypes
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from loguru import logger

logger.debug("Microphone control module loaded.")

def get_mic_endpoint():
    comtypes.CoInitialize() 

    devices = AudioUtilities.GetMicrophone() 
    interface = devices.Activate(
        IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    return cast(interface, POINTER(IAudioEndpointVolume))

def disable_microphone():
    try:
        volume = get_mic_endpoint()
        volume.SetMute(1, None)
        logger.info("Microphone set to Muted!")
    except Exception as e:
        logger.error(f"Disable Error: {e}")

def enable_microphone():
    try:
        volume = get_mic_endpoint()
        volume.SetMute(0, None)
        logger.info("Microphone set to Unmuted!")
    except Exception as e:
        logger.error(f"Enable Error: {e}")

def is_microphone_mute():
    try:
        volume = get_mic_endpoint()
        mute_state = volume.GetMute()
        if mute_state == 1:
            is_muted = True
        else:
            is_muted = False
        logger.info(f"Microphone mute state: {is_muted}")
        return is_muted
    except:
        return False

def toggle_microphone():
    try:
        if is_microphone_mute():
            enable_microphone()
        else:
            disable_microphone()
    except Exception as e:
        print(f"Hotkey Error: {e}")
    finally:
        pass

if __name__ == "__main__":
    print("This is a test.")
    print("Press F4 to toggle, F5 to query, ESC to quit.")
    
    comtypes.CoInitialize()
    
    keyboard.add_hotkey('f4', toggle_microphone)
    keyboard.add_hotkey('f5', is_microphone_mute)
    try:
        keyboard.wait('esc')
    except KeyboardInterrupt:
        pass