import json
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import mimetypes
import pathlib
from datetime import datetime
from threading import Thread
import socket


IP = '127.0.0.1'
UDP_PORT = 5000
HTTP_PORT = 3000
message = {}


class HttpHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        pr_url = urllib.parse.urlparse(self.path)
        if pr_url.path == '/':
            self.send_html_file('index.html')
        elif pr_url.path == '/message':
            self.send_html_file('message.html')
        else:
            if pathlib.Path().joinpath(pr_url.path[1:]).exists():
                self.send_static()
            else:
                self.send_html_file('error.html', 404)

    def do_POST(self):
        data = self.rfile.read(int(self.headers['Content-Length']))
        run_client(data=data)
        self.send_response(302)
        self.send_header('Location', '/')
        self.end_headers()

    def send_html_file(self, filename, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        with open(filename, 'rb') as fd:
            self.wfile.write(fd.read())

    def send_static(self):
        self.send_response(200)
        mt = mimetypes.guess_type(self.path)
        if mt:
            self.send_header("Content-type", mt[0])
        else:
            self.send_header("Content-type", 'text/plain')
        self.end_headers()
        with open(f'.{self.path}', 'rb') as file:
            self.wfile.write(file.read())


def run(server_class=HTTPServer, handler_class=HttpHandler):
    server_address = ('', HTTP_PORT)
    http = server_class(server_address, handler_class)
    try:
        http.serve_forever()
    except KeyboardInterrupt:
        http.server_close()


def run_server(ip, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server = ip, port
    sock.bind(server)
    try:
        while True:
            data, address = sock.recvfrom(1024)
            print(f'SERVER: Received data: {data.decode()} from: {address}')
            data_parse = urllib.parse.unquote_plus(data.decode())
            data_dict = {key: value for key, value in [el.split('=') for el in data_parse.split('&')]}
            print(data_dict)
            message[str(datetime.now())] = data_dict
            with open('storage/data.json', 'w') as file:
                json.dump(message, file, indent=4, separators=(',', ': '))
            sock.sendto(data, address)
            print(f'SERVER: Send data: {data.decode()} to: {address}')
    except KeyboardInterrupt:
        print(f'Destroy server')
    finally:
        sock.close()


def run_client(ip: str = IP, port: int = UDP_PORT, data=None):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        server = ip, port
        sock.sendto(data, server)
        print(f'CLIENT Send data: {data.decode()} to server: {server}')
        response, address = sock.recvfrom(1024)
        print(f'CLIENT Response data: {response.decode()} from address: {address}')


t1 = Thread(target=run)
t2 = Thread(target=run_server, args=(IP, UDP_PORT))

if __name__ == '__main__':
    t1.start()
    t2.start()
    t1.join()
    t2.join()
