import socket
import selectors
from .lib import SMessage, MidSMessage
import traceback
import time, os
from .utils import append_to_txt, save_json, load_json
from collections import defaultdict
import random
from tabulate import tabulate
# import tempfile

## add for demo 
def fake_time(net):
    return random.randint(1,100)

class Server(object):
    """ Multi-connection 
    Run server in Machine A.
    Run clinet in Machine B. 
    And mini-socket is able to build connect between A and B.

    In basic Client and Sever:
        B -> send data -> A -> save data in some files -> send reponse to B -> close.
        B -> requry data -> A -> parse query and send data back -> B recv data and send response to A -> close.
    
    demo mode: show the case in tutorial
    """
    def __init__(self, host, port, 
                 save=True, 
                 demo=False, 
                 msg=SMessage, 
                 query_file=None, 
                 ip_filter=None,
                 logger=None):
        super().__init__()
        self.host = host
        self.port = port
        self.logger = logger if logger else print
        self.save = False
        self.msg_func = msg
        self._query_file = query_file
        self._ip_filter = ip_filter
        self._demo = demo
        self._cget_times = defaultdict(int)
        self._cput_times = defaultdict(int)
        self._ccon_times = defaultdict(int)

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sel  = selectors.DefaultSelector()

        self.sock.bind((host, port))
        self.sock.listen()
        self.sock.setblocking(False)
        self.sel.register(self.sock, selectors.EVENT_READ, data=None)
        if save is True:
            self._prefix = "./_recv_"
            self.save = True
        elif isinstance(save, str):
            self._prefix = save
            self.save = True

    def __repr__(self):
        repr = f"Server(host={self.host}," \
             + f"port={self.port}," \
             + f"save={self.save}," \
             + f"demo={self._demo}," \
             + f"query_file={self._query_file}," \
             + f"ip_filter={self._ip_filter})" 
        return repr

    def accept_wrapper(self, accpet_sock):
        conn, addr = accpet_sock.accept()   
        self.logger("accepted connection from", addr)
        if self._ip_filter is not None and addr[0] not in self._ip_filter:
            self.logger("Not White List connections")
        else:
            self._ccon_times[addr[0]] += 1
            conn.setblocking(False) 
            message = self.msg_func(self.sel, conn, addr, self._query_file, self.logger)
            self.sel.register(conn, selectors.EVENT_READ, data=message)
    
    def run(self):
        try:
            while True:
                # waiting connection
                events = self.sel.select(timeout=None)
                for key, mask in events:
                    if key.data is None:
                        self.accept_wrapper(key.fileobj)
                    else:
                        message = key.data
                        try:
                            message.process_events(mask)
                            if self.save and mask==2:
                                self.save_events(message)
                                if message.stat == "get":
                                    self._cget_times[message.connect_ip] += 1
                                elif message.stat == "put":
                                    self._cput_times[message.connect_ip] += 1
                                else:
                                    raise TypeError(message.stat)
                        except Exception:
                            self.logger(
                                "main: error: exception for",
                                f"{message.addr}:\n{traceback.format_exc()}",
                            )
                            message.close()

        except KeyboardInterrupt:
            self.logger("caught keyboard interrupt, exiting server")
        finally:
            self.call_after_run()

    def save_events(self, message):
        # case for latency and network
        try:
            content = message.request
            request_type = message.jsonheader.get("content-type")
            if "json" in request_type:
                raise NotImplementedError("Json is not support to save")
            self.logger(type(content), request_type)
            str_content = content.decode("utf-8")
            val_content = str_content.split(">>")[-1].strip()
            self.logger(val_content, type(val_content), eval(val_content))
            self._filename = (self._prefix + str(message.connect_ip) + ".txt")
            # only return string  type data
            append_to_txt(self._filename, val_content) # 
            self.logger(f"message append to {self._filename}") 
            if self._demo:
                # cal latency
                latency = fake_time(val_content)
                all_request = load_json(message.request_file)
                all_request.update({val_content: latency})
                self.logger(" \n recv new net latency, updating request file")
                save_json(message.request_file, all_request)
                
        except NotImplementedError:
            self.logger("Save failed, Only save recv data from client")
        finally:
            self.logger("Exit saving message")

    def display(self):
        header = ["ip", "Query Times", "Put Times", "Connect Times"]
        msg = []
        for ip, time in self._ccon_times.items():
            msg.append([ip, self._cget_times[ip], self._cput_times[ip], self._ccon_times[ip]])
        table = tabulate(msg, header, tablefmt="grid")
        self.logger("\n", table)
        
    @property
    def prefix(self):
        return self._prefix

    @property
    def latest_save_file(self):
        return self._filename

    def call_after_run(self):
        self.sel.close()
        self.logger("\n ---- Count Connection ---\n")
        self.display()

class MidServer(Server):
    def __init__(self, host, port, save=True, demo=False, msg=MidSMessage):
        super().__init__(host, port, save=save, demo=demo, msg=msg)

    def save_events(self, message):
        # alway flush request file
        try:
            content = message.request
            request_type = message.jsonheader.get("content-type")
            if "json" in request_type:
                raise NotImplementedError("Json is not support to save")
            str_content = content.decode("utf-8")
            split_content = str_content.split(">>")
            val_content = split_content[-1][1:]
            type_content = split_content[0][:-1]
            # according type_content to save val_content
            if type_content.lower() == "net":
                # to json, re-write the request file
                print(" \n >> Note: recv new nets, reflush  request file")
                val_content_dict = {"net": val_content}  # make sure query latest net
                save_json(message.request_file, val_content_dict)
            elif type_content.lower() == "lat":
                print(" \n >> recv latency")
                ori_request = load_json(message.request_file)
                str_net = ori_request["net"]
                val_content_dict = {str_net: val_content}
                print(" \n >> Note: recv net latency, reflushing request file")
                save_json(message.request_file, val_content_dict)
        except NotImplementedError:
            print("Save failed, Only save recv data from client")
        finally:
            print("Exit saving message")


    
    


    