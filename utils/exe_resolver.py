"""
Utility to resolve executable paths from either the local directory or system PATH.
"""

import os
import shutil
import sys

def get_executable_path(name: str) -> str | None:
    """
    Finds the absolute path to an executable.
    First checks the current working directory, then the system PATH.
    """
    exe_name = f"{name}.exe" if sys.platform == "win32" else name
    
    # Check local directory first
    local_path = os.path.join(os.getcwd(), exe_name)
    if os.path.isfile(local_path) and os.access(local_path, os.X_OK):
        return local_path
        
    # Check system PATH
    return shutil.which(name)
