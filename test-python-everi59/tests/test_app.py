from fastapi.testclient import TestClient
from ..solution.app import app

client = TestClient(app)


def test_profiles():
    reg_data = {
              "login": "pisunchik",
              "email": "pidoras1488@niga.ru",
              "password": "Qwerty1337)",
              "countryCode": "RU",
              "isPublic": True,
              "phone": "+7000000000",
              "image": "https://http.cat/images/100.jpg"
    }
    response = client.post('/api/auth/register', json=reg_data)

    assert response.status_code == 201
    assert response.json()['profile'] == {
              "login": "pisunchik",
              "email": "pidoras1488@niga.ru",
              "countryCode": "RU",
              "isPublic": True,
              "phone": "+7000000000",
              "image": "https://http.cat/images/100.jpg"
    }

    auth_data = {
        "login": "pisunchik",
        "password": "Qwerty1337)"
    }
    response = client.post('/api/auth/sign-in', json=auth_data)

    assert response.status_code == 200
    assert 'token' in response.json()

    bearer = response.json()['token']
    headers = {
        "Authorization": f"Bearer {bearer}"
    }
    response = client.get('/api/me/profile', headers=headers)

    assert response.status_code == 200
    assert response.json() == {
              "login": "pisunchik",
              "email": "pidoras1488@niga.ru",
              "countryCode": "RU",
              "isPublic": True,
              "phone": "+7000000000",
              "image": "https://http.cat/images/100.jpg"
    }

    reg_data = {
        "login": "pisunchik2",
        "email": "pidoras1488@niga.ru2",
        "password": "Qwerty1337)",
        "countryCode": "RU",
        "isPublic": True,
        "phone": "+700000002",
        "image": "https://http.cat/images/100.jpg"
    }
    response = client.post('/api/auth/register', json=reg_data)

    assert response.status_code == 201
    assert response.json()['profile'] == {
        "login": "pisunchik2",
        "email": "pidoras1488@niga.ru2",
        "countryCode": "RU",
        "isPublic": True,
        "phone": "+700000002",
        "image": "https://http.cat/images/100.jpg"
    }

    auth_data = {
        "login": "pisunchik2",
        "password": "Qwerty1337)"
    }
    response = client.post('/api/auth/sign-in', json=auth_data)

    assert response.status_code == 200
    assert 'token' in response.json()

    bearer2 = response.json()['token']
    headers2 = {
        "Authorization": f"Bearer {bearer2}"
    }
    response = client.get('/api/me/profile', headers=headers2)

    assert response.status_code == 200
    assert response.json() == {
        "login": "pisunchik2",
        "email": "pidoras1488@niga.ru2",
        "countryCode": "RU",
        "isPublic": True,
        "phone": "+700000002",
        "image": "https://http.cat/images/100.jpg"
    }
    patch_data = {
                  "countryCode": "RU",
                  "isPublic": True,
                  "phone": "+7000002000",
                  "image": "https://http.cat/images/101.jpg"
                }
    response = client.patch('/api/me/profile', json=patch_data, headers=headers2)

    assert response.status_code == 200
    assert response.json() == {
        "login": "pisunchik2",
        "email": "pidoras1488@niga.ru2",
        "countryCode": "RU",
        "isPublic": True,
        "phone": "+7000002000",
        "image": "https://http.cat/images/101.jpg"
    }

    response = client.get('/api/profiles/pisunchik2', headers=headers)

    assert response.status_code == 200
    assert response.json() == {
        "login": "pisunchik2",
        "email": "pidoras1488@niga.ru2",
        "countryCode": "RU",
        "isPublic": True,
        "phone": "+7000002000",
        "image": "https://http.cat/images/101.jpg"
    }

def test_profile_friends():
    auth_data = {
        "login": "pisunchik",
        "password": "Qwerty1337)"
    }
    response = client.post('/api/auth/sign-in', json=auth_data)
    bearer = response.json()['token']
    headers = {
        "Authorization": f"Bearer {bearer}"
    }

    fake_login = {'login': 'xyizxc'}
    response = client.post('/api/friends/add', headers=headers, json=fake_login)
    assert response.status_code == 404
    assert response.json() == {
        'reason': 'Пользователь с указанным логином не найден.'
    }

    response = client.post('/api/friends/add', json=auth_data)
    assert response.status_code == 401
    assert response.json() == {
        'reason': 'Переданный токен не существует либо некорректен'
    }

    add_friend_login = {
        "login": "pisunchik2"
    }
    response = client.post('/api/friends/add', json=add_friend_login, headers=headers)
    assert response.status_code == 200
    assert response.json() == {
        'status': 'ok'
    }

    add_friend_login = {
        "login": "pisunchik"
    }
    response = client.post('/api/friends/add', json=add_friend_login, headers=headers)
    assert response.status_code == 200
    assert response.json() == {
        'status': 'ok'
    }

    response = client.get('/api/friends', headers=headers)
    assert response.status_code == 200
    assert response.json() == [
        {
            "login": "pisunchik2",
            "addedAt": "2024-03-04T15:18:33Z"
        }
    ]
    response = client.get('/api/friends')
    assert response.status_code == 401
    assert response.json() == {
        'reason': 'Переданный токен не существует либо некорректен'
    }

    fake_user = {
        "login": "fake_pisun"
    }
    response = client.post('/api/friends/remove', json=fake_user, headers=headers)
    assert response.status_code == 404

    invalid_form = {
        "zxcgg": "dota2",
        "login": "pisunchik",
        "huinya": "dolboeb?"
    }
    response = client.post('/api/friends/remove', json=invalid_form, headers=headers)
    assert response.status_code == 200

    invalid_token = {
        "token": "invalid"
    }
    response = client.post('/api/friends/remove', json=fake_user, headers=invalid_token)
    assert response.status_code == 401

    user = {
        "login": "pisunchik",
    }
    response = client.post('/api/friends/remove', json=user, headers=headers)
    assert response.status_code == 200

    user = {
        "login": "pisunchik2",
    }
    response = client.post('/api/friends/remove', json=user, headers=headers)
    assert response.status_code == 200
