import os
import requests
import random
from dotenv import load_dotenv


def print_error_message(response):
    if response.get('error'):
        error_message = '{}. Code: {}\nRequest params:{}'.format(response['error']['error_msg'],
                                                                 response['error']['error_code'],
                                                                 response['error']['request_params'])
        print(error_message)


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
    filename = '{}{}'.format(response.json()['title'], os.path.splitext(url_comic)[1])
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


def post_comic_in_vk(api_url, params):
    method = 'wall.post'
    response = requests.get(api_url.format(method), params=params)
    return response.json()


def download_comic():
    try:
        return get_random_comic_from_xkcd()
    except requests.exceptions.HTTPError as error:
        exit("Can't get data from server xkcd:\n{0}".format(error))


def publish_comic(vk_token, group_id, comic, author_comment):
    api_url = 'https://api.vk.com/method/{}'
    params = {
        'access_token': vk_token,
        'v': 5.95,
    }

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
    post_comic_in_vk(api_url, params)


def get_token_and_group_id():
    return int(os.getenv('group_id')), os.getenv('vk_token')


def main():
    load_dotenv()
    group_id, vk_token = get_token_and_group_id()

    comic, author_comment = download_comic()
    publish_comic(vk_token, group_id, comic, author_comment)


if __name__ == '__main__':
    main()

