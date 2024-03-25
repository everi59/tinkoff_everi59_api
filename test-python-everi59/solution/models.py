from pydantic import BaseModel
from typing import Optional


class Region(BaseModel):
    name: Optional[str]


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    login: str | None = None


class UserData(BaseModel):
    login: str
    email: str
    countryCode: str
    isPublic: bool
    phone: Optional[str] = None
    image: Optional[str] = None


class UserUpdatedProfile(BaseModel):
    countryCode: Optional[str] = None
    isPublic: Optional[bool] = None
    phone: Optional[str] = None
    image: Optional[str] = None


class UserReg(BaseModel):
    login: str
    email: str
    password: str
    countryCode: str
    isPublic: bool
    phone: Optional[str] = None
    image: Optional[str] = None


class UserInDB(UserData):
    hashed_password: str


class FormData(BaseModel):
    login: str
    password: str


class UpdatePassword(BaseModel):
    oldPassword: str
    newPassword: str


class AddFriend(BaseModel):
    login: str


class RemoveFriend(BaseModel):
    login: str


class NewPost(BaseModel):
    content: str
    tags: list