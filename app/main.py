from fastapi import FastAPI

from app.modules import register_modules
from app.routes import auth


def create_app() -> FastAPI:
    app = FastAPI(title="WhiteBalloon")

    @app.get("/health", tags=["system"])
    async def healthcheck() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(auth.router)
    register_modules(app)

    return app


app = create_app()
