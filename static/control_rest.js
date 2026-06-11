hidden = 'content-visibility: hidden;';
visible = 'content-visibility: visible;';

function show_q_form() {
  document.querySelector('#q_form').style = visible;
  document.querySelector('#lim_form').style = hidden;
  document.querySelector('#cc_form').style = hidden;
}

function show_lim_form() {
  document.querySelector('#q_form').style = hidden;
  document.querySelector('#lim_form').style = visible;
  document.querySelector('#cc_form').style = hidden;
}

function show_cc_form() {
  document.querySelector('#q_form').style = hidden;
  document.querySelector('#lim_form').style = hidden;
  document.querySelector('#cc_form').style = visible;
}

/*Submit all data from each form at once*/
var btn = null 
document.addEventListener('DOMContentLoaded', () => {
  btn = document.querySelector('#ctu');
  btn.addEventListener("click", () => {
    console.log('button clicked');
    const forms = document.querySelectorAll('.forms');
    const data = new FormData();

    forms.forEach(form => {
      new FormData(form).forEach((value, key) => {
        data.append(key, value);
      });
    });
    
    const params = new URLSearchParams(data);
    fetch(`/get_rest_requests?data=${params}`, {
      method: "GET",
    }).then(response => response.text())
    .then(html => {
      document.open(html);
      document.write(html);
      document.close(html);
    });
  });
});
