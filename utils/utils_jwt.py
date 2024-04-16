import jwt
from typing import Optional
from DjangoHW.settings import SECRET_KEY

def generate_jwt_token(username: str) -> str:
    payload = {"username": username}
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return token

def check_jwt_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        print("Token expired")
    except jwt.InvalidTokenError:
        print("Invalid token")
    return None