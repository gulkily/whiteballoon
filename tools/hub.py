#!/usr/bin/env python3
from __future__ import annotations

import uvicorn

from app.hub import hub_app


if __name__ == "__main__":
    uvicorn.run(
        hub_app,
        host="0.0.0.0",
        port=9100,
        reload=False,
    )
