/*We define a function in which a link initially is hidden, but becomes visible
once the user completes certain actions.*/
document.addEventListener('DOMContentLoaded', () => {
  //By default, the link is invisible. 
  if (!localStorage.getItem('visibility_p')) {
    localStorage.setItem('visibility_p', 'content-visibility: hidden;');
  }
  document.querySelector('#csv').style = localStorage.getItem('visibility_p')
});
// When the user clicks the button, the link becomes visible and remains so after page reloads.
function activate() {
  localStorage.setItem('visibility_p', 'content-visibility: visible;');
}

/*We define something here which responds if the user raises a FieldError.*/
const params = new URLSearchParams(window.location.search);
const code = params.get('code');
if (code == 1) {
  //... Then tell the user that they entered something wrong.
  document.querySelector('#error-message').hidden = "false";
} else {
  document.querySelector('#error-message').hidden = "true";
}