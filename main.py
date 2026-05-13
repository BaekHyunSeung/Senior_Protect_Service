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
from Routers.Data_Receiving_Router import router as data_receiving_router

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
    logger.info("StartUp Complete!")

    yield

    logger.info("Shutdown: Close Database Engine...")
    await engine.dispose()
    logger.info("Shutdown Complete")


app = FastAPI(lifespan=lifespan)
app.include_router(data_receiving_router)


app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    uvicorn.run(app, host=APP_HOST, port=APP_PORT)