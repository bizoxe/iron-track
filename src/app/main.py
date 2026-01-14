import structlog
import uvicorn
from server.core import create_app

app = create_app()
logger = structlog.stdlib.get_logger(__name__)

if __name__ == "__main__":
    uvicorn.run("main:app", port=8001, reload=True)
