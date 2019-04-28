import os
import requests
import random
from dotenv import load_dotenv


def get_file_extension(file_url):
    return file_url.split('.')[-1]


def download_and_save_image(url, filename):
    response = requests.get(url)
    response.raise_for_status()

    with open(filename, 'wb') as f:
        f.write(response.content)


def get_random_comic_from_xkcd():
    postfix = 'info.0.json'

    base_url = 'https://xkcd.com/{}'
    number_last_comic = requests.get(base_url.format(postfix)).json()['num']
    number_comic = random.randint(1, number_last_comic)

    url = 'https://xkcd.com/{}/{}'.format(number_comic, postfix)
    response = requests.get(url)
    response.raise_for_status()

    url_comic = response.json()['img']
    author_comment = response.json()['alt']
    filename = '{}.{}'.format(response.json()['title'], get_file_extension(url_comic))
    download_and_save_image(url_comic, filename)

    return filename, author_comment


def get_upload_server(api_url, params):
    method = 'photos.getWallUploadServer'
    response = requests.get(api_url.format(method), params=params)
    return response.json()['response']['upload_url']


def upload_comic_to_server(upload_url, comic):
    with open(comic, 'rb') as comic:
        files = {
            'photo': comic,
        }
        response = requests.post(upload_url, files=files)

    return response.json()['server'], response.json()['photo'], response.json()['hash']


def save_comic_in_album(api_url, params, data):
    method = 'photos.saveWallPhoto'
    response = requests.post(api_url.format(method), data=data, params=params)
    return response.json()['response'][0]['owner_id'], response.json()['response'][0]['id']


def publish_comic(api_url, params):
    method = 'wall.post'
    response = requests.get(api_url.format(method), params=params)
    return response.json()


def main():
    load_dotenv()
    group_id = 181677110
    vk_token = os.getenv('vk_token')
    api_url = 'https://api.vk.com/method/{}'
    params = {
        'access_token': vk_token,
        'v': 5.95,
    }

    comic, author_comment = get_random_comic_from_xkcd()
    upload_url = get_upload_server(api_url, params)
    server, photo, hash_comic = upload_comic_to_server(upload_url, comic)
    os.remove(comic)
    data = {
        'server': server,
        'photo': photo,
        'hash': hash_comic
    }
    owner_id_comic, media_id_comic = save_comic_in_album(api_url, params, data)
    params_add = {
        'owner_id': -group_id,
        'from_group': 1,
        'message': author_comment,
        'attachments': 'photo{}_{}'.format(owner_id_comic, media_id_comic)
    }

    params.update(params_add)
    publish_comic(api_url, params)


if __name__ == '__main__':
    main()

