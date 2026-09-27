"""Resilient production entrypoint.

Works no matter the current working directory: it puts its own folder (which also
contains `app/`) on sys.path and chdirs there, so `app.main:app` always imports.

Render Start Command options (any one):
  python start.py                       (if this file sits at the service root)
  python folio-backend/start.py         (if the repo nests everything under folio-backend/)
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
os.chdir(HERE)

import uvicorn  # noqa: E402

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=False, workers=1)
