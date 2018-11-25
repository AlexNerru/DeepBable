import vkapi
import os
import importlib
from command_system import command_list
import requests
import ffmpeg
import io
import base64

messages = []

def load_modules():
    files = os.listdir("mysite/commands")
    modules = filter(lambda x: x.endswith('.py'), files)
    for m in modules:
        importlib.import_module("commands." + m[0:-3])


def speech_to_text(filepath):
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/home/AlexNerru/mysite/DriveAPI-f33ebdfffc9e.json"

    from google.cloud import speech
    from google.cloud.speech import enums
    from google.cloud.speech import types

    client = speech.SpeechClient()
    with io.open(filepath, 'rb') as audio_file:
        content = audio_file.read()
        audio = types.RecognitionAudio(content=content)

    config = types.RecognitionConfig(
        encoding=enums.RecognitionConfig.AudioEncoding.FLAC,
        sample_rate_hertz=48000,
        language_code='ru-RU')

    response = client.recognize(config, audio)

    phrases = []
    for result in response.results:
        phrases.append(result.alternatives[0].transcript)

    return phrases


def translate(textes):
    from google.cloud import translate

    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/home/AlexNerru/mysite/DriveAPI-f33ebdfffc9e.json"
    translate_client = translate.Client()

    target = 'en'
    translated = []

    for text in textes:
        print(text)
        translation = translate_client.translate(
            text,
            target_language=target)
        translated.append(translation['translatedText'])

    print(translated)
    return translated


def ogg_to_flac(doc):
    stream = ffmpeg.input(get_file_path(doc))
    stream = ffmpeg.output(stream, get_file_path(doc, ".flac"))
    try:
        ffmpeg.run(stream)
    except:
        pass

def mp3_to_ogg(filepath, output):
    stream = ffmpeg.input(filepath)
    stream = ffmpeg.output(stream, output)
    try:
        ffmpeg.run(stream)
    except:
        pass


def get_file_path(doc, ext=".ogg"):
    file_path_small = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                   'files')
    filename = str(doc['doc']['owner_id']) + "." + str(doc['doc']['id']) + ext
    file_path = os.path.join(file_path_small, str(filename))
    return file_path


def test_to_speech(text, userid, docid):
    from google.cloud import texttospeech

    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/home/AlexNerru/mysite/DriveAPI-f33ebdfffc9e.json"

    # Instantiates a client
    client = texttospeech.TextToSpeechClient()
    # Set the text input to be synthesized

    if not os.path.isdir(f"./mysite/{userid}"):
        os.mkdir(f"./mysite/{userid}")

    synthesis_input = texttospeech.types.SynthesisInput(text=text)

    voice = texttospeech.types.VoiceSelectionParams(
        language_code='en-US',
        ssml_gender=texttospeech.enums.SsmlVoiceGender.NEUTRAL)

    audio_config = texttospeech.types.AudioConfig(
        audio_encoding=texttospeech.enums.AudioEncoding.MP3)

    response = client.synthesize_speech(synthesis_input, voice, audio_config)

    with open(f'./mysite/{userid}/{docid}.mp3', 'wb') as out:
        out.write(response.audio_content)
        print(f'Audio content written to file {userid}_{docid}.mp3')

    return


def get_answer(data, token):
    message = "Sorry, I can't understand you. Please write 'help' to get info"
    attachment = ''
    title = ''
    if ('attachments' in data):
        if (data['attachments'][0]['type'] == "doc"):
            if (data['attachments'][0]['doc']['ext'] == "ogg"):
                doc = data['attachments'][0]
                save_doc(doc)
                ogg_to_flac(doc)
                phrases = speech_to_text(get_file_path(doc, ".flac"))
                translations = translate(phrases)
                message = ""
                for trans in translations:
                    message += trans
                test_to_speech(message, data['user_id'], data['id'])
                url = vkapi.upload_voice(data['user_id'], token, "")['upload_url']
                userid = data['user_id']
                docid = data['id']
                mp3_to_ogg(f'./mysite/{userid}/{docid}.mp3', f'./mysite/{userid}/{docid}.ogg')
                response = requests.post(url, files={
                    'file':open(f'./mysite/{userid}/{docid}.ogg', 'rb')}).text
                import json
                file = json.loads(response)['file']
                print(file)
                attachment = vkapi.save(file, token)[0]

                # response = requests.post("http://167.99.253.72:8070/transfer", data = {'link' : attachment['url'],
                #                                                                   'user_id' :
                #     "misha", 'voice_name': "{userid}/{docid}.ogg",  'lang': 'en'})

                print(response)
                title = attachment['title']
                document = 'doc%s_%s' % (str(attachment['owner_id']), str(attachment['id']))
                print(document)
                print(attachment)
                attachment = document

    message = message
    # else:
    #    for c in command_list:
    #        if data['body'] in c.keys:
    #            message, attachment = c.process()
    return message, attachment, title


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
                inner_messages = message['fwd_messages']
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
    user_id = data['user_id']
    message, attachment, title = get_answer(data, token)
    print(message)
    print(attachment)
    if (title not in messages):
        vkapi.send_message(user_id, token, message, attachment)
        messages.append(title)
