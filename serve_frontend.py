#!/usr/bin/env python3
"""
Simple HTTP Server for Frontend
Serves the HTML/CSS/JS frontend files
"""
import http.server
import socketserver
import webbrowser
import os
import sys
from pathlib import Path

def serve_frontend(port=3000, open_browser=True):
    """Serve the frontend files on the specified port"""
    # Get the frontend directory path
    current_dir = Path(__file__).parent
    frontend_dir = current_dir / "frontend"
    
    if not frontend_dir.exists():
        print(f"Error: Frontend directory not found at {frontend_dir}")
        return
    
    # Change to frontend directory
    os.chdir(frontend_dir)
    
    # Create server
    handler = http.server.SimpleHTTPRequestHandler
    
    with socketserver.TCPServer(("", port), handler) as httpd:
        url = f"http://localhost:{port}"
        print(f"Serving frontend at {url}")
        print("Press Ctrl+C to stop the server")
        
        if open_browser:
            webbrowser.open(url)
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server...")
            httpd.shutdown()

if __name__ == "__main__":
    port = 3000
    
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print("Invalid port number. Using default port 3000.")
    
    serve_frontend(port)
