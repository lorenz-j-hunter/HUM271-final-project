from flask import Flask, render_template, request
import requests # pyright: ignore[reportMissingModuleSource]

url = "https://public.api.bsky.app/xrpc/app.bsky.feed.getAuthorFeed?actor=mrsbettybowers.bsky.social"

headers = {
    "x-api-key": "mEfnWayVwrU9QVtDtAF0CG8PFpfizNTy",
    "Content-Type": "application/json",
}

payload = {
  "url" : "https://bsky.app",
  "device": "desktop",
  "format": [
    "json"
  ],
  "renderJS": True,
  "blockAds": True,
  "stealth": False
}

response = requests.get(
    url
#    json=payload,
#    headers=headers
)

# Open the app
app = Flask(__name__)

@app.route('/', methods=['GET','POST'])
def main():
    """Open the main route for the app."""
    print(response.json())
    return render_template('main.html', response=response.json())