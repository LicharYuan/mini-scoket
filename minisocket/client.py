# copy to clinet end
import sys
import socket
import selectors
import traceback
from .lib import CMessage

class Client(object):
    def __init__(self, host, port, action, value, msg=CMessage, verbose=True):
        super().__init__()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sel = selectors.DefaultSelector()
        self.host = host
        self.port = port
        self.action = action
        self.value = value
        self.msg_func = msg
        self._connect = "UNKONW" 
        self._recv_info = None
        self.verbose = verbose

    def create_request(self, action, value):
        if action == "search":
            # GET 
            return dict(
                type="text/json",
                encoding="utf-8",
                content=dict(action=action, value=value),
            )
        else:
            # POST
            content = "{} >> {}".format(action, value)
            # encoder action to content
            return dict(
                type="binary/custom-client-binary-type",
                encoding="binary",
                content=bytes(content, encoding="utf-8"),
            )
    
    def start_connection(self, host, port, action, value):
        request = self.create_request(action, value)
        self.sock.setblocking(False)
        addr = (host, port)
        self.sock.connect_ex(addr)
        events = selectors.EVENT_READ | selectors.EVENT_WRITE 
        message = self.msg_func(self.sel, self.sock, addr, request, self.verbose)
        self.sel.register(self.sock, events, data=message)

    def run(self):
        self.start_connection(self.host, self.port, self.action, self.value)
        try:
            while True:
                events = self.sel.select(timeout=1)
                for key, mask in events:
                    message = key.data
                    try:
                        message.process_events(mask)
                        self._recv_info = message.request_result
                        self._connect = True
                    except Exception:
                        if self.verbose:
                            print(
                                "main: error: exception for",
                                "{}:\n{}".format(message.addr, traceback.format_exc()),
                            )
                        self._connect = False
                        message.close()
                # check socket being monitored to continue
                if not self.sel.get_map():
                    break
        except KeyboardInterrupt:
            print("caught keyboard interrupt, exiting client")
            exit("Interrupt by user")
        finally:
            self.sel.close()
    
    @property
    def is_connect(self):
        return self._connect

    @property
    def recv_info(self):
        return self._recv_info