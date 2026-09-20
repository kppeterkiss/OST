import socket
import os

if __name__ == "__main__":
    HOST, PORT = "localhost", 9999
    HOST, PORT = "python_server", 9999





    
    binary_message = bytes([0, 0, 0])    

    # Create a socket (SOCK_STREAM means a TCP socket)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        # Connect to server and send data
        sock.connect((HOST, PORT))
        sock.sendall(binary_message)
        # Receive data from the server and shut down
        received = sock.recv(1024)
        print(received)

