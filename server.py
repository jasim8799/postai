import os
import asyncio
from fastapi import FastAPI
from fastapi.responses import PlainTextResponse

from main import main_with_posting_cycle

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(main_with_posting_cycle())

@app.get("/")
async def root():
    return PlainTextResponse("✅ Background task started on startup")

@app.get("/healthz")
def healthz():
    return PlainTextResponse("OK")
