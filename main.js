const options = {
  method: 'POST',
  headers: {'x-api-key': '<api-key>', 'Content-Type': 'application/json'},
  body: JSON.stringify({
    url: 'https://bsky.app',
    device: 'desktop',
    blockAds: true,
    renderJS: true,
    proxyCountry: 'us',
    format: ['html-llm'],
    fileOutput: false,
    stealth: false,
    waitTime: 0,
    extractionMode: 'default'
  })
};

fetch('https://api.geekflare.com/webscraping', options)
  .then(res => res.json())
  .then(res => console.log(res))
  .catch(err => console.error(err));

//Work with the response gathered from app.py.
console.log('here')