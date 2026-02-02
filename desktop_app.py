import subprocess
import sys
import time
import webbrowser
import os
import socket

# Explicitly import gradio to ensure PyInstaller bundles it.
# This is a workaround for the ModuleNotFoundError that can occur
# when gradio is imported by a secondary script (like app.py).
import gradio

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOCK_FILE = os.path.join(BASE_DIR, "sadtalker.lock")

# This script can be in one of two modes:
# 1. Main mode: Checks for other instances, launches the backend, and opens the browser.
# 2. Backend mode: (when called with 'run_backend' arg). Runs the Gradio server.

# --- Backend Mode ---
if len(sys.argv) > 1 and sys.argv[1] == 'run_backend':
    # Create a lock to signal that the backend is running.
    try:
        with open(LOCK_FILE, "w") as f:
            f.write(str(os.getpid()))
        
        # Import and start the SadTalker application
        import launcher
        launcher.prepare_environment()
        launcher.start()  # This is a blocking call
    finally:
        # Clean up the lock file when the server is stopped or crashes.
        if os.path.exists(LOCK_FILE):
            os.remove(LOCK_FILE)
    sys.exit(0)

# --- Main Mode ---

# Check if an instance is already running using the lock file.
if os.path.exists(LOCK_FILE):
    print("SadTalker is already running. Opening the web UI.")
    webbrowser.open("http://127.0.0.1:7860", new=1, autoraise=True)
    sys.exit(0)

# Launch the backend process. The executable itself is the script.
command = [sys.executable, "run_backend"]

print("Starting SadTalker backend...")
subprocess.Popen(command, cwd=BASE_DIR)
proc = subprocess.Popen(command, cwd=BASE_DIR)

# Wait for the server to start up by polling the port.
print("Waiting for Gradio server to start...")
for _ in range(60): # Wait for up to 60 seconds
    try:
        with socket.create_connection(("127.0.0.1", 7860), timeout=1):
            webbrowser.open("http://127.0.0.1:7860", new=0, autoraise=True)
            sys.exit(0)
            break
    except (ConnectionRefusedError, socket.timeout):
        time.sleep(1)
else:
    print("Failed to start the Gradio server in time.")
    proc.terminate()
    sys.exit(1)

print("Failed to start the Gradio server in time.")
sys.exit(1)
print("SadTalker is running. Close this window to stop the application.")
try:
    proc.wait()
except KeyboardInterrupt:
    proc.terminate()
