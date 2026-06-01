hidden = 'content-visibility: hidden;';
visible = 'content-visibility: visible;';

['#rest', '#jetstream'].forEach(option => {
  document.addEventListener('DOMContentLoaded', () => {
    document.querySelector(option).style = hidden;    
  });
});

function show_rest() {
  document.querySelector('#rest').style = visible;
  document.querySelector('#jetstream').style = hidden;
}

function show_jetstream() {
  document.querySelector('#rest').style = hidden;
  document.querySelector('#jetstream').style = visible;
}
