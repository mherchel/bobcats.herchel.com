#!/usr/bin/env python3
"""
Simple HTTP server for testing the Lacrosse Goal Songs soundboard locally.
Run this script and open http://localhost:8080 in your browser.
"""

import http.server
import socketserver
import sys
from pathlib import Path

PORT = 8080
DIRECTORY = Path(__file__).parent.resolve()

class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DIRECTORY), **kwargs)

    def end_headers(self):
        # Add MIME type for WebM files
        self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()

def main():
    handler = CustomHTTPRequestHandler

    try:
        with socketserver.TCPServer(("", PORT), handler) as httpd:
            print("=" * 60)
            print("🎵 Lacrosse Goal Songs Soundboard Server")
            print("=" * 60)
            print(f"\n✓ Server running at: http://localhost:{PORT}")
            print(f"✓ Serving files from: {DIRECTORY}")
            print("\nPages:")
            print(f"  • Landing page: http://localhost:{PORT}/")
            print(f"  • Varsity:      http://localhost:{PORT}/varsity.html")
            print(f"  • JV:           http://localhost:{PORT}/jv.html")
            print("\nPress Ctrl+C to stop the server\n")
            print("=" * 60)

            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\n✓ Server stopped")
        sys.exit(0)
    except OSError as e:
        if e.errno == 48:  # Address already in use
            print(f"\n✗ Error: Port {PORT} is already in use")
            print(f"  Stop the other server or change PORT in this script")
            sys.exit(1)
        else:
            raise

if __name__ == '__main__':
    main()
