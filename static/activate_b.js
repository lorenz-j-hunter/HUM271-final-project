hidden = 'content-visibility: hidden;';
visible = 'content-visibility: visible;';
/*We define a function in which a link initially is hidden, but becomes visible
once the user completes certain actions.*/
/*We define a function for which the stream link is initially hidden, but becomes visible
once the user enters their stream data.*/
document.addEventListener('DOMContentLoaded', () => {
  //By default, the link is invisible. 
  if (!localStorage.getItem('visibility_b')) {
    localStorage.setItem('visibility_b', hidden);
  }
  if (!localStorage.getItem('visibility_b_stream')) {
    localStorage.setItem('visibility_b_stream', hidden);
  }
  document.querySelector('#csv').style = localStorage.getItem('visibility_b')
  document.querySelector('#stream-csv').style = localStorage.getItem('visibility_b_stream')
});
// When the user clicks the button, the link becomes visible and remains so after page reloads.
function activate() {
  localStorage.setItem('visibility_b', visible);
}

/*Here we define something that lets something activate only once the worker is
done.*/
async function wait_for_worker() {
  while (true) {
    const res = await fetch('/worker_status');
    const data = await res.json();
    if (data.done) break;
    await new Promise(r => setTimeout(r, 500));
  }

  localStorage.setItem('visibility_b_stream', visible);
  document.querySelector('#stream-csv').style = localStorage.getItem('visibility_b_stream')
}

wait_for_worker();
