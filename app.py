from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY
from contextlib import asynccontextmanager
import time
import uvicorn

import log as Log
import upload
import os

# Set Google Vision credentials (absolute path)
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = r"E:\Google Visioin\semiotic-cove-448406-j3-f2bc0fc5da35.json"


@asynccontextmanager
async def lifespan(app: FastAPI):
    Log.log.info("App starting")
    yield
    Log.log.info("App ended")


app = FastAPI(lifespan=lifespan)


# Custom validation error handler
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    first_error = exc.errors()[0].get("msg", "Invalid input")
    return JSONResponse(
        status_code=HTTP_422_UNPROCESSABLE_ENTITY,
        content={"message": first_error},
    )


# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_headers=["*"],
    allow_methods=["*"],
)


# Logging middleware
@app.middleware("http")
async def middleware(request: Request, call_next):
    start = time.time()
    try:
        body = await request.json()
    except Exception:
        body = None

    response = await call_next(request)
    process = (time.time() - start) * 1000
    Log.log.info(
        f"{request.method} {request.url.path} | body:{body} | "
        f"statuscode:{response.status_code} | processtime:{process:.2f}ms"
    )
    return response


# Register routers
app.include_router(upload.router, prefix="/api", tags=["Upload"])


if __name__ == "__main__":
    uvicorn.run("app:app", host="192.168.0.109", port=3000, reload=True)
