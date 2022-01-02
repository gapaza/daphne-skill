from mycroft import FallbackSkill, intent_file_handler
from threading import Thread
from queue import Queue
import websocket
import time
import json


class Daphne(FallbackSkill):
    def __init__(self):
        super(Daphne, self).__init__(name='Daphne')

        # Connection Variables
        self.ws_url = 'wss://dev.selva-research.com/api/mycroft'
        # self.ws_url = 'ws://localhost:8000/api/mycroft'
        self.ws_thread = None
        self.connection = None
        self.connection_queue = Queue()

        # Session Variables
        self.session_key = None
        self.session_key_phrase = None
        self.session_key_tutorial = True
        self.session_key_set_tries = 3



    # -------------------------------
    # --- Websocket App Functions ---
    # -------------------------------
    def open_connection(self, messaging_queue, connection):
        connection.run_forever()

    def on_error(self, ws, error):
        print(error)

    def on_close(self, ws, close_status_code, close_msg):
        print(close_status_code, close_msg)

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

    def on_message(self, ws, message):
        json_message = json.loads(message)
        if 'type' not in json_message:                 # Ping messages
            return
        if json_message['type'] == 'mycroft.test':     # Test messages
            self.handle_test_message(json_message['content'])
        if json_message['type'] == 'mycroft.forward':  # Forwarded messages
            self.handle_test_message(json_message['content'])

    def handle_test_message(self, message_content):
        self.speak(str(message_content))

    def send_command(self, msg_type, command):
        # msg_type: mycroft_message --> message to front-end
        # msg_type: mycroft_test    --> test message
        if self.connection is not None and self.ws_thread is not None:
            message = json.dumps({'msg_type': msg_type, 'command': command})
            self.connection.send(message)
        else:
            self.speak("communication error with daphne server")

    def establish_connection(self):
        if self.connection is None and self.ws_thread is None:
            self.connection = websocket.WebSocketApp(self.ws_url,
                                                     on_message=lambda ws, message: self.on_message(ws, message),
                                                     on_error=lambda ws, error: self.on_error(ws, error),
                                                     on_close=lambda ws, status, msg: self.on_close(ws, status, msg),
                                                     header={'mycroft-session': str(self.session_key)})
            self.connection.on_open = lambda ws: self.on_open(ws)
            self.ws_thread = Thread(target=self.open_connection, args=(self.connection_queue, self.connection))
            self.ws_thread.start()
            self.test_connection(success_phrase="connection established", fail_phrase="failed to connect")

    def test_connection(self, success_phrase=None, fail_phrase=None):
        true_phrase = "connection successful"
        false_phrase = "connection error"
        if success_phrase is not None:
            true_phrase = str(success_phrase)
        if fail_phrase is not None:
            false_phrase = str(fail_phrase)
        time.sleep(3)
        if self.connection is not None and self.ws_thread is not None:
            test_message = json.dumps({'msg_type': 'mycroft_test', 'phrase': true_phrase})
            self.connection.send(test_message)
        else:
            self.speak(false_phrase)

    def terminate_connection(self, terminate_phrase=None):
        phrase = 'connection closed'
        if terminate_phrase is not None:
            phrase = terminate_phrase
        if self.connection is not None and self.ws_thread is not None:
            self.connection.close()
            self.ws_thread.join()
            self.connection = None
            self.ws_thread = None
            if terminate_phrase is not None:
                self.speak(str(phrase))

    def get_session_key_strong(self):
        return 0

    def get_session_key(self):
        session_key = self.get_response("PleaseReadYourFourDigitKey",
                                        data=None,
                                        validator=lambda utterance: self.validate_key(utterance),
                                        on_fail=lambda utterance: self.invalid_key(utterance),
                                        num_retries=3)
        self.session_key_set_tries = 3
        if session_key:
            key_digits = [int(i) for i in session_key if i.isdigit()]
            key_string = ''
            for digit in key_digits:
                key_string = key_string + str(digit)
            self.session_key = int(key_string)
            self.session_key_phrase = str(key_string)
            phrase = 'session key set to ' + self.session_key_phrase
            self.speak(phrase)
            return True
        else:
            self.speak("key set unsuccessful")
            return False

    def validate_key(self, utterance):
        key_digits = [int(i) for i in utterance if i.isdigit()]
        if len(key_digits) != 4:
            return False
        else:
            return True

    def invalid_key(self, utterance):
        self.session_key_set_tries = self.session_key_set_tries - 1
        if self.session_key_set_tries == 0:
            return "invalid key"
        elif self.session_key_set_tries == 1:
            return "invalid key. try again"
        else:
            return "the key must be four digits long. please read your key"




    # --------------------------
    # --- Connection Intents ---
    # --------------------------
    @intent_file_handler('set.session.key.intent')     # set daphne session
    def set_daphne_session_key(self, message):
        self.get_session_key()

    @intent_file_handler('connect.intent')             # connect to daphne
    def connect_to_daphne(self, message):
        if self.connection is None and self.session_key is not None:
            self.speak('connecting to daphne with session key ' + self.session_key_phrase)
            self.establish_connection()
        elif self.connection is None and self.session_key is None:
            self.speak("You must set a session key before connecting to daphne")
            if self.session_key_tutorial:
                if self.ask_yesno("WouldYouLikeToSetASessionKey") == "yes":
                    if self.get_session_key():
                        self.establish_connection()
                    else:
                        self.speak("connection aborted")
                else:
                    self.speak("connection aborted")
        elif self.connection is not None and self.session_key is not None:
            self.speak("you are already connected to daphne with session key " + self.session_key_phrase)
            if self.ask_yesno("WouldYouLikeToConnectToANewSession") == "yes":
                if self.get_session_key():
                    self.terminate_connection('disconnected from current session')
                    self.establish_connection()
                else:
                    self.speak("connection aborted")
            else:
                self.speak("keeping current connection")

    @intent_file_handler('test.connection.intent')     # "test daphne connection"
    def test_daphne_connection(self, message):
        self.test_connection(success_phrase="connection valid", fail_phrase="you are not connected to daphne")

    @intent_file_handler('disconnect.intent')          # disconnect daphne
    def disconnect_from_daphne(self, message):
        if self.connection is None:
            self.speak('you are not currently connected to daphne')
        else:
            self.terminate_connection('connection closed')

    @intent_file_handler('refresh.connection.intent')  # refresh daphne connection
    def refresh_daphne_connection(self, message):
        if self.connection is not None and self.session_key is not None:
            self.terminate_connection('refreshing connection')
            self.establish_connection()
            self.speak('connection refreshed')
        else:
            self.speak('no connection currently exists')



    # ---------------------------------
    # --- Daphne Command Processing ---
    # ---------------------------------
    def initialize(self):
        self.register_fallback(self.handle_fallback_command, 80)

    def shutdown(self):
        self.remove_fallback(self.handle_fallback_command)
        super(Daphne, self).shutdown()

    def handle_fallback_command(self, message):
        if self.ws_thread is not None and self.connection is not None:
            command = message.data['utterance']
            self.send_command('mycroft_message', command)
            return True
        return False



def create_skill():
    return Daphne()
