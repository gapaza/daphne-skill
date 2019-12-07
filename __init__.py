from mycroft import MycroftSkill, intent_file_handler
from mycroft.skills.core import intent_handler
from adapt.intent import IntentBuilder

import websocket
from threading import Thread
from queue import Queue
import time
import json


class Daphne(MycroftSkill):
    def __init__(self):
        MycroftSkill.__init__(self)
        print("Initializing Daphne Skill")

        # Connection Variables
        self.ws_url = 'ws://localhost:8000/api/eoss/ws'
        self.ws_thread = None
        self.connection = None
        self.connection_queue = Queue()
        self.session_key = None
        self.session_key_tutorial = True

    # Websocket App Functions
    def on_message(self, ws, message):
        print(message)
        json_message = json.loads(message)
        message_class = None

        # Message Class
        if 'class' in json_message:
            message_class = json_message['class']

        if message_class == 'testing':
            self.speak(str(json_message['message']))

    def on_error(self, ws, error):
        print(error)

    def on_close(self, ws):
        print('connection closed')

    def on_open(self, ws):
        def run(*args):
            print("Ping routine started")
            counter = 0
            while counter < 10000:
                ping = json.dumps({'msg_type': 'ping'})
                ws.send(ping)
                time.sleep(30)
                counter = counter + 1
            time.sleep(1)
            ws.close()

        Thread(target=run).start()

    def open_connection(self, messaging_queue, connection):
        connection.run_forever()


    # Connection Functions
    def establish_connection(self):
        if self.connection is None and self.ws_thread is None:
            self.connection = websocket.WebSocketApp(self.ws_url,
                                                     on_message=lambda ws, message: self.on_message(ws, message),
                                                     on_error=lambda ws, error: self.on_error(ws, error),
                                                     on_close=lambda ws: self.on_close(ws))
            self.connection.on_open = lambda ws: self.on_open(ws)
            self.ws_thread = Thread(target=self.open_connection, args=(self.connection_queue, self.connection))
            self.ws_thread.start()

    def test_connection(self):
        if self.connection is not None and self.ws_thread is not None:
            test_message = json.dumps({'msg_type': 'mycroft', 'class': 'test_connection'})
            self.connection.send(test_message)
        else:
            self.speak("no connection exists")

    def terminate_connection(self):
        if self.connection is not None and self.ws_thread is not None:
            self.connection.close()
            self.ws_thread.join()
            self.connection = None
            self.ws_thread = None

    def get_session_key(self):
        print("Fill")


    # Intents
    @intent_file_handler('set.session.key.intent')  # set daphne key to ###
    def set_daphne_session_key(self, message):
        # please read your six digit key
        session_key = self.get_response("connection.key.request", data=None, validator=None, on_fail=None, num_retries=3)
        if session_key:
            self.speak(str(session_key))
            self.session_key = session_key

    @intent_file_handler('connect.intent')  # connect to daphne
    def connect_to_daphne(self, message):
        if self.connection is None and self.session_key is not None:
            self.establish_connection()
            time.sleep(3)
            self.test_connection()
        elif self.connection is None and self.session_key is None:
            self.speak("You must set a session key before connecting to daphne")
            if self.session_key_tutorial:
                if self.ask_yesno("connection.new.session.query") == "yes":
        else:
            # I am already connected to daphne, would you like to connect to a new session?
            if self.ask_yesno("connection.new.session.query") == "yes":
                self.get_session_key()
                self.terminate_connection()
                self.establish_connection()
                self.speak('new connection successful')

    @intent_file_handler('test.connection.intent')  # "test daphne connection"
    def test_daphne_connection(self, message):
        self.test_connection()

    @intent_file_handler('disconnect.intent')  # disconnect daphne
    def disconnect_from_daphne(self, message):
        if self.connection is None:
            self.speak('no connection exists')
        else:
            self.terminate_connection()
            self.speak('connection terminated')







def create_skill():
    return Daphne()
