from fastapi import FastAPI

from app.routes import auth


def create_app() -> FastAPI:
    app = FastAPI(title="WhiteBalloon")

    @app.get("/health", tags=["system"])
    async def healthcheck() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(auth.router)

    return app


app = create_app()
