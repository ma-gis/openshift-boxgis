import logging, os,sys, json, datetime, httpx
from fastapi import Depends, FastAPI, Request, HTTPException
from functools import lru_cache
from typing import Annotated
from box_sdk_gen import BoxClient, BoxJWTAuth, JWTConfig, AddShareLinkToFileSharedLink,AddShareLinkToFileSharedLinkAccessField
from pyproj import Transformer
from config import Settings
import uvicorn

app = FastAPI()

@lru_cache
def get_settings():
    return Settings()

# logging configuration
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
stream_handler = logging.StreamHandler(sys.stdout)
logger.addHandler(stream_handler)

# box configuration
settings = Settings()
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

# coordinate converter from 4326 to 3857 used by ArcGIS Online
transformer = Transformer.from_crs("EPSG:4326", "EPSG:3857")
ags_service_url = settings.ags_service_url

@app.get('/')
def index():
    logger.debug(f"Root was called!!!")
    return {'data': 'Awesome BoxGIS API!',
            'jwt': jwt_config}

@app.post("/webhook")
async def webhook(request: Request):
    body_dict = await request.json()

    # get box file id and webhook details
    webhook_id = body_dict['webhook']['id']
    webhook_trigger = body_dict['trigger']
    source_id = body_dict['source']['id']
    source_type = body_dict['source']['type']

    # get box file's capture metadata for location lat\long
    if webhook_trigger == "FILE.UPLOADED":
        file_info = client.files.get_file_by_id(file_id=source_id, fields=['id','type','name','metadata.global.boxCaptureV1'])
        metadata = file_info.metadata.extra_data['global']
          
        if 'boxCaptureV1' in file_info.metadata.extra_data['global']:
            metadata = file_info.metadata.extra_data['global']['boxCaptureV1']
            latitude,_,longitute,_ = metadata['location'].split(' ')
            x,y = transformer.transform(float(latitude),-float(longitute))
            created_at = f'{datetime.datetime.now().strftime("%m/%d/%Y %H:%M:%S")}'
            # add shared link
            file_info = client.shared_links_files.add_share_link_to_file(file_id=source_id, 
                                                                           fields=['id','type','name','shared_link'], 
                                                                           shared_link=AddShareLinkToFileSharedLink(access=AddShareLinkToFileSharedLinkAccessField.OPEN.value))

            features = [{"attributes":{"BoxFileID" : source_id,"SharedLink":file_info.shared_link.url, "FileName":file_info.name,"CreatedDate":created_at, "WebhookID":webhook_id, "WebhookTrigger":webhook_trigger},
                        "geometry" : {"x" : x,"y" : y}}]

            async with httpx.AsyncClient() as httpClient:
                response_add = await httpClient.post(f"{ags_service_url}/addFeatures?f=json", data={"features": json.dumps(features)})
                logger.debug(f"ArcGIS add features response:{response_add.status_code}")

    elif webhook_trigger == "FILE.TRASHED":
        async with httpx.AsyncClient() as httpClient:
            response_delete = await httpClient.post(f"{ags_service_url}/deleteFeatures?f=json", data={"where": f'BoxFileID={source_id}'})
            logger.debug(f"ArcGIS delete features response:{response_delete.status_code}")        

    return  {"success": True}


if __name__ == "__main__":
    uvicorn.run(app, host='0.0.0.0', port=8080)
