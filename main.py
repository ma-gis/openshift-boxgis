import logging, os,sys, json, datetime, httpx
from fastapi import Depends, FastAPI, Request, HTTPException
from functools import lru_cache
from typing import Annotated
from box_sdk_gen import BoxClient, BoxJWTAuth, JWTConfig
from pyproj import Transformer
from config import Settings
import uvicorn

app = FastAPI()

@lru_cache
def get_settings():
    return Settings()


@app.get('/')
def index():
    return {'data': 'Awesome BoxGIS API!'}

@app.get("/info")
async def info(settings: Annotated[Settings, Depends(get_settings)]):

    jwt_config = JWTConfig(
        client_id=settings.client_id,
        client_secret=settings.client_secret,
        jwt_key_id=settings.jwt_key_id,
        private_key=settings.private_key,
        private_key_passphrase=settings.private_key_passphrase,
        enterprise_id=settings.enterprise_id,
    )

    auth = BoxJWTAuth(config=jwt_config)
    client =  BoxClient(auth=auth)

    return {
        "ok": "Box client authenticated!"
    }

if __name__ == "__main__":
    uvicorn.run(app, host='0.0.0.0', port=8080)
