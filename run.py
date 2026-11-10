"""Amrapali University - TQM Course Project Entry Point.

Usage:
  python run.py          # Launches the Modern Web Application (Default)
  python run.py --web    # Launches the Modern Web Application on http://127.0.0.1:5001/
  python run.py --gui    # Launches the Desktop Tkinter GUI
"""

import sys
import argparse
import socket
import os
import subprocess
import time


def free_port(port: int):
    """If port is occupied by a stale/previous process, free it so the server starts seamlessly."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", port)) == 0:
                cmd = ["lsof", "-t", f"-i:{port}"]
                out = subprocess.check_output(cmd, stderr=subprocess.DEVNULL).decode().strip()
                if out:
                    pids = [int(p) for p in out.split() if p.isdigit() and int(p) != os.getpid()]
                    for pid in pids:
                        try:
                            os.kill(pid, 15)
                        except ProcessLookupError:
                            pass
                    time.sleep(0.3)
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s2:
                        if s2.connect_ex(("127.0.0.1", port)) == 0:
                            for pid in pids:
                                try:
                                    os.kill(pid, 9)
                                except ProcessLookupError:
                                    pass
                            time.sleep(0.3)
    except Exception:
        pass


def start_web(port: int = 5001, host: str = "0.0.0.0"):
    free_port(port)
    from web_app import run_web
    run_web(host=host, port=port)


def start_gui():
    from main import main
    main()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Amrapali Inventory & TQM Management System")
    parser.add_argument("--gui", "--desktop", dest="gui", action="store_true", help="Launch Tkinter Desktop GUI")
    parser.add_argument("--web", dest="web", action="store_true", help="Launch Web Application (Default)")
    parser.add_argument("--port", type=int, default=5001, help="Port for web server (default: 5001)")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host interface (default: 0.0.0.0 for LAN/Wi-Fi access)")
    args = parser.parse_args()

    if args.gui:
        start_gui()
    else:
        start_web(port=args.port, host=args.host)
