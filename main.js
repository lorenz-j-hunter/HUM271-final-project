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

document.addEventListener('DOMContentLoaded', function() {
  //The result from scraping was sent in the HTML file this script acts on. Here it is. 
  text: String = document.querySelector('#show_word_count').value
  if (!localStorage.getItem('word_count')) {
    localStorage.setItem('word_count', text[0])
  }

  word_count = localStorage.getItem('word_count')
  document.querySelector('#show_word_count').innerHTML = word_count
})