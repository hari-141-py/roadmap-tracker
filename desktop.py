"""Desktop launcher: runs the Flask app in the background and shows it in a native window."""
import logging
import os
import socket
import sys
import threading
import time
import urllib.request

os.environ["DEVOPS_TRACKER_DESKTOP"] = "1"

import webview  # pywebview
from werkzeug.serving import make_server

from app import DATA_DIR, app

DATA_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    filename=str(DATA_DIR / "app.log"),
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def main():
    port = free_port()
    server = make_server("127.0.0.1", port, app, threaded=True)
    threading.Thread(target=server.serve_forever, daemon=True).start()

    url = f"http://127.0.0.1:{port}/"
    for _ in range(50):  # wait until Flask answers
        try:
            urllib.request.urlopen(url + "api/health", timeout=0.5)
            break
        except OSError:
            time.sleep(0.1)

    webview.settings["ALLOW_DOWNLOADS"] = True  # lets "Download backup file" show a save dialog
    webview.create_window("DevOps Tracker", url, width=1280, height=860, min_size=(480, 600))
    webview.start()
    server.shutdown()


if __name__ == "__main__":
    try:
        main()
    except Exception:
        logging.exception("App crashed")
        raise
