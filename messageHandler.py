import vkapi
import os
import importlib
from command_system import command_list
import wget
import requests
import random

def damerau_levenshtein_distance(s1, s2):
   d = {}
   lenstr1 = len(s1)
   lenstr2 = len(s2)
   for i in range(-1, lenstr1 + 1):
       d[(i, -1)] = i + 1
   for j in range(-1, lenstr2 + 1):
       d[(-1, j)] = j + 1
   for i in range(lenstr1):
       for j in range(lenstr2):
           if s1[i] == s2[j]:
               cost = 0
           else:
               cost = 1
           d[(i, j)] = min(
               d[(i - 1, j)] + 1,  # deletion
               d[(i, j - 1)] + 1,  # insertion
               d[(i - 1, j - 1)] + cost,  # substitution
           )
           if i and j and s1[i] == s2[j - 1] and s1[i - 1] == s2[j]:
               d[(i, j)] = min(d[(i, j)], d[i - 2, j - 2] + cost)  # transposition
   return d[lenstr1 - 1, lenstr2 - 1]


def load_modules():
   files = os.listdir("mysite/commands")
   modules = filter(lambda x: x.endswith('.py'), files)
   for m in modules:
       importlib.import_module("commands." + m[0:-3])


def get_answer(body):
   message = "Прости, не понимаю тебя. Напиши 'помощь', чтобы узнать мои команды"
   attachment = ''
   distance = len(body)
   command = None
   key = ''
   for c in command_list:
       for k in c.keys:
           d = damerau_levenshtein_distance(body, k)
           if d < distance:
               distance = d
               command = c
               key = k
               if distance == 0:
                   message, attachment = c.process()
                   return message, attachment
   if distance < len(body)*0.4:
       message, attachment = command.process()
       message = 'Я понял ваш запрос как "%s"\n\n' % key + message
   return message, attachment


def save_doc(doc):
    file_path_small = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                   'files')

    filename = str(doc['doc']['owner_id']) + "." + str(doc['doc']['id']) + ".mp3"
    file_path = os.path.join(file_path_small, str(filename))
    print(file_path)
    doc = requests.get(doc['doc']['url'])
    with open(file_path, "wb") as f:
        f.write(doc.content)

def create_answer(data, token):
    user_id = data['user_id']
    doc = None
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




