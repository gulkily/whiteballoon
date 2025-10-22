from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.modules import register_modules
from app.routes import auth, ui


def create_app() -> FastAPI:
    app = FastAPI(title="WhiteBalloon")

    @app.get("/health", tags=["system"])
    async def healthcheck() -> dict[str, str]:
        return {"status": "ok"}

    app.mount("/static", StaticFiles(directory="static"), name="static")

    app.include_router(auth.router)
    app.include_router(ui.router)
    register_modules(app)

    return app


app = create_app()
