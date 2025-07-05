from http.server import BaseHTTPRequestHandler, HTTPServer
from io import StringIO
import threading

_data_lock = threading.Lock()
_data = StringIO()

def update_data(new_data):
    global _data
    with _data_lock:
        _data = StringIO(new_data)

class CSVDownloadHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global _data
        if self.path == "/":
            with _data_lock:
                csv_content = _data.getvalue()

            csv_bytes = csv_content.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/csv")
            self.send_header("Content-Disposition", "attachment; filename=LOG.csv")

            if csv_content:
                self.send_header("Content-Length", str(len(csv_bytes)))
                self.end_headers()
                self.wfile.write(csv_bytes)
            else:
                # Send default CSV header when no data
                default_csv = b"sender,value,date_time\n"
                self.send_header("Content-Length", str(len(default_csv)))
                self.end_headers()
                self.wfile.write(default_csv)

        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not found")

def run_server():
    port = 8000
    server_address = ('', port)
    httpd = HTTPServer(server_address, CSVDownloadHandler)
    print(f"Serving on http://localhost:{port}/")
    httpd.serve_forever()

if __name__ == "__main__":
    run_server()