hidden = 'content-visibility: hidden;';
visible = 'content-visibility: visible;';
/*We define a function in which a link initially is hidden, but becomes visible
once the user completes certain actions.*/
document.addEventListener('DOMContentLoaded', () => {
  //By default, the link is invisible. 
  if (!localStorage.getItem('visibility_b')) {
    localStorage.setItem('visibility_b', hidden);
  }
  if (!localStorage.getItem('visibility_b_stream')) {
    localStorage.setItem('visibility_b_stream', hidden);
  }
  document.querySelector('#csv').style = localStorage.getItem('visibility_b');
  document.querySelector('#jetstream').style = localStorage.getItem('visibility_b_stream');

  //Once the user enters their dropdown, they can choose.
  //By default, the #rest and #jetstream are invisible.
  const params = new URLSearchParams(document.location.search);
  console.log(`params=${params}`)
  const option = params.get('option');
  if (option) {
    if (option == 'rest') {
      document.querySelector('#rest').style = visible;
    } else if (option == 'jetstream') {
      document.querySelector('#jetstream').style = visible;
    }
  }
});
// When the user clicks the button, the link becomes visible and remains so after page reloads.
function activate() {
  localStorage.setItem('visibility_b', visible);
}

