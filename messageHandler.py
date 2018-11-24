import vkapi
import os
import importlib
from command_system import command_list
import requests
import ffmpeg

def load_modules():
   files = os.listdir("mysite/commands")
   modules = filter(lambda x: x.endswith('.py'), files)
   for m in modules:
       importlib.import_module("commands." + m[0:-3])

def speech_to_text(filepath):
    import io
    import os

    print(os.getcwd())

    #process = os.popen('gcc -E /home/AlexNerru/mysite/DriveAPI-f33ebdfffc9e.json')
    #preprocessed = process.read()
    #process.close()

    from google.cloud import speech
    from google.cloud.speech import enums
    from google.cloud.speech import types

    print("in stt")

    client = speech.SpeechClient()
    with io.open(filepath, 'rb') as audio_file:
        content = audio_file.read()
        audio = types.RecognitionAudio(content=content)

    config = types.RecognitionConfig(
        encoding=enums.RecognitionConfig.AudioEncoding.FLAC,
        sample_rate_hertz=48000,
        language_code='ru-RU')

    print("before recognize")
    # Detects speech in the audio file
    try:
        response = client.recognize(config, audio)
    except:
        print("was erroe")

    for result in response.results:
        print('Transcript: {}'.format(result.alternatives[0].transcript))
    print("after recognize")

def translate(doc):
    save_doc(doc)
    print("times in translate")
    stream = ffmpeg.input(get_file_path(doc))
    stream = ffmpeg.output(stream, get_file_path(doc, ".flac"))
    ffmpeg.run(stream)
    speech_to_text(get_file_path(doc, ".flac"))
    print("after ffmpeg")

def get_file_path(doc, ext = ".ogg"):
    file_path_small = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                   'files')
    filename = str(doc['doc']['owner_id']) + "." + str(doc['doc']['id']) + ext
    file_path = os.path.join(file_path_small, str(filename))
    return file_path


def get_answer(data):
    message = "Sorry, I can't understand you. Please write 'help' to get info"
    attachment = ''

    if ('attachments' in data):
        if (data['attachments'][0]['type'] == "doc"):
            if (data['attachments'][0]['doc']['ext'] == "ogg"):
                translate(data['attachments'][0])
    #else:
    #    for c in command_list:
    #        if data['body'] in c.keys:
    #            message, attachment = c.process()
    return message, attachment

def save_doc(doc):
    file_path = get_file_path(doc)
    doc = requests.get(doc['doc']['url'])
    with open(file_path, "wb") as f:
        f.write(doc.content)


def parse_mess_and_save(data):
    if ('fwd_messages' in data):
        messages = data['fwd_messages']
        for message in messages:
            if ('fwd_messages' in message):
                inner_messages =  message['fwd_messages']
                for inner_message in inner_messages:
                    if ('attachments' in inner_message):
                        print(inner_message)
                        if (inner_message['attachments'][0]['type'] == "doc"):
                            doc = inner_message['attachments'][0]
                            save_doc(doc)
            else:
                if ('attachments' in message):
                    print(message)
                    if (message['attachments'][0]['type'] == "doc"):
                        doc = message['attachments'][0]
                        save_doc(doc)
    else:
        if ('attachments' in data):
            if (data['attachments'][0]['type'] == "doc"):
                doc = data['attachments'][0]
                save_doc(doc)


def create_answer(data, token):
    load_modules()
    #parse_mess_and_save(data)

    user_id = data['user_id']
    message, attachment = get_answer(data)
    vkapi.send_message(user_id, token, message, attachment)
