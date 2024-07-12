from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    ags_service_url: str
    client_id: str
    client_secret: str
    jwt_key_id: str
    private_key:str
    private_key_passphrase:str
    enterprise_id:str