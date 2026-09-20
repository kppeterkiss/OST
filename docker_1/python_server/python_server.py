import datetime
import socketserver
import time

class MyTCPHandler(socketserver.BaseRequestHandler):
    def handle(self):
        try:
            # Beolvassuk a beérkező adatot (max 1024 bájt)
            self.data = self.request.recv(1024).strip()
            
            # Kiíratjuk a konzolra (a .decode() átalakítja a bájtokat olvasható szöveggé)
            print(datetime.datetime.now(), " - {} wrote:".format(self.client_address[0]))
            print(' data: ', self.data.decode('utf-8'))
            
            # Válasz küldése: a sztringet bájttá alakítjuk az .encode() segítségével
            server_hello = "Python Server is up and running.\n"
            send_data = server_hello.encode('utf-8')
            
            self.request.sendall(send_data)
        except Exception as e:
            print('Exception occurred in handle:', e)
       
if __name__ == "__main__":
    # "0.0.0.0" kell, hogy Dockerben kívülről is elérhető legyen!
    HOST, PORT = "0.0.0.0", 9999
    print(f"Szerver elindult a {PORT}-es porton...")
    with socketserver.TCPServer((HOST, PORT), MyTCPHandler) as server:
        server.serve_forever()
