import psycopg2
from .config import load_configs

conn_settings = load_configs()
# conn = psycopg2.connect(host=conn_settings['host'], dbname=conn_settings['data'],
#                         user=conn_settings['username'], password=conn_settings['password'], port=conn_settings['port'])
conn = psycopg2.connect(host='localhost', dbname='postgres', user='postgres', password='1234', port=5432)


def get_countries(region):
    cur = conn.cursor()
    if region:
        cur.execute(f"""SELECT name, alpha2, alpha3, region FROM countries
                    WHERE region='{region}';""")
    else:
        cur.execute(f"""SELECT name, alpha2, alpha3, region FROM countries;""")
    s = cur.fetchall()
    res = []
    for country in s:
        res.append({
            'name': country[0],
            'alpha2': country[1],
            'alpha3': country[2],
            'region': country[3]
        })
    conn.commit()
    cur.close()
    return res


def get_country(alpha2):
    cur = conn.cursor()
    cur.execute(f"""SELECT name, alpha2, alpha3, region FROM countries
                    WHERE alpha2='{alpha2}';""")
    country = cur.fetchone()
    conn.commit()
    cur.close()
    res = {
        'name': country[0],
        'alpha2': country[1],
        'alpha3': country[2],
        'region': country[3]
    }
    return res


def create_users_database():
    cur = conn.cursor()
    cur.execute(f"""CREATE TABLE IF NOT EXISTS UsersDatabase
                    (login TEXT PRIMARY KEY,
                    email TEXT UNIQUE,
                    hashed_password TEXT,
                    countryCode TEXT,
                    isPublic BOOL,
                    phone TEXT UNIQUE,
                    image TEXT);""")
    conn.commit()
    cur.close()


def check_user(login, email, phone):
    cur = conn.cursor()
    cur.execute(f"""SELECT login, email, phone FROM UsersDatabase""")
    users = cur.fetchall()
    logins, emails, phones = [], [], []
    for user in users:
        logins.append(user[0])
        emails.append(user[1])
        phones.append(user[2])
    print(logins, emails, phones)
    conn.commit()
    cur.close()
    return login in logins or email in emails or (phone in phones if phone else False)


def check_country_code(countryCode):
    cur = conn.cursor()
    cur.execute(f"""SELECT alpha2 FROM countries WHERE alpha2='{countryCode}'""")
    s = cur.fetchone()
    return True if s else False


def register_user(login, email, hashed_password, countryCode, isPublic, phone, image):
    cur = conn.cursor()
    cur.execute(f"""INSERT INTO UsersDatabase (login, email, hashed_password, countryCode, isPublic, phone, image)"""
                f"""VALUES ('{login}', '{email}', '{hashed_password}', '{countryCode}', '{isPublic}', '{phone}', '{image}');""")
    conn.commit()
    cur.close()


def get_user_from_db(login: str):
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM UsersDatabase WHERE login='{login}'")
    s = cur.fetchone()
    if s:
        result = {
            'login': s[0],
            'email': s[1],
            'hashed_password': s[2],
            'countryCode': s[3],
            'isPublic': s[4],
            'phone': s[5],
            'image': s[6]
        }
        return result
    return None


def get_user_profile_from_db(login: str):
    cur = conn.cursor()
    cur.execute(f"SELECT login, email, countryCode, isPublic, phone, image FROM UsersDatabase WHERE login='{login}'")
    s = cur.fetchone()
    if s:
        result = {
            'login': s[0],
            'email': s[1],
            'countryCode': s[2],
            'isPublic': s[3]
        }
        if s[4]:
            result['phone'] = s[4]
        if s[5]:
            result['image'] = s[5]
        return result
    return None


def update_user_profile(login, **kwargs):
    cur = conn.cursor()
    for i in kwargs.keys():
        cur.execute(f"""UPDATE UsersDatabase SET {i}='{kwargs[i]}' WHERE login='{login}'""")
    conn.commit()
    cur.close()


def check_user_for_update(login, phone):
    cur = conn.cursor()
    cur.execute(f"""SELECT phone FROM UsersDatabase WHERE NOT(login='{login}')""")
    users = cur.fetchall()
    phones = []
    for user in users:
        phones.append(user[0])
    conn.commit()
    cur.close()
    return phone in phones if phone else False


def get_user_hashed_password(login: str):
    cur = conn.cursor()
    cur.execute(f"""SELECT hashed_password FROM UsersDatabase WHERE login='{login}'""")
    s = cur.fetchone()
    conn.commit()
    cur.close()
    return s[0]


def create_friends_database():
    cur = conn.cursor()
    cur.execute(f"""CREATE TABLE IF NOT EXISTS FriendsDatabase
                    (friend_from_login TEXT,
                    friend_to_login TEXT,
                    addedAt TEXT);""")
    conn.commit()
    cur.close()


def get_friends_from_database(friend_from_login, offset=0, limit=0):
    cur = conn.cursor()
    if offset > 0 and limit > 0:
        cur.execute(f"""SELECT friend_to_login, addedAt FROM FriendsDatabase WHERE friend_from_login='{friend_from_login}' 
                ORDER BY friend_to_login OFFSET {offset} LIMIT {limit};""")
    elif offset > 0:
        cur.execute(f"""SELECT friend_to_login, addedAt FROM FriendsDatabase WHERE friend_from_login='{friend_from_login}' 
                ORDER BY friend_to_login OFFSET {offset};""")
    elif limit > 0:
        cur.execute(f"""SELECT friend_to_login, addedAt FROM FriendsDatabase WHERE friend_from_login='{friend_from_login}' 
                        ORDER BY friend_to_login LIMIT {limit};""")
    else:
        cur.execute(f"""SELECT friend_to_login FROM FriendsDatabase WHERE friend_from_login='{friend_from_login}';""")
    s = cur.fetchall()
    if offset == 0 and limit == 0:
        s = [i[0] for i in s]
    conn.commit()
    cur.close()
    return s


def add_friend_to_database(friend_from_login, friend_to_login, addedAt):
    cur = conn.cursor()
    cur.execute(f"""INSERT INTO FriendsDatabase (friend_from_login, friend_to_login, addedAt) VALUES 
    ('{friend_from_login}', '{friend_to_login}', '{addedAt}');""")
    conn.commit()
    cur.close()


def remove_friend_from_database(friend_from_login, friend_to_login):
    cur = conn.cursor()
    cur.execute(f"""DELETE FROM FriendsDatabase WHERE friend_from_login='{friend_from_login}' AND friend_to_login='{friend_to_login}');""")
    conn.commit()
    cur.close()


def create_posts_database():
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS PostsDatabase ("
                "post_id TEXT PRIMARY KEY,"
                "content TEXT,"
                "author TEXT,"
                "tags TEXT,"
                "createdAT TEXT,"
                "likesCount INT,"
                "dislikesCount INT);")
    conn.commit()
    cur.close()


def insert_new_post(post_id: str, content: str, author: str,
                    tags: list, createdAt: str):
    cur = conn.cursor()
    cur.execute(f"""INSERT INTO PostsDatabase (post_id, content, author, tags, createdAt, likesCount, dislikesCount) 
    VALUES ('{post_id}', '{content}', '{author}', '[{', '.join(f'"{tag}"' for tag in tags)}]', '{createdAt}', 0, 0)""")
    conn.commit()
    cur.close()


def get_post_from_db(post_id: str):
    cur = conn.cursor()
    cur.execute(f"""SELECT content, author, tags, createdAt, likesCount, dislikesCount
     FROM PostsDatabase WHERE post_id='{post_id}'""")
    s = cur.fetchone()
    conn.commit()
    cur.close()
    if s:
        res = {
            "post_id": post_id,
            "content": s[0],
            "author": s[1],
            "tags": eval(s[2]),
            "createdAt": s[3],
            "likesCount": s[4],
            "dislikesCount": s[5]
            }
        return res
    return None


def get_feed_by_author(author: str, offset=0, limit=0):
    cur = conn.cursor()
    if limit <= 0:
        cur.execute(f"""SELECT post_id, content, author, tags, createdAt, likesCount, dislikesCount
         FROM PostsDatabase WHERE author='{author}' ORDER BY post_id OFFSET {offset}""")
    else:
        cur.execute(f"""SELECT post_id, content, author, tags, createdAt, likesCount, dislikesCount
                 FROM PostsDatabase WHERE author='{author}' ORDER BY post_id LIMIT {limit} OFFSET {offset}""")
    s = cur.fetchall()
    conn.commit()
    cur.close()
    if s:
        res = []
        for i in s:
            res.append({
                "post_id": i[0],
                "content": i[1],
                "author": i[2],
                "tags": eval(i[3]),
                "createdAt": i[4],
                "likesCount": i[5],
                "dislikesCount": i[6]
                })
        return sorted(res, key=lambda x: x['createdAt'], reverse=True)
    return []


def create_posts_reaction_database():
    cur = conn.cursor()
    cur.execute('CREATE TABLE IF NOT EXISTS PostsReactionDatabase'
                '(post_id TEXT,'
                'login TEXT,'
                'reaction TEXT);')
    conn.commit()
    cur.close()


def get_reaction(post_id, login):
    cur = conn.cursor()
    cur.execute(f"""SELECT reaction FROM PostsReactionDatabase WHERE post_id='{post_id}' AND login='{login}';""")
    s = cur.fetchone()
    conn.commit()
    cur.close()
    if s:
        return s[0]
    return None


def update_reaction(reaction, login, post_id):
    cur = conn.cursor()
    cur.execute(f"""UPDATE PostsReactionDatabase SET reaction='{reaction}' 
                    WHERE post_id='{post_id}' AND login='{login}';""")
    conn.commit()
    cur.close()


def insert_reaction(reaction, login, post_id):
    cur = conn.cursor()
    cur.execute(f"""INSERT INTO PostsReactionDatabase (reaction, login, post_id) 
                    VALUES ('{reaction}', '{login}', '{post_id}');""")
    conn.commit()
    cur.close()
    

def update_posts_counts(post_id, likesCount, dislikesCount):
    cur = conn.cursor()
    cur.execute(f"""UPDATE PostsDatabase SET likesCount='{likesCount}', dislikesCount='{dislikesCount}'
                    WHERE post_id='{post_id}'""")
    conn.commit()
    cur.close()


create_users_database()
create_friends_database()
create_posts_database()
create_posts_reaction_database()
