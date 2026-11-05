import os
# from dotenv import load_dotenv
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

# load_dotenv()
api_key = os.environ["API_KEY"]


API_TOKEN = os.getenv("API_TOKEN", api_key)

bearer = HTTPBearer()


def auth(c: HTTPAuthorizationCredentials = Depends(bearer)):
    if c.credentials != API_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid token")
