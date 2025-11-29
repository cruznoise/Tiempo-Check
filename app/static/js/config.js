    // Funciones para manejar modales
    function openEditModal(tipo) {
      document.getElementById('modal-' + tipo).style.display = 'flex';
    }

    function closeModal(tipo) {
      document.getElementById('modal-' + tipo).style.display = 'none';
    }

    function openResetModal() {
      document.getElementById('modal-reset').style.display = 'flex';
    }

    function openDeleteModal() {
      document.getElementById('modal-delete').style.display = 'flex';
    }

    // Cerrar modal al hacer clic fuera
    window.onclick = function(event) {
      if (event.target.classList.contains('modal-overlay')) {
        event.target.style.display = 'none';
      }
    }

    // Funciones para enviar formularios
    function submitFormNombre(event) {
      event.preventDefault();
      const nombre = document.getElementById('input-nombre').value;
      
      fetch('/admin/actualizar-nombre', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ nuevo_nombre: nombre })
      })
      .then(response => response.json())
      .then(data => {
        if (data.success) {
          document.getElementById('display-nombre').textContent = nombre;
          closeModal('nombre');
          showAlert('success', 'Nombre actualizado correctamente');
          // Actualizar el sidebar
          document.querySelector('.sidebar h2').textContent = '¡Hola, ' + nombre + '!';
        } else {
          showAlert('error', data.message || 'Error al actualizar el nombre');
        }
      })
      .catch(error => {
        showAlert('error', 'Error de conexión');
      });
      
      return false;
    }

    function submitFormCorreo(event) {
      event.preventDefault();
      const correo = document.getElementById('input-correo').value;
      const password = document.getElementById('input-password-correo').value;
      
      fetch('/admin/actualizar-correo', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          nuevo_correo: correo,
          password: password 
        })
      })
      .then(response => response.json())
      .then(data => {
        if (data.success) {
          location.reload();
        } else {
          showAlert('error', data.message || 'Error al actualizar el correo');
        }
      })
      .catch(error => {
        showAlert('error', 'Error de conexión');
      });
      
      return false;
    }

    function submitFormPassword(event) {
      event.preventDefault();
      const passwordActual = document.getElementById('input-password-actual').value;
      const passwordNueva = document.getElementById('input-password-nueva').value;
      const passwordConfirmar = document.getElementById('input-password-confirmar').value;
      
      if (passwordNueva !== passwordConfirmar) {
        showAlert('error', 'Las contraseñas no coinciden');
        return false;
      }
      
      fetch('/admin/cambiar-password', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          password_actual: passwordActual,
          password_nueva: passwordNueva 
        })
      })
      .then(response => response.json())
      .then(data => {
        if (data.success) {
          closeModal('password');
          showAlert('success', 'Contraseña actualizada correctamente');
          document.getElementById('form-password').reset();
        } else {
          showAlert('error', data.message || 'Error al cambiar la contraseña');
        }
      })
      .catch(error => {
        showAlert('error', 'Error de conexión');
      });
      
      return false;
    }

    function submitFormReset(event) {
      event.preventDefault();
      const confirmacion = document.getElementById('input-confirm-reset').value;
      const password = document.getElementById('input-password-reset').value;
      
      if (confirmacion !== 'RESETEAR') {
        showAlert('error', 'Debes escribir "RESETEAR" para confirmar');
        return false;
      }
      
      if (!confirm('¿Estás completamente seguro? Esta acción no se puede deshacer.')) {
        return false;
      }
      
      fetch('/admin/resetear-cuenta', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ password: password })
      })
      .then(response => response.json())
      .then(data => {
        if (data.success) {
          showAlert('success', 'Cuenta reseteada correctamente. Redirigiendo...');
          setTimeout(() => {
            window.location.href = '/dashboard';
          }, 2000);
        } else {
          showAlert('error', data.message || 'Error al resetear la cuenta');
        }
      })
      .catch(error => {
        showAlert('error', 'Error de conexión');
      });
      
      return false;
    }

    function submitFormDelete(event) {
      event.preventDefault();
      const confirmacion = document.getElementById('input-confirm-delete').value;
      const password = document.getElementById('input-password-delete').value;
      
      if (confirmacion !== 'ELIMINAR') {
        showAlert('error', 'Debes escribir "ELIMINAR" para confirmar');
        return false;
      }
      
      if (!confirm('ÚLTIMA ADVERTENCIA: Tu cuenta será eliminada permanentemente. ¿Continuar?')) {
        return false;
      }
      
      fetch('/admin/eliminar-cuenta', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ password: password })
      })
      .then(response => response.json())
      .then(data => {
        if (data.success) {
          showAlert('success', 'Cuenta eliminada. Redirigiendo...');
          setTimeout(() => {
            window.location.href = '/logout';
          }, 2000);
        } else {
          showAlert('error', data.message || 'Error al eliminar la cuenta');
        }
      })
      .catch(error => {
        showAlert('error', 'Error de conexión');
      });
      
      return false;
    }

    function showAlert(type, message) {
      const alertElement = document.getElementById('alert-' + type);
      alertElement.textContent = message;
      alertElement.style.display = 'block';
      
      setTimeout(() => {
        alertElement.style.display = 'none';
      }, 5000);
    }