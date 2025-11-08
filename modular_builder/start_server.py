#!/usr/bin/env python3
"""
Simple HTTP Server for Nova Skyrift Prompt Builder
Fixes Chrome file access issues by serving files over HTTP instead of file://

Usage: 
1. Double-click this file, or
2. Run from command line: python start_server.py
3. Open the URL shown in your browser
"""

import http.server
import socketserver
import webbrowser
import os
import sys
from pathlib import Path

# Configuration
PORT = 8000
HTML_FILE = "Nova_skyrift_darkside_adventures_newnogood.html"  # Main HTML file to open

def find_available_port(start_port=8000):
    """Find an available port starting from start_port"""
    port = start_port
    while port < start_port + 100:
        try:
            with socketserver.TCPServer(("", port), None) as test_server:
                return port
        except OSError:
            port += 1
    return None

def main():
    # Change to the script's directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    print("🚀 Nova Skyrift Prompt Builder Server")
    print("=" * 50)
    
    # Find available port
    port = find_available_port(PORT)
    if port is None:
        print("❌ Could not find an available port!")
        input("Press Enter to exit...")
        return
    
    # Set up the server
    handler = http.server.SimpleHTTPRequestHandler
    
    # Enable CORS for local development
    class CORSHTTPRequestHandler(handler):
        def end_headers(self):
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            super().end_headers()
    
    try:
        with socketserver.TCPServer(("", port), CORSHTTPRequestHandler) as httpd:
            url = f"http://localhost:{port}"
            html_url = f"{url}/{HTML_FILE}"
            
            print(f"✅ Server starting on port {port}")
            print(f"📁 Serving files from: {script_dir}")
            print(f"🌐 Server URL: {url}")
            print(f"🎯 Prompt Builder: {html_url}")
            print("")
            print("📋 Available files:")
            for file in sorted(script_dir.glob("*.html")):
                print(f"   • {url}/{file.name}")
            print("")
            print("🔧 This fixes the Chrome file access issue!")
            print("💡 Your CSV category files will now load properly.")
            print("")
            print("Press Ctrl+C to stop the server")
            print("=" * 50)
            
            # Try to open the browser automatically
            try:
                webbrowser.open(html_url)
                print(f"🌐 Opening {HTML_FILE} in your default browser...")
            except:
                print(f"⚠️  Could not auto-open browser. Please visit: {html_url}")
            
            # Start serving
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Server error: {e}")
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()