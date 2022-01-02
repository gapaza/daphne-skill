from threading import Thread
from queue import Queue
import websocket
import time
import json


def open_connection(connection):
    connection.run_forever()


def on_error(ws, error):
    print('--> ON ERROR:', error)


def on_close(ws, close_status_code, close_msg):
    print('--> ON CLOSE', close_status_code, close_msg)


def on_open(ws):
    print('--> ON OPEN')
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


def on_message(ws, message):
    print('--> ON MESSAGE')
    json_message = json.loads(message)
    if 'type' not in json_message:  # Ping messages
        return
    if json_message['type'] == 'mycroft.test':  # Test messages
        print(json_message['content'])
        # self.handle_test_message(json_message['content'])
    if json_message['type'] == 'mycroft.forward':  # Forwarded messages
        print(json_message['content'])
        # self.handle_test_message(json_message['content'])


def test():
    websocket.enableTrace(True)
    print("TESTING WEBSOCKET")

    ws_url = 'ws://localhost:8000/api/mycroft'
    session_key = '9836'

    connection = websocket.WebSocketApp(ws_url, header={'mycroft-session': str(session_key)})
    connection.on_message = lambda ws, message: on_message(ws, message)
    connection.on_error = lambda ws, error: on_error(ws, error)
    connection.on_close = lambda ws, status, msg: on_close(ws, status, msg)
    connection.on_open = lambda ws: on_open(ws)

    print('--> CONNECTION OBJ ESTABLISHED')


    ws_thread = Thread(target=open_connection, args=(connection,))
    ws_thread.start()

    print('--> WEBSOCKET STARTED')

    # for x in range(5):
    #     time.sleep(1)
    #     print('--> SLEEP:', x)


    time.sleep(3)
    print('--> TESTING CONNECTION')
    true_phrase = "connection successful"
    false_phrase = "connection error"
    test_message = json.dumps({'msg_type': 'mycroft_test', 'phrase': true_phrase})
    connection.send(test_message)
    time.sleep(10)



if __name__ == "__main__":
    test()


