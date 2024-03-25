import os

from environs import Env

SECRET_KEY = "9d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d"
ALGORITHM = "HS256"


def load_configs() -> dict:
    env = Env()
    env.read_env()
    return {'username': os.environ['POSTGRES_USERNAME'], 'password': os.environ['POSTGRES_PASSWORD'],
            'host': os.environ['POSTGRES_HOST'], 'port': os.environ['POSTGRES_PORT'],
            'data': os.environ['POSTGRES_DATABASE']}
