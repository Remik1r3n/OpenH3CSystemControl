# Open H3C System Control
This is a open-source implementation of H3C System Control Center App, found on H3C Megabook device.

Original H3C System Control Center app is a buggy .NET app that sometimes delays startup and shutdown (Displays as .NET-BroadcastEventWindow.bf7771.0). 

This open-source implementation is written in Python using PyQt6 and aims to provide a more stable and reliable experience. 

We tries to replicate the original app's functionality as closely as possible. It creates a system tray icon with a menu to access these features, and runs in the background to handle key events.

## Supported Environments
This app is intended to run on the following operating systems:
- Windows 10 (not recommended)
- Windows 11 (recommended)

Although not very difficult, I don't think it's necessary to adapt this app to Linux.

This app must be run with administrator privileges.

## Features
- Enable/Disable Microphone key support (F20 actually)
- Switch to MegaOS button support (F21 actually)
- Start H3CSound app (If installed. Also we will kill it after 60s of closing, because the original app just leaves this garbage process running)

Note: "Linsee AI Key" is actually F13, but support for this key will not be added, since it's not ControlCenter related. If you don't use Linsee AI App, you can use PowerToys or AutoHotkey, to remap it to other keys, like Copilot Key (LShift+LWin+F23 actually), if you really want. (I don't.)

## Disclaimer
This software is provided "as is", without any warranty. Use it at your own risk. The author is not responsible for any damage or data loss that may occur from using this software.

You must have read all the code and understand what it does before using it.

AI assistance was used in the process of writing the code.

## License
This project is licensed under the GPL V3 License.
