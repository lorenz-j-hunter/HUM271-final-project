hidden = 'content-visibility: hidden;';
visible = 'content-visibility: visible;';

/*Show the user the querystring entry.*/
function show_querystring() {
  document.querySelector('#show-querystring').style = visible;
  document.querySelector('#show-limit').style = hidden; 
}

/*Show the user the sample size entry.*/
function show_limit() {
  document.querySelector('#show-querystring').style = hidden;
  document.querySelector('#show-limit').style = visible; 
}