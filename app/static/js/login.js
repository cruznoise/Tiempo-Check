$(document).ready(function() {
  const loginSection = $('#login-section');
  const registroSection = $('#registro-section');
  const errorMsg = $('#error-msg');

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
          errorMsg
            .text(" Correo o contraseña incorrectos")
            .removeClass("d-none")
            .fadeIn();
        }
      },
      error: function() {
        errorMsg
          .text(" Error del servidor")
          .removeClass("d-none")
          .fadeIn();
      }
    });
  });

  // Manejo de registro
  $('#formRegistro').on('submit', function(e) {
    e.preventDefault();
    $.ajax({
      url: "/registro",
      method: "POST",
      contentType: "application/json",
      data: JSON.stringify({
        nombre: $('input[name="nombre"]').val(),
        correo: $('input[name="correo"]').val(),
        contraseña: $('input[name="contraseña"]').val()
      }),
      success: function(res) {
        if (res.success) {
          window.location.href = "/dashboard";
        } else {
          errorMsg
            .text("⚠️ No se pudo registrar. " + (res.message || "Intenta de nuevo."))
            .removeClass("d-none")
            .fadeIn();
        }
      },
      error: function() {
        errorMsg
          .text("❌ Error en el servidor durante el registro")
          .removeClass("d-none")
          .fadeIn();
      }
    });
  });

  // Alternar entre login y registro con animación
  $('#mostrarRegistro').on('click', function(e) {
    e.preventDefault();
    loginSection.fadeOut(300, function() {
      registroSection.fadeIn(300).removeClass('hidden');
    });
  });

  $('#mostrarLogin').on('click', function(e) {
    e.preventDefault();
    registroSection.fadeOut(300, function() {
      loginSection.fadeIn(300);
    });
  });
});
