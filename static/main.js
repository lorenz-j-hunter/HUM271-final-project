hidden = 'content-visibility: hidden;';
visible = 'content-visibility: visible;';
/*This resets the settings.
Learn more in activate_b.js.*/
function reset_bsky() {
  localStorage.setItem('visibility_b', hidden);
  localStorage.setItem('visibility_b_stream', hidden);
}
function reset_x() {
  localStorage.setItem('visibility_x', hidden);
}
function reset_pornhub() {
  localStorage.setItem('visibility_p', hidden);
}