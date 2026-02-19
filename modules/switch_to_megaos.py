import subprocess
import os
from pathlib import Path

uefi_var_tool_path = Path(__file__).parent.joinpath("utilities", "UEFIVariableTool.exe").resolve()

bootorder_change_tool_path = Path(__file__).parent.joinpath("utilities", "ChangeBootOrderFirst.ps1").resolve()

def change_boot_order(is_run_as_admin:bool=False):
    '''
    Use Powershell script to change the boot order, set MegaOS as the first boot option.
    '''
    if not os.path.exists(bootorder_change_tool_path):
        print(f"Error: {bootorder_change_tool_path} not found.")
        return 6

    try:
        if is_run_as_admin:
        # Request admin privileges using Start-Process with -Verb RunAs
            ps_command = f"Start-Process powershell -ArgumentList '-ExecutionPolicy Bypass -File \"{bootorder_change_tool_path}\"' -Verb RunAs -WindowStyle Hidden -Wait"
        else:
            ps_command = f"& '{bootorder_change_tool_path}'"
        
        result = subprocess.run(
            ["powershell", "-Command", ps_command],
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        
        # Note: When running with Start-Process, we might not get the script's exit code directly
        # checking result.returncode checks if the launch was successful.
        if result.returncode == 0:
            print("Run Success")
            print("Output:", result.stdout)
        else:
            print("Run Fail")
            print("Error:", result.stderr)

        return result.returncode
            
    except Exception as e:
        print(f"Execution exception: {e}")
        return 5

def write_h3c_efivar():
    '''
    I have no idea what is it, but original app writes this.
    It's not used for switching to MegaOS, but I will keep it here just in case someone wants to use it.
    '''
    args = "BscInstallSystem@e896daf2-380d-4c77-aacb-098efbc05c9d@01"
    
    if not os.path.exists(uefi_var_tool_path):
        print(f"Error: {uefi_var_tool_path} not found.")
        return 6

    try:
        result = subprocess.run(
            [uefi_var_tool_path, args],
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        
        if result.returncode == 0:
            print("Run Success")
            print("Output:", result.stdout)
        else:
            print("Run Fail")
            print("Error:", result.stderr)
        
        return result.returncode
    except Exception as e:
        print(f"Execution exception: {e}")
        return 5