import structlog
import uvicorn

from server.core import create_app

app = create_app()
logger = structlog.stdlib.get_logger(__name__)


@app.get("/")
def get_hello() -> dict[str, str]:
    logger.info("Getting greeting message")
    return {"message": "hello from FastAPI"}


if __name__ == "__main__":
    uvicorn.run("main:app", port=8001, reload=True)
