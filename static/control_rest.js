hidden = 'content-visibility: hidden;';
visible = 'content-visibility: visible;';

document.addEventListener('DOMContentLoaded', () => {
  //By default, the link is invisible. 
  if (!localStorage.getItem('visibility')) {
    localStorage.setItem('visibility', hidden);
  }
  if (localStorage.getItem('isposts') == 'true') {
    localStorage.setItem('visibility', 'true');   
  }
  document.querySelector('#querystring').style = localStorage.getItem('visibility');
});

/*Click the hidden download link.*/
function click_link() {
  document.querySelector('#download-link').click()
}