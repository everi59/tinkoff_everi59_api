import jwt

from passlib.context import CryptContext
from fastapi.responses import JSONResponse
from fastapi import status
from datetime import datetime, timedelta

from .config import SECRET_KEY, ALGORITHM
from .models import UserInDB
from .database import get_user_from_db, get_user_profile_from_db

pwd_context = CryptContext(schemes=["sha256_crypt", "md5_crypt", "des_crypt"],
                           default="des_crypt", deprecated="auto")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def authenticate_user(password: str, user_dict: str):
    user = get_user(user_dict)
    if not user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                'reason': 'Пользователь с указанным логином не найден!'
            }
        )
    if not verify_password(password, user.hashed_password):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                'reason': 'Вы ввели неправильный пароль!'
            }
        )
    return user


def get_user(user_dict):
    if user_dict:
        return UserInDB(**user_dict)
    return None


def create_token(login: str, password: str):
    expires_delta = timedelta(hours=6)
    expire = datetime.utcnow() + expires_delta
    to_encode = {'login': login, 'password': password, 'exp': expire}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_token(token: str) -> dict | JSONResponse:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=ALGORITHM)
        return {'login': payload['login'], 'password': payload['password']}
    except jwt.InvalidTokenError:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={'reason': 'Некорректный токен аутентификации!'}
        )


def check_valid_auth_bearer(authorization):
    if not authorization or not authorization.startswith('Bearer '):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                'reason': 'Некорректный токен аунтефикации!'
            }
        )
    return None


def verify_token_data(user_data, token_data):
    return (user_data['login'] == token_data['login'] and
            verify_password(plain_password=token_data['password'], hashed_password=user_data['hashed_password']))


def token_data_validation(authorization):
    check_bearer = check_valid_auth_bearer(authorization)
    if isinstance(check_bearer, JSONResponse):
        return check_bearer
    token = authorization[7:]
    token_data = get_token(token)
    if isinstance(token_data, JSONResponse):
        return token_data
    user_json = get_user_profile_from_db(login=token_data['login'])
    user_data = get_user_from_db(login=token_data['login'])
    if user_json is None or user_data is None:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={'reason': 'Данные токена устарели или не верны!'}
        )
    if not verify_token_data(user_data=user_data, token_data=token_data):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={'reason': 'Данные токена не верны!'}
        )
    return user_json

