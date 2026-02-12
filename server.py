from http.server import HTTPServer, SimpleHTTPRequestHandler
import json
import sqlite3
import urllib.parse
import os

class PILAHandler(SimpleHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/api/signup':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            
            try:
                # Handle JSON data
                if self.headers.get('Content-Type') == 'application/json':
                    data = json.loads(post_data)
                else:
                    # Fallback for form data
                    parsed = urllib.parse.parse_qs(post_data)
                    data = {k: v[0] for k, v in parsed.items()}

                fullname = data.get('fullname')
                email = data.get('email')
                password = data.get('password')

                if not fullname or not email or not password:
                    self.send_response(400)
                    self.end_headers()
                    self.wfile.write(b'{"error": "Missing fields"}')
                    return

                conn = sqlite3.connect('pila.db')
                c = conn.cursor()
                try:
                    c.execute('INSERT INTO users (fullname, email, password) VALUES (?, ?, ?)', (fullname, email, password))
                    conn.commit()
                    conn.close()
                    
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"message": "User registered successfully"}).encode('utf-8'))
                except sqlite3.IntegrityError:
                    conn.close()
                    self.send_response(409)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": "Email already exists"}).encode('utf-8'))
                    
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
        else:
            self.send_error(404, "File not found")

    def do_GET(self):
        # Serve static files normally
        return SimpleHTTPRequestHandler.do_GET(self)

if __name__ == '__main__':
    # Ensure database exists
    if not os.path.exists('pila.db'):
        conn = sqlite3.connect('pila.db')
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fullname TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()
        print("Database initialized.")

    server_address = ('', 8000)
    httpd = HTTPServer(server_address, PILAHandler)
    print("Server running on port 8000...")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass

