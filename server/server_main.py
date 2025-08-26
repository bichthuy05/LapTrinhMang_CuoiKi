import socket, threading
from server.client_handler import handle_client
from server.utils.logger import get_logger
from config.server_config import HOST, PORT

logger = get_logger("server")

def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen(50)
    logger.info(f"Server started on {HOST}:{PORT}")
    try:
        while True:
            client_socket, addr = server_socket.accept()
            logger.info(f"New connection from {addr}")
            t = threading.Thread(target=handle_client, args=(client_socket, addr), daemon=True)
            t.start()
    except KeyboardInterrupt:
        logger.info("Server stopping...")
    finally:
        server_socket.close()

if __name__ == "__main__":
    start_server()
