import command_system


def hello():
   message = 'Hi, I am DeepBabel chatbot/n I can help you speek on different languages!'
   return message, ''

hello_command = command_system.Command()

hello_command.keys = ['hi', 'hello']
hello_command.description = 'Greeting'
hello_command.process = hello
