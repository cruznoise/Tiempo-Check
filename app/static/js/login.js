      $('#login-form').on('submit', function(e) {
      e.preventDefault();

      $.ajax({
        url: "/login",
        method: "POST",
        contentType: "application/json",
        data: JSON.stringify({
          correo: $('#correo').val(),
          contraseña: $('#contraseña').val()
        }),
        success: function(res) {
          if (res.success) {
            window.location.href = "/dashboard";
          } else {
            $('#error').fadeIn();
          }
        },
        error: function() {
          $('#error').text("Error del servidor").fadeIn();
        }
      });
    });
  
  document.addEventListener("DOMContentLoaded", function () {
    const enlace = document.getElementById("mostrarRegistro");
    const formulario = document.getElementById("formRegistro");

    enlace.addEventListener("click", function (e) {
      e.preventDefault();
      formulario.style.display = formulario.style.display === "none" ? "block" : "none";
    });
  });