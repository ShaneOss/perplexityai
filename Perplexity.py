from time import sleep
from uuid import uuid4
from requests import Session
from threading import Thread
from time import time, sleep
from json import loads, dumps
from random import getrandbits
from websocket import WebSocketApp
import websocket
import ssl

class Perplexity:
    """A class to interact with the Perplexity website.
    To get started you need to create an instance of this class.
    For now this class only support one Answer at a time.
    """
    def __init__(self) -> None:
        self.session: Session = self.init_session()

        self.searching = False
        self.t: str = self.get_t()
        self.sid: str = self.get_sid()
        self.frontend_uuid = str(uuid4())
        self.frontend_session_id = str(uuid4())

        assert self.ask_anonymous_user(), "Failed to ask anonymous user"
        self.ws: WebSocketApp = self.init_websocket()
        self.ws_message = ""
        self.n = 1
        self.ws_connected = False
        self.auth_session()
        self.query_str = ""
        self.answer = ""
        self.testcloseconnection = 1
        
        #Available Models
        # llama-2-7b-chat
        # llama-2-13b-chat
        # llama-2-70b-chat
        self.model = "llama-2-13b-chat"

        sleep(1)
        
    def reconnect(self):
        print("Reconnecting websocket...")

        # Reinitialize the WebSocket
        self.session: Session = self.init_session()
        self.searching = False
        self.t: str = self.get_t()
        self.sid: str = self.get_sid()
        self.frontend_uuid = str(uuid4())
        self.frontend_session_id = str(uuid4())

        assert self.ask_anonymous_user(), "Failed to ask anonymous user"
        self.ws: WebSocketApp = self.init_websocket()
        
        
    def init_session(self) -> Session:
        session: Session = Session()

        uuid = str(uuid4())
        headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36 Edg/115.0.1901.183',
            'Origin': 'https://labs.perplexity.ai',
            'Host': 'labs-api.perplexity.ai'
        }
        
        session.headers.update(headers)
        session.get(url=f"https://www.perplexity.ai/search/{uuid}", allow_redirects=False)
                                 
        return session

    def get_t(self) -> str:
        return format(getrandbits(32), "08x")

    def get_sid(self) -> str:
        response = self.session.get(
            url=f"https://labs-api.perplexity.ai/socket.io/?EIO=4&transport=polling&t={self.t}",
        )

        response_text = response.text[1:]

        if response_text:
            try:
                response_json = loads(response_text)
                if 'sid' in response_json:
                    return response_json["sid"]
                else:
                    print('The "sid" key was not found in the response.')
                    return None
            except Exception as e:
                print('Error parsing JSON:', e)
                return None
        else:
            print('Empty response')
            return None


    def ask_anonymous_user(self) -> bool:
        response = self.session.post(
            url=f"https://labs-api.perplexity.ai/socket.io/?EIO=4&transport=polling&t={self.t}&sid={self.sid}",
            data="40{\"jwt\":\"anonymous-ask-user\"}"
        ).text

        return response == "OK"
                
    def get_cookies_str(self) -> str:
        cookies = ""
        for key, value in self.session.cookies.get_dict().items():
            cookies += f"{key}={value}; "
        return cookies[:-2]
   
    def on_open(self, ws):
        print("Websocket connection opened.")
        self.ws_connected = True
        self.ws.send("2probe")
        
    def on_message(self, _, message):
        if message is not None and isinstance(message, str):
            #print(message)
            if message == "2":
                self.ws.send("3")
            elif message == "3probe":
                self.ws.send("5")
            elif message == "6":
                if self.ws:
                    if self.ws_message != "":
                        self.ws.send(self.ws_message)

            if (self.searching) and message.startswith(f"42[\"{self.model}_query_progress"):
                # Check if the string contains '"status":"completed"' and '"final":true'
                if '"status":"completed"' in message and '"final":true' in message:
                    # Extract the output from the message
                    start = message.find('"output":"') + len('"output":"')
                    end = message.find('","final"')
                    output = message[start+1:end]
                    self.answer = output
                    self.searching = False
        else:
            print('The message is None or not a string.')
                
    def on_close(self, ws, close_status_code, close_msg):
        print("Websocket connection closed.", close_status_code, close_msg)
        self.ws_connected = False
        self.reconnect()  # Call reconnect method


    def on_error(self, ws, error):
        print(f"Websocket error: {error}")
        self.reconnect()  # Call reconnect method
    
    def init_websocket(self) -> websocket.WebSocketApp:       
        headers = {
            "Host": "labs-api.perplexity.ai",
            "Connection": "Upgrade",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36 Edg/115.0.1901.183",
            "Upgrade": "websocket",
            "Origin": "https://labs.perplexity.ai",
            "Cookie": self.get_cookies_str()
        }

        self.ws = WebSocketApp(
            url=f"wss://labs-api.perplexity.ai/socket.io/?EIO=4&transport=websocket&sid={self.sid}",
            header=headers,
            on_open=self.on_open,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
        )
        ws_thread = Thread(target=self.ws.run_forever, kwargs={'sslopt': {"cert_reqs": ssl.CERT_NONE}})
        ws_thread.daemon = True
        ws_thread.start()
        return self.ws

    def auth_session(self) -> None:
        self.session.get(url="https://www.perplexity.ai/api/auth/session")

    def search(self, query: str):
        formatted_query = query.replace('\n', '\\n').replace('\t', '\\t')
        self.query_str = formatted_query

        # If already searching, return an error, reset the searching flag, and retry
        if self.searching:
            print("Already searching...")
            self.searching = False
            return self.search(query)

        self.searching = True
        self.n += 1
        self.ws_message: str = f'42["perplexity_playground",{{"model":"{self.model}","messages":[{{"role":"user","content":"{formatted_query}","priority":0}}]}}]'
            
        # Waiting for connection to open
        while not self.ws.sock or not self.ws.sock.connected:
            print("Waiting for connection to open...")
            sleep(1)

        self.ws.send(self.ws_message)

        # Waiting for search to complete
        while self.searching:
            #print("Searching...")
            sleep(1)

        # Process the response
        if self.answer != "":
            formatted_output = self.answer.replace('\\n', '\n').replace('\\t', '\t')
            self.testcloseconnection += 1
            return formatted_output
        else:
            self.searching = False  # Reset the searching flag before retrying
            return self.search(query)  # Recursive call if there is an error

        
