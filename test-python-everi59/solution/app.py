# -.- encoding:utf-8 -.-
import re
import uuid

from datetime import datetime
from string import ascii_lowercase, ascii_uppercase
from typing import Optional, Annotated
from fastapi import FastAPI, Header
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer
from starlette import status

from .database import (get_countries, get_country, check_user, check_country_code,
                      register_user,
                      get_user_from_db, get_user_profile_from_db, update_user_profile, check_user_for_update,
                      get_user_hashed_password, get_friends_from_database,
                      add_friend_to_database, remove_friend_from_database, insert_new_post,
                      get_post_from_db, get_feed_by_author, get_reaction,
                      update_reaction, insert_reaction, update_posts_counts)
from .models import Region, UserReg, FormData, UserUpdatedProfile, UpdatePassword, AddFriend, RemoveFriend, \
    NewPost
from .service import verify_password, get_password_hash, authenticate_user, create_token, token_data_validation

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/sign-in")


@app.get('/api/ping')
def send():
    return {"status": "ok"}


@app.get('/api/countries')
def countries(region: Optional[Region] = None):
    return get_countries(region=region)


@app.get('/api/countries/{alpha2}')
def country(alpha2: str):
    return get_country(alpha2=alpha2.upper())


@app.post('/api/auth/register')
def register(user_data: UserReg):
    error = None
    check_user_exists = check_user(
        user_data.login,
        user_data.email,
        user_data.phone
    )
    if check_user_exists:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                'reason': 'Юзер с таким email/login/phone уже существует!'
            }
        )
    if not re.fullmatch(r'[a-zA-Z0-9-]{1,30}', user_data.login):
        error = 'Вы ввели некорректный логин!'
    elif not len(user_data.email) <= 50:
        error = 'Вы ввели некорректный email'
    elif (
            not 6 <= len(user_data.password) <= 100
            or not any(i in ascii_lowercase for i in user_data.password)
            or not any(i in ascii_uppercase for i in user_data.password)
            or not any(i in '0123456789' for i in user_data.password)
    ):
        error = 'Вы ввели некорректный пароль!'
    elif not check_country_code(user_data.countryCode):
        error = 'Вы ввели некорректный код страны'
    elif user_data.phone:
        if not re.fullmatch(r'\+\d+', user_data.phone):
            error = 'Вы ввели некорректный номер телефона!'
    elif user_data.image:
        if not len(user_data.image) <= 200:
            error = 'Вы отправили некорректное фото!!'
    if error:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                'reason': error
            }
        )
    else:
        register_user(
            email=user_data.email,
            login=user_data.login,
            phone=user_data.phone,
            countryCode=user_data.countryCode,
            isPublic=user_data.isPublic,
            hashed_password=get_password_hash(user_data.password),
            image=user_data.image
        )
        result = {
            'login': user_data.login,
            'email': user_data.email,
            'countryCode': user_data.countryCode,
            'isPublic': user_data.isPublic
        }
        if user_data.phone:
            result['phone'] = user_data.phone
        if user_data.image:
            result['image'] = user_data.image
        return JSONResponse(status_code=status.HTTP_201_CREATED,
                            content={'profile': result})


@app.post('/api/auth/sign-in')
async def user_sign_in(form_data: FormData):
    user_dict = get_user_from_db(login=form_data.login)
    user_auth = authenticate_user(password=form_data.password, user_dict=user_dict)
    if isinstance(user_auth, JSONResponse):
        return user_auth
    token = create_token(form_data.login, form_data.password)
    return {'token': token}


@app.get('/api/me/profile')
def get_user_profile(authorization: Annotated[str | None, Header()]):
    user_json = token_data_validation(authorization=authorization)
    if isinstance(user_json, JSONResponse):
        return user_json
    return user_json


@app.patch('/api/me/profile')
def get_user_profile(authorization: Annotated[str | None, Header()], user_updated_profile: UserUpdatedProfile):
    user_json = token_data_validation(authorization=authorization)
    if isinstance(user_json, JSONResponse):
        return user_json
    error = False
    check_user_exists = check_user_for_update(
        user_json['login'],
        user_updated_profile.phone
    )
    if check_user_exists:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                'reason': 'Такой номер телефона уже занят!'
            }
        )
    if user_updated_profile.countryCode:
        if not check_country_code(user_updated_profile.countryCode):
            error = 'Вы ввели некорректный код страны'
        else:
            user_json['countryCode'] = user_updated_profile.countryCode
    if user_updated_profile.phone:
        if not re.fullmatch(r'\+\d+', user_updated_profile.phone):
            error = 'Вы ввели некорректный номер телефона!'
        else:
            user_json['phone'] = user_updated_profile.phone
    if user_updated_profile.isPublic:
        user_json['isPublic'] = True
    else:
        user_json['isPublic'] = False
    if user_updated_profile.image:
        if not len(user_updated_profile.image) <= 200:
            error = 'Вы отправили некорректное фото!!'
        else:
            user_json['image'] = user_updated_profile.image
    if error:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                'reason': error
                }
        )
    else:
        update_user_profile(**user_json)
        return JSONResponse(status_code=status.HTTP_200_OK,
                            content=user_json)


@app.get('/api/profiles/{login_to_get}')
def send_profile(login_to_get: str, authorization: Annotated[str | None, Header()]):
    user_json = token_data_validation(authorization=authorization)
    if isinstance(user_json, JSONResponse):
        return user_json
    user_to_get_json = get_user_profile_from_db(login=login_to_get)
    if user_to_get_json is None:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={'reason': 'Данного пользователя не нашлось!'}
        )
    if user_json['login'] == login_to_get:
        return user_to_get_json
    elif user_to_get_json['isPublic'] is True:
        return user_to_get_json
    elif user_json['login'] in get_friends_from_database(friend_from_login=login_to_get):
        return user_to_get_json
    else:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={'reason': 'Нет доступа к данному юзеру!'}
        )


@app.post('/api/me/updatePassword')
def updating_password(update_password: UpdatePassword, authorization: Annotated[str | None, Header()]):
    user_json = token_data_validation(authorization=authorization)
    if isinstance(user_json, JSONResponse):
        return user_json
    user_hashed_password = get_user_hashed_password(user_json['login'])
    if not verify_password(update_password.oldPassword, user_hashed_password):
        return JSONResponse(status_code=status.HTTP_403_FORBIDDEN,
                            content={'reason': 'Старый пароль не совпадает!'})
    else:
        if (
                not 6 <= len(update_password.newPassword) <= 100
                or not any(i in ascii_lowercase for i in update_password.newPassword)
                or not any(i in ascii_uppercase for i in update_password.newPassword)
                or not any(i in '0123456789' for i in update_password.newPassword)
        ):
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST,
                                content={'reason': 'Вы ввели некорректный пароль!'})
        else:
            update_user_profile(login=user_json['login'],
                                hashed_password=get_password_hash(update_password.newPassword))
            return JSONResponse(status_code=status.HTTP_200_OK,
                                content={'status': 'ok'})


@app.post('/api/friends/add')
def adding_friend(add_friend: AddFriend, authorization: Annotated[str | None, Header()]):
    user_json = token_data_validation(authorization=authorization)
    if isinstance(user_json, JSONResponse):
        return user_json
    friends = get_friends_from_database(friend_from_login=user_json['login'])
    if add_friend.login in friends or user_json['login'] == add_friend.login:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"status": "ok"}
        )
    else:
        friend_to_json = get_user_profile_from_db(login=add_friend.login)
        if friend_to_json:
            add_friend_to_database(friend_from_login=user_json['login'], friend_to_login=friend_to_json['login'],
                                   addedAt=datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'))
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={"status": "ok"}
            )
        else:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"reason": "Пользователя с данным логином не существует!"}
            )


@app.post('/api/friends/remove')
def removing_friend(remove_friend: RemoveFriend, authorization: Annotated[str | None, Header()]):
    user_json = token_data_validation(authorization=authorization)
    if isinstance(user_json, JSONResponse):
        return user_json
    friends = get_friends_from_database(friend_from_login=user_json['login'])
    if remove_friend.login in friends:
        remove_friend_from_database(friend_from_login=user_json['login'], friend_to_login=remove_friend.login)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={'status': 'ok'}
    )


@app.get('/api/friends')
def send_friends(authorization: Annotated[str | None, Header()], offset: int = 0, limit: int = 5):
    user_json = token_data_validation(authorization=authorization)
    if isinstance(user_json, JSONResponse):
        return user_json
    if limit > 50 or limit < 0 or offset < 0:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                'reason': 'Некорректный offset или limit!'
            }
        )
    friends = get_friends_from_database(friend_from_login=user_json['login'], offset=offset, limit=limit)
    result = []
    for friend in friends:
        result.append({'login': friend[0], 'addedAt': friend[1]})
    result.sort(reverse=True, key=lambda x: x['addedAt'])
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=result
    )


@app.post('/api/posts/new')
def create_post(new_post: NewPost, authorization: Annotated[str | None, Header()]):
    user_json = token_data_validation(authorization=authorization)
    if isinstance(user_json, JSONResponse):
        return user_json
    if len(new_post.content) > 1000:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={'reason': 'Количество символов контента превышает 1000!'}
        )
    for tag in new_post.tags:
        if len(tag) > 20:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={'reason': 'Количество символов тега превышает 20!'}
            )
    post_id = uuid.uuid4()
    post_createdAt = datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
    insert_new_post(post_id=str(post_id), content=new_post.content, tags=new_post.tags, createdAt=post_createdAt,
                    author=user_json['login'])
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
                "id": str(post_id),
                "content": new_post.content,
                "author": user_json['login'],
                "tags": new_post.tags,
                "createdAt": post_createdAt,
                "likesCount": 0,
                "dislikesCount": 0
                }
        )


@app.get('/api/posts/{postId}')
def send_post_by_id(postId: str, authorization: Annotated[str | None, Header()]):
    user_json = token_data_validation(authorization=authorization)
    if isinstance(user_json, JSONResponse):
        return user_json
    post = get_post_from_db(post_id=postId)
    if post:
        author_profile = get_user_profile_from_db(login=post['author'])
        if post['author'] == user_json['login'] or author_profile['isPublic'] == 'true' or \
                user_json['login'] in get_friends_from_database(friend_from_login=post['author']):
            return JSONResponse(status_code=status.HTTP_200_OK,
                                content=post)
        else:
            return JSONResponse(status_code=status.HTTP_404_NOT_FOUND,
                                content={'reason': 'Этот пост вам не доступен!'})
    else:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND,
                            content={'reason': 'Данного поста не существует!'})


@app.get('/api/posts/feed/my')
def get_my_feed(authorization: Annotated[str | None, Header()], limit: int = 5, offset: int = 0):
    user_json = token_data_validation(authorization=authorization)
    if isinstance(user_json, JSONResponse):
        return user_json
    if limit > 50 or limit < 0 or offset < 0:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                'reason': 'Некорректный offset или limit!'
            }
        )
    feed = get_feed_by_author(author=user_json['login'], limit=limit, offset=offset)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=feed
    )


@app.get('/api/posts/feed/{login}')
def get_other_feed(login: str, authorization: Annotated[str | None, Header()], limit: int = 5, offset: int = 0):
    user_json = token_data_validation(authorization=authorization)
    if isinstance(user_json, JSONResponse):
        return user_json
    profile = get_user_profile_from_db(login=login)
    if profile is None:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND,
                            content={'reason': 'Юзера с данным логином не существует!'})
    if limit > 50 or limit < 0 or offset < 0:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                'reason': 'Некорректный offset или limit!'
            }
        )
    feed = get_feed_by_author(author=login, limit=limit, offset=offset)
    if login == user_json['login']:
        return feed
    if user_json['login'] in get_friends_from_database(friend_from_login=login):
        return feed
    elif profile['isPublic'] == 'true':
        return feed
    else:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={'reason': 'У вас нет доступа к данной публикации!'}
        )


@app.post('/api/posts/{postId}/like')
def like_post(postId: str, authorization: Annotated[str | None, Header()]):
    user_json = token_data_validation(authorization=authorization)
    if isinstance(user_json, JSONResponse):
        return user_json
    reaction = get_reaction(post_id=postId, login=user_json['login'])
    post = get_post_from_db(post_id=postId)
    if post is None:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={'reason': 'Поста с данным айди не существует!'}
        )
    if ((user_json['login'] == post['author']) or
            (user_json['login'] in get_friends_from_database(friend_from_login=post['author'])
             or get_user_from_db(login=post['author'])['isPublic'] is True)):
        if reaction == 'like':
            return post
        if reaction == 'dislike':
            post['dislikesCount'] -= 1
            post['likesCount'] += 1
            update_reaction(reaction='like', login=user_json['login'], post_id=postId)
            update_posts_counts(post_id=postId, likesCount=post['likesCount'], dislikesCount=post['dislikesCount'])
            return post
        if reaction is None:
            post['likesCount'] += 1
            insert_reaction(reaction='like', login=user_json['login'], post_id=postId)
            update_posts_counts(post_id=postId, likesCount=post['likesCount'], dislikesCount=post['dislikesCount'])
            return post
    else:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={'reason': 'Доступ к данному посту ограничен!'}
        )


@app.post('/api/posts/{postId}/dislike')
def like_post(postId: str, authorization: Annotated[str | None, Header()]):
    user_json = token_data_validation(authorization=authorization)
    if isinstance(user_json, JSONResponse):
        return user_json
    reaction = get_reaction(post_id=postId, login=user_json['login'])
    post = get_post_from_db(post_id=postId)
    if post is None:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={'reason': 'Поста с данным айди не существует!'}
        )
    if ((user_json['login'] == post['author']) or
            (user_json['login'] in get_friends_from_database(friend_from_login=post['author'])
             or get_user_from_db(login=post['author'])['isPublic'] is True)):
        if reaction == 'dislike':
            return post
        if reaction == 'like':
            post['dislikesCount'] += 1
            post['likesCount'] -= 1
            update_reaction(reaction='dislike', login=user_json['login'], post_id=postId)
            update_posts_counts(post_id=postId, likesCount=post['likesCount'], dislikesCount=post['dislikesCount'])
            return post
        if reaction is None:
            post['dislikesCount'] += 1
            insert_reaction(reaction='dislike', login=user_json['login'], post_id=postId)
            update_posts_counts(post_id=postId, likesCount=post['likesCount'], dislikesCount=post['dislikesCount'])
            return post
    else:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={'reason': 'Доступ к данному посту ограничен!'}
        )


@app.exception_handler(RequestValidationError)
async def validation_error():
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            'reason': 'Вы отправили некорректную форму'
        }
    )
