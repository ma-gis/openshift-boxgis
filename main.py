from fastapi import FastAPI, Depends
from functools import lru_cache
from typing import Annotated
import uvicorn
from config import Settings

app = FastAPI()

@lru_cache
def get_settings():
    return Settings()

@app.get('/')
def index():
    return {'data': 'Awesome FastAPI 3!'}

@app.get("/info")
async def info(settings: Annotated[Settings, Depends(get_settings)]):
    return {
        "app_name": settings.app_name,
        "admin_email": settings.admin_email,
        "items_per_user": settings.items_per_user,
    }

if __name__ == "__main__":
    uvicorn.run(app, host='0.0.0.0', port=8080)
