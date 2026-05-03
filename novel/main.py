import os

import uvicorn

from novel import get_app

app = get_app()



if __name__ == '__main__':
    uvicorn.run(
        app="novel.main:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
        log_level="info",
    )