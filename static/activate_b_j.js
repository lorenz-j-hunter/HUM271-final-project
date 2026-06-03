hidden = 'content-visibility: hidden;';
visible = 'content-visibility: visible;';

/*Here we define something that lets something activate only once the worker is
done. It's for the stream*/
async function wait_for_worker() {
  while (true) {
    const res = await fetch('/worker_status');
    const data = await res.json();
    if (data.done == 'true') { 
      localStorage.setItem('visibility_b_stream', visible);
      document.querySelector('#stream-csv').style = localStorage.getItem('visibility_b_stream');
      document.querySelector('#success').style = visible;
      break;
    }
    await new Promise(r => setTimeout(r, 200));
  }
}

/*This activates once user selecte 'update database' and acts like 'wait_for_worker()'.*/
async function backfill() {
  //Activate when the user clicks the 'Update Database' button.
  while (true) {
    document.addEventListener('clickedUpdate', () => {
      //Hide the 'Download csv' button until the backfill has completed.
      document.querySelector('#download-link').style = hidden;
      const res = await fetch('/worker_status');
      const data = await res.json();
      if (data.done == 'true') { 
        document.querySelector('#download-link').style = visible;
        break;
      }
      await new Promise(r => setTimeout(r, 200));
    });
  } 
}

wait_for_worker();

backfill();

/*Click the hidden download link.*/
function click_link() {
  document.querySelector('#download-link').click();
}

function dispatch_event() {
  //Dispatch an event when user clicks a button.
  document.dispatchEvent(
    new CustomEvent("clickedUpdate", {
        detail: { reason: "clicked update" }
    })
  );
}
