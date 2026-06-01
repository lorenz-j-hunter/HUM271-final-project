hidden = 'content-visibility: hidden;';
visible = 'content-visibility: visible;';
/*We define a function in which a link initially is hidden, but becomes visible
once the user completes certain actions.*/
document.addEventListener('DOMContentLoaded', () => {
  //By default, the link is invisible. 
  if (!localStorage.getItem('visibility_b')) {
    localStorage.setItem('visibility_b', hidden);
  }
  document.querySelector('#csv').style = localStorage.getItem('visibility_b');
});
