import socket


def check_server(address, port):
    # Create a TCP socket
    s = socket.socket()
    s.settimeout(1)
    try:
        s.connect((address, port))
        return True
    except socket.error as e:
        return False
    finally:
        s.close()
