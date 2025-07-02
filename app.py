from fastapi import FastAPI
import asyncio
from main import main_loop

app = FastAPI()

@app.get("/")
async def root():
    # Run your main loop whenever this endpoint is hit
    await main_loop()
    return {"status": "done"}
