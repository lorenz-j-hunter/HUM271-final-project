hidden = 'content-visibility: hidden;';
visible = 'content-visibility: visible;';

document.addEventListener('DOMContentLoaded', () => {
  //get previous input data from window
  const params = new URLSearchParams(window.location.search);
  const pattern = params.get('pattern');
  console.log(`pattern=${pattern}`);
  if (pattern == 'post') {
    localStorage.setItem('isposts', 'true');
  } else {
    localStorage.setItem('isposts', 'false');
  }
  //Only if the user has selected 'posts' on the page before
  //can the user choose a querystring.
  if (localStorage.getItem('isposts') == 'true') {
    document.querySelector('#querystring').style = visible;
  }
});

function show_mark_blocks() {
  if (localStorage.getItem('isposts') == 'true') {
    document.querySelector('#show-mark-blocks').style = visible;
    document.querySelector('#show-querystring').style = hidden;
  } else {
    document.querySelector('#show-mark-blocks').style = visible;
  }
}

function show_querystring() {
  document.querySelector('#show-mark-blocks').style = hidden;
  document.querySelector('#show-querystring').style = visible;
}