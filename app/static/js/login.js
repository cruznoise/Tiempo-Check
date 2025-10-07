// --- login.js ---

// Referencias de elementos globales
const errorMsg = $('#error-msg');  // <<--- ESTA LÍNEA VA AQUÍ, ARRIBA

// Manejo de login
$('#login-form').on('submit', function (e) {
  e.preventDefault();
  $.ajax({
    url: '/login',
    method: 'POST',
    contentType: 'application/json',
    data: JSON.stringify({
      correo: $('#correo').val(),
      contraseña: $('#contraseña').val()
    }),
    success: function (res) {
      if (res.success) {
        window.location.href = '/dashboard';
      } else {
        errorMsg.text("⚠️ " + (res.message || "Error al iniciar sesión"))
                .removeClass('d-none')
                .fadeIn();
      }
    },
    error: function () {
      errorMsg.text("❌ Error en el servidor").removeClass('d-none').fadeIn();
    }
  });
});

// Manejo de registro
$('#formRegistro').on('submit', function (e) {
  e.preventDefault();
  $.ajax({
    url: "/admin/registro",   // o '/admin/registro' si tu blueprint tiene prefijo
    method: 'POST',
    contentType: 'application/json',
    data: JSON.stringify({
      nombre: $('input[name="nombre"]').val(),
      correo: $('input[name="correo"]').val(),
      contraseña: $('input[name="contraseña"]').val()
    }),
    success: function (res) {
      if (res.success) {
        window.location.href = '/dashboard';
      } else {
        errorMsg.text("⚠️ No se pudo registrar. " + (res.message || "Intenta de nuevo."))
                .removeClass('d-none')
                .fadeIn();
      }
    },
    error: function () {
      errorMsg.text("❌ Error en el servidor durante el registro")
              .removeClass('d-none')
              .fadeIn();
    }
  });
});

// Mostrar / ocultar secciones
$('#mostrarRegistro').on('click', function () {
  $('#login-section').addClass('hidden');
  $('#registro-section').removeClass('hidden');
});

$('#mostrarLogin').on('click', function () {
  $('#registro-section').addClass('hidden');
  $('#login-section').removeClass('hidden');
});
