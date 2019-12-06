from mycroft import MycroftSkill, intent_file_handler


class Daphne(MycroftSkill):
    def __init__(self):
        MycroftSkill.__init__(self)

    @intent_file_handler('daphne.intent')
    def handle_daphne(self, message):
        self.speak_dialog('daphne')


def create_skill():
    return Daphne()

