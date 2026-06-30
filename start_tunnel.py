"""
start_tunnel.py — Opens a public HTTPS tunnel to the local Flask backend.
Requires: pip install pyngrok
Usage: python start_tunnel.py
"""
from pyngrok import ngrok, conf
import time, subprocess, sys, os

# Kill any existing ngrok
ngrok.kill()

# Start a tunnel to port 5000
print("Starting tunnel to http://127.0.0.1:5000 ...")
http_tunnel = ngrok.connect(5000, "http")
public_url = http_tunnel.public_url.replace("http://", "https://")

print("=" * 60)
print(f"  PUBLIC BACKEND URL: {public_url}")
print(f"  API URL:            {public_url}/api")
print("=" * 60)
print("Keep this window OPEN. Press Ctrl+C to stop.")
print()

# Write the URL to a file so another script can read it
with open("tunnel_url.txt", "w") as f:
    f.write(public_url)

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\nTunnel closed.")
    ngrok.kill()
