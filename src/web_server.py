import socket
import os
import mimetypes
from datetime import datetime

class HTTPServer:
    def __init__(self, host='127.0.0.1', port=8080):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.static_dir = '../site'
        self.routes = {
            '/': 'index.html',
            '/about': 'about.html',
            '/team': 'team.html',
            '/journal': 'journal.html',
            '/resources': 'resources.html'
        }

    def serve_forever(self):
        self.socket.bind((self.host, self.port))
        self.socket.listen(5)
        print(f"Сервер запущен на http://{self.host}:{self.port}")

        while True:
            conn, addr = self.socket.accept()
            print(f"Подключение от {addr}")
            try:
                self.handle_request(conn)
            except Exception as e:
                print(f"Ошибка при обработке запроса: {e}")
            finally:
                conn.close()

    def handle_request(self, conn):
        data = conn.recv(1024).decode('utf-8')
        if not data:
            return

        request_line = data.split('\r\n')[0]
        method, path, _ = request_line.split()

        print(f"{datetime.now()} - {method} {path}")

        if method == 'GET':
            self.handle_get(conn, path)
        else:
            self.send_error(conn, 405, "Method Not Allowed")

    def handle_get(self, conn, path):
        if path in self.routes:
            file_path = os.path.join(self.static_dir, self.routes[path])
            self.serve_file(conn, file_path)
        else:
            file_path = os.path.join(self.static_dir, path.lstrip('/'))
            if os.path.exists(file_path) and not os.path.isdir(file_path):
                self.serve_file(conn, file_path)
            else:
                self.send_error(conn, 404, "Not Found")

    def serve_file(self, conn, file_path):
        try:
            with open(file_path, 'rb') as f:
                content = f.read()

            mime_type, _ = mimetypes.guess_type(file_path)
            if not mime_type:
                mime_type = 'text/html'

            response = (
                "HTTP/1.1 200 OK\r\n"
                f"Content-Type: {mime_type}\r\n"
                f"Content-Length: {len(content)}\r\n"
                "Connection: close\r\n"
                "\r\n"
            ).encode('utf-8') + content

            conn.sendall(response)
        except IOError:
            self.send_error(conn, 403, "Forbidden")

    def send_error(self, conn, code, message):
        error_page = f"""
        <html>
        <head><title>{code} {message}</title></head>
        <body>
        <h1>{code} {message}</h1>
        <p>An error occurred while processing your request.</p>
        </body>
        </html>
        """.encode('utf-8')

        response = (
            f"HTTP/1.1 {code} {message}\r\n"
            "Content-Type: text/html\r\n"
            f"Content-Length: {len(error_page)}\r\n"
            "Connection: close\r\n"
            "\r\n"
        ).encode('utf-8') + error_page

        conn.sendall(response)

if __name__ == '__main__':
    if not os.path.exists('../site'):
        os.makedirs('../site')
        print("Создана папка 'site'. Поместите туда файлы вашего сайта.")

    server = HTTPServer()
    server.serve_forever()