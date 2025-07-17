from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import mimetypes
import pathlib
import socket
import threading
import datetime
from time import sleep
import json

HOST = '127.0.0.1'
SOCKET_PORT = 5000
HTTP_PORT = 3000


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

    def do_POST(self):
        data = self.rfile.read(int(self.headers['Content-Length']))
        data_parse = urllib.parse.unquote_plus(data.decode())
        data_dict = {key: value for key, value in [el.split('=') for el in data_parse.split('&')]}
        json_string = json.dumps(data_dict, indent=4, ensure_ascii=False)
        json_bytes = json_string.encode('utf-8')

        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.sendto(json_bytes, (HOST, SOCKET_PORT))  # SOCKET_PORT = 5000

        self.send_response(302)
        self.send_header('Location', '/')
        self.end_headers()

# Серверна частина
def echo_server(host, port):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.bind((host, port))
        while True:
            data, addr = s.recvfrom(1024)
            decoded = data.decode('utf-8')
            json_dictionary = json.loads(decoded)
            time_now = datetime.datetime.now()
            timestamp = str(time_now)
            result = {timestamp: json_dictionary}
            with open("storage/data.json", "r") as f:
                existing_data = json.load(f)
                existing_data.update(result)
                data_to_write = existing_data
                with open("storage/data.json", "w") as f:
                    json.dump(data_to_write, f, indent=4)

# Клієнтська частина
def http_server(server_class=HTTPServer, handler_class=HttpHandler):
    server_address = ('', HTTP_PORT)
    http = server_class(server_address, handler_class)
    try:
        http.serve_forever()
    except KeyboardInterrupt:
        http.server_close()


if __name__ == '__main__':
    server_thread = threading.Thread(target=echo_server, args=(HOST, SOCKET_PORT), daemon=True)
    server_thread.start()
    
    try:
        http_server()
    except KeyboardInterrupt:
        print("\nСервер зупинено через Ctrl+C")

    # http_thread = threading.Thread(target=http_server, daemon=True)
    
    # http_thread.start()
    # server_thread.join()
    # http_thread.join()


