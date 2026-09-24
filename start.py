"""Production entrypoint. Binds 0.0.0.0 on the platform-provided $PORT.

Use this as the Render Start Command:  python start.py
(equivalent to: uvicorn app.main:app --host 0.0.0.0 --port $PORT)
"""
import os

import uvicorn

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=False, workers=1)
