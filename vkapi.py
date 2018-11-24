import vk
import random

session = vk.Session()
api = vk.API(session, v=5.0)

def send_message(user_id, token, message, attachment=""):
    api.messages.send(access_token=token, user_id=str(user_id), message=message, attachment=attachment)

def upload_voice(user_id, token, path):
    url = api.docs.getMessagesUploadServer(type='audio_message', access_token = token, peer_id = user_id)
    print(url)
    return url