import os
def _find_chromium_executable() -> str:
    paths = ["/usr/bin/chromium", "/usr/bin/chromium-browser"]
    for path in paths:
        if os.path.exists(path):
            return path
    raise FileNotFoundError("Chromium not found")
