from flask import Flask, render_template, request
import requests

url = "https://api.geekflare.com/webscraping"

headers = {
    "x-api-key": "mEfnWayVwrU9QVtDtAF0CG8PFpfizNTy",
    "Content-Type": "application/json",
}

payload = {
  "url" : "https://bsky.app",
  "device": "desktop",
  "format": [
    "html"
  ],
  "renderJS": True,
  "blockAds": True,
  "stealth": False
}

response = requests.post(
    url,
    json=payload,
    headers=headers
)

print(response.json())
app = Flask(__name__)

@app.route('/', methods=['GET','POST'])
def main():
    """Open the main route for the app."""
    return render_template('main.html')