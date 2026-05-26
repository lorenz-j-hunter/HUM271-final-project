hidden = 'content-visibility: hidden;';
visible = 'content-visibility: visible;';
/*This resets the settings.
Learn more in activate_b.js.

Upon clicking their respective links, they activaet*/
function reset_bsky() {
  localStorage.removeItem('visibility_b');
  localStorage.removeItem('visibility_b_stream');
}
function reset_x() {
  localStorage.setItem('visibility_x', hidden);
}
function reset_pornhub() {
  localStorage.setItem('visibility_p', hidden);
}