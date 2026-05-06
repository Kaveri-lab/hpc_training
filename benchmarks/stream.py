import os
import sys
import subprocess
from config import STREAM_CFG

def check_binary():
    binary = STREAM_CFG["binary"]
    if os.path.isfile(binary) and os.access(binary, os.X_OK):
        return True
    return False

def ensure_source():
    src = STREAM_CFG["src"]
    url = STREAM_CFG["src_url"]
    os.makedirs(os.path.dirname(src), exist_ok=True)


    if os.path.isfile(src):
        print(f"[stream] source file found at {src}")
        return

    print(f"[stream] source not found, downloading from {url}")
    ret = subprocess.run(["wget", "-q", "-O", src, url])
    if ret.returncode != 0:
        print("[stream] download failed, check internet connection")
        sys.exit(1)
    print(f"[stream] download complete: {src}")

def get_build_cmd():
    s  = STREAM_CFG
    src    = STREAM_CFG["src"]
    cc = s["build"]["cc"]
    flags = s["build"]["flags"]
    size   = STREAM_CFG["build"]["array_size"]
    binary = STREAM_CFG["binary"]
    return f"{cc} {flags} -DSTREAM_ARRAY_SIZE={size} -o {binary} {src} -lm"

def get_run_cmd(threads):
    binary     = STREAM_CFG["binary"]
    iterations = STREAM_CFG["iterations"]

    lines = []
    for i in range(1, iterations + 1):
        lines.append(f'echo "--- threads={threads} iteration={i} ---"')
        lines.append(f"export OMP_NUM_THREADS={threads}")
        lines.append(f"{binary}")
    return "\n".join(lines)
