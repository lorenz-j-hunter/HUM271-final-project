hidden = 'content-visibility: hidden;';
visible = 'content-visibility: visible;';

/*Show the user the form that they chose.*/
function show(arg) {
  document.querySelectorAll('.show').forEach(form => {
    /*if thing has 'arg' then show it, else don't*/
    console.log(`form=${form}. form.id=${form.id}.`);
    if (form.id == arg) {
      form.style = visible;
    } else {
      form.style = hidden;
    }
  });
}

/*Submit all data from each form at once*/
var btn = null 
document.addEventListener('DOMContentLoaded', () => {
  btn = document.querySelector('#ctu');
  btn.addEventListener("click", () => {
    const forms = document.querySelectorAll('.forms');
    const data = new FormData();

    forms.forEach(form => {
      new FormData(form).forEach((value, key) => {
        data.append(key, value);
      });
    });

    localStorage.setItem('data', data);
  });
});
