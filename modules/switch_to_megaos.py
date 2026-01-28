# WARNING: WIP
# Non-functional

import subprocess
import os
from pathlib import Path

tool_path = Path(__file__).parent.joinpath("utilities", "UEFIVariableTool.exe").resolve()

def write_h3c_efivar():
    '''
    I have no idea what is it, but original app writes this.
    '''
    args = "BscInstallSystem@e896daf2-380d-4c77-aacb-098efbc05c9d@01"
    
    if not os.path.exists(tool_path):
        print(f"Error: {tool_path} not found.")
        return

    try:
        result = subprocess.run(
            [tool_path, args],
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
            
    except Exception as e:
        print(f"Execution exception: {e}")
