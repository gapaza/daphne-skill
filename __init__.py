from mycroft import MycroftSkill, intent_file_handler


class Daphne(MycroftSkill):
    def __init__(self):
        MycroftSkill.__init__(self)
        print("Initializing Daphne Skill")

        # Connection Variables
        self.connection = None
        self.session_key = None


    def establish_connection(self):
        print("Establishing connection")

    @intent_file_handler('connect.intent')
    def handle_daphne(self, message):
        if self.connection is not None:
            if self.ask_yesno("connection.new.session.query") == "yes":
                print("Creating a new connection")
                self.speak_dialog('connection.connecting')
            else:
                print("keeping old connection")

        else:
            print("creating connection")
            self.connection = 'connected'



        self.speak_dialog('daphne')





def create_skill():
    return Daphne()

