import logging
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from sqlmodel import SQLModel

import DB.Entity
from DB.DB import engine
from Ingest.protobuf_receiver import protobuf_ingest_receiver

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

load_dotenv()

APP_HOST = os.getenv("APP_HOST", "0.0.0.0")
APP_PORT = int(os.getenv("APP_PORT", 8000))
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")

@asynccontextmanager
async def lifespan(app: FastAPI):
    del app
    logger.info("StartUp: Connect Database...")
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    await protobuf_ingest_receiver.start()
    logger.info("StartUp Complete!")

    yield

    logger.info("Shutdown: Stop protobuf ingest receiver...")
    await protobuf_ingest_receiver.stop()
    logger.info("Shutdown: Close Database Engine...")
    await engine.dispose()
    logger.info("Shutdown Complete")


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    uvicorn.run(app, host=APP_HOST, port=APP_PORT)