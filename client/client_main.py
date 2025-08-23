from network import SocketClient
from network.protocol_handler import ProtocolHandler

def main():
    client = SocketClient("127.0.0.1", 12345)
    client.connect()

    msg = build_message("LOGIN", "nhuan123")
    client.send(msg)

    response = client.receive()
    command, content = parse_message(response)
    print(f"Server responded with: {command} - {content}")

    client.close()

if __name__ == "__main__":
    main()