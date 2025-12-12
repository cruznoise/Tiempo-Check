$(document).ready(function() {
  const loginSection = $('#login-section');
  const registroSection = $('#registro-section');
  const errorMsg = $('#error-msg');

  // === Manejo de Login ===
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
          if (typeof chrome !== 'undefined' && chrome.storage) {
            chrome.storage.local.set({ 
              usuario_id: res.usuario_id,
              sesion_activa: true,
              timestamp: Date.now()
            }, () => {
              console.log(' [AUTH] Sesión guardada en extensión');
              console.log('   Usuario ID:', res.usuario_id);
            });
          } else {
            console.log(' [AUTH] Chrome storage no disponible');
          }
          
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

  // ------------------------------------
  // MANEJO DEL REGISTRO (CON NUEVOS CAMPOS)
  // ------------------------------------
  $('#formRegistro').on('submit', function(e) {
    e.preventDefault();
    
    // Recolectar datos, incluyendo los nuevos campos de perfil
    const nombre = $('input[name="nombre"]').val();
    const correo = $('input[name="correo"]').val();
    const contraseña = $('input[name="contraseña"]').val();
    const dedicacion = $('select[name="dedicacion"]').val();
    const horario = $('select[name="horario"]').val();
    const dias_trabajo = $('select[name="dias_trabajo"]').val();
    
    // Validación para asegurar que se seleccionaron las opciones
    if (!dedicacion || !horario || !dias_trabajo) {
        errorMsg
            .text("⚠ Por favor, selecciona tu dedicación, horario y días de trabajo.")
            .removeClass("d-none")
            .fadeIn();
        return;
    }

    $.ajax({
      url: "/admin/registro",
      method: "POST",
      contentType: "application/json",
      data: JSON.stringify({
        nombre: $('input[name="nombre_reg"]').val(),
        correo: $('input[name="correo_reg"]').val(), 
        contrasena: $('input[name="contraseña_reg"]').val(), 
        dedicacion: $('input[name="dedicacion"]').val(),
        horario: $('input[name="horario"]').val(),
        dias_trabajo: $('input[name="dias_trabajo"]').val()
      }),
      success: function(res) {
        if (res.success) {
          if (typeof chrome !== 'undefined' && chrome.storage && res.usuario_id) {
            chrome.storage.local.set({ 
              usuario_id: res.usuario_id,
              sesion_activa: true,
              timestamp: Date.now()
            }, () => {
              console.log(' [AUTH] Sesión guardada en extensión (registro)');
            });
          }
          
          window.location.href = "/dashboard";
        } else {
          errorMsgRegistro
            .text(" No se pudo registrar. " + (res.message || "Intenta de nuevo."))
            .removeClass("d-none")
            .fadeIn();
        }
      },
      error: function() {
        errorMsgRegistro
          .text(" Error en el servidor durante el registro")
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