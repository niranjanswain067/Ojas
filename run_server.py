"""
Ojas AI Platform - Application Launcher.

Initializes the environment, starts the Uvicorn web server,
and opens the application in the user's default browser once ready.
"""

import sys
import threading
import time
import urllib.request
import webbrowser
from pathlib import Path

# Ensure project root is in sys.path
_PROJECT_ROOT = Path(__file__).resolve().parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))


def _wait_and_open_browser(url: str, timeout: float = 30.0) -> None:
    """Wait until the HTTP server is responsive, then open the browser."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with urllib.request.urlopen(f"{url}/api/health", timeout=1.0) as resp:
                if resp.status == 200:
                    time.sleep(0.5)
                    print(f"\n[INFO] Server ready! Opening browser at {url} ...\n")
                    webbrowser.open(url)
                    return
        except Exception:
            pass
        time.sleep(0.8)
    # Fallback: open browser after timeout
    webbrowser.open(url)


def main() -> None:
    import uvicorn
    from backend.app.config import get_settings

    settings = get_settings()
    host = settings.host or "127.0.0.1"
    port = settings.port or 8000
    url = f"http://{host}:{port}"

    print("=" * 60)
    print("         Launching Ojas AI Development Platform")
    print("=" * 60)
    print(f"\n[INFO] Starting server at {url} ...")
    print("[INFO] Serving FastAPI Backend API and compiled React Frontend.\n")

    # Start browser opener in background thread
    opener_thread = threading.Thread(
        target=_wait_and_open_browser,
        args=(url,),
        daemon=True,
    )
    opener_thread.start()

    # Run Uvicorn server
    uvicorn.run(
        "backend.app.main:app",
        host=host,
        port=port,
        log_level=settings.log_level.lower() if settings.log_level else "info",
    )


if __name__ == "__main__":
    main()
