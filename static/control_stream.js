hidden = 'content-visibility: hidden;';
visible = 'content-visibility: visible;';

document.addEventListener('DOMContentLoaded', () => {
  //get previous input data from window
  const params = new URLSearchParams(window.location.search);
  const pattern = params.get('pattern');
  console.log(`pattern=${pattern}`);
  if (pattern == 'post') {
    localStorage.setItem('isposts', 'true');
  } else if (pattern == 'false') {
    localStorage.setItem('isposts', 'false');
  }
  //Only if the user has selected 'posts' on the page before
  //can the user choose a querystring.
  //If they have, they can't select 'mark blocks'.
  if (localStorage.getItem('isposts') == 'true') {
    document.querySelector('#querystring').style = visible;
    document.querySelector('#mark-blocks').style = hidden;
    document.querySelector('#ctu-q-btn').style = visible;
    document.querySelector('#ctu-mb-btn').style = hidden;
  } else if (localStorage.getItem('isposts') == 'false') {
    document.querySelector('#querystring').style = hidden;
    document.querySelector('#mark-blocks').style = visible;
    document.querySelector('#ctu-q-btn').style = hidden;
    document.querySelector('#ctu-mb-btn').style = visible;
  }
});

function show_mark_blocks() {
  //If the user has selected 'posts' on the page before, they can
  //only see 'querystring'. And vice versa.
  if (localStorage.getItem('isposts') == 'false') {
    document.querySelector('#show-mark-blocks').style = visible;
    document.querySelector('#show-querystring').style = hidden;
  } else if (localStorage.getItem('isposts') == 'true') {
    document.querySelector('#show-mark-blocks').style = hidden;
    document.querySelector('#show-querystring').style = visible;
  }
}

function show_querystring() {
  //If the user has selected 'follows' on the page before, they can
  //only see 'mark-blocks'. And vice versa.
  if (localStorage.getItem('isposts') == 'false') {
    //because we're in 'posts', this 'show-mark-blocks' will not show anyway..
    document.querySelector('#show-mark-blocks').style = visible; 
    document.querySelector('#show-querystring').style = hidden;
  } else if (localStorage.getItem('isposts') == 'true') {
    document.querySelector('#show-mark-blocks').style = hidden;
    document.querySelector('#show-querystring').style = visible;
  }
}