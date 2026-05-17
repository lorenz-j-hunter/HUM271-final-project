/*We define a function in which a link initially is hidden, but becomes visible
once the user completes certain actions.*/
document.addEventListener('DOMContentLoaded', () => {
  //By default, the link is invisible. 
  if (!localStorage.getItem('visibility_b')) {
    localStorage.setItem('visibility_b', 'content-visibility: hidden;');
  }
  document.querySelector('#csv').style = localStorage.getItem('visibility_b')
});
// When the user clicks the button, the link becomes visible and remains so after page reloads.
function activate() {
  document.querySelector('#csv').style = 'content-visibility: visible;';
  localStorage.setItem('visibility_b', 'content-visibility: visible;');
}