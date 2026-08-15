// static/js/logout.js
$(function() {
  $('#logout-btn').on('click', function() {
    window.location.href = '/logout'; // o '/logout', según tu blueprint
  });
});
