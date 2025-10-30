$(document).ready(function() {
  const loginSection = $('#login-section');
  const registroSection = $('#registro-section');
  const errorMsg = $('#error-msg');

  // === Manejo de Login (Endpoint Mantenido) ===
  $('#login-form').on('submit', function(e) {
    e.preventDefault();
    $.ajax({
      // Endpoint Mantenido
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

  // === Manejo de registro (Endpoint Mantenido) ===
  $('#formRegistro').on('submit', function(e) {
    e.preventDefault();
    // Se usa el mismo errorMsg para mostrar alertas de registro
    const errorMsgRegistro = $('#error-msg-registro').length ? $('#error-msg-registro') : errorMsg;

    $.ajax({
      // Endpoint Mantenido
      url: "/admin/registro",
      method: "POST",
      contentType: "application/json",
      data: JSON.stringify({
        nombre: $('input[name="nombre_reg"]').val(),
        // Se usa el nombre de campo 'correo' que usa el HTMLN estandarizado
        correo: $('input[name="correo_reg"]').val(), 
        // Se usa el nombre de campo 'contraseña' que usa el HTMLN estandarizado
        contrasena: $('input[name="contraseña_reg"]').val() 
      }),
      success: function(res) {
        if (res.success) {
          window.location.href = "/dashboard";
        } else {
          errorMsgRegistro
            .text("⚠️ No se pudo registrar. " + (res.message || "Intenta de nuevo."))
            .removeClass("d-none")
            .fadeIn();
        }
      },
      error: function() {
        errorMsgRegistro
          .text("❌ Error en el servidor durante el registro")
          .removeClass("d-none")
          .fadeIn();
      }
    });
  });

  // === Alternar entre login y registro con animación (Mejora de UI) ===
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