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

/*Here we define something that lets something activate only once the worker is
done. It's for rest*/
async function wait_for_worker() {
  while (true) {
    //Since the two request types use the same database, they
    //can fetch from the same function.
    const res = await fetch('/worker_status');
    const data = await res.json();
    if (data.done == 'true') { 
      console.log('data.done==true');
      document.querySelector('#rest-csv').style = visible;
      document.querySelector('#success').style = visible;
      break;
    }
    await new Promise(r => setTimeout(r, 200));
  }
}

wait_for_worker();

/*Click the hidden download link.*/
function click_link() {
  document.querySelector('#download-link').click()
}
