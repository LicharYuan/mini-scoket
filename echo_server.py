# from minisocket.server import MidServer as Server
from minisocket.server import Server as Server
import sys
from minisocket.utils import Logger
if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("usage:", sys.argv[0], "<host> <port>")
        sys.exit(1)

    host, port = sys.argv[1], int(sys.argv[2])
    logger = Logger("./server_0.log")
    server = Server(host, port, demo=True, logger=logger)
    print(f"file will saving to  {server.prefix}_*")
    server.run()
