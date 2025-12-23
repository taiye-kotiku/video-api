from pydantic import BaseSettings


class Settings(BaseSettings):
    r2_access_key_id: str
    r2_secret_access_key: str
    r2_bucket_name: str
    r2_account_id: str
    r2_endpoint: str = "https://7b056fa69c87d450715caeb36205e766.r2.cloudflarestorage.com"
