import sys
import os
import hashlib
from datetime import datetime
import subprocess
import logging

logger = logging.getLogger()

def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

def make_branch_name(url_list):
    """
    YYYY.MM.DD.HH.SS_sha1sum(url_list)
    """
    # Generate timestamp: YYYY.MM.DD.HH.SS
    timestamp = datetime.now().strftime("%Y.%m.%d.%H.%M.%S")
    
    # Calculate SHA1 hash of the url_list
    # Convert the list to a string representation and encode to bytes
    url_string = str(sorted(url_list))  # Sort to ensure consistent hash for same URLs
    sha1_hash = hashlib.sha1(url_string.encode('utf-8')).hexdigest()
    
    # Combine timestamp and hash
    ret = f"{timestamp}_{sha1_hash}"
    return ret

def subprocess_popen_poll(popen_args, print_func, root = None):
    logger.debug(f"running {popen_args}")
    process = subprocess.Popen(
        popen_args,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    for line in process.stdout:
        # Only log lines that end with newline (completed messages)
        if line.endswith('\n'):
            clean_line = line.strip()
            if clean_line:
                print_func(clean_line)
                if root:
                    root.update()
    
    returncode = process.wait()

    if returncode != 0:
        print_func(f"error {popen_args} (exit code: {returncode})")

    return returncode