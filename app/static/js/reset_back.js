// Descarga JSON y CSV

    document.getElementById("exportarCSV").addEventListener("click", () => {
      const rango = document.getElementById("rango").value;
      window.location.href = `/admin/exportar/datos?formato=csv&rango=${rango}`;
    });

    document.getElementById("exportarJSON").addEventListener("click", async () => {
  const rango = document.getElementById("rango").value;

  try {
    const response = await fetch(`/admin/exportar/datos?formato=json&rango=${rango}`);
    const json = await response.json();

    if (!json.datos || json.datos.length === 0) {
      alert(" No hay datos para exportar en ese rango.");
      return;
    }

    const blob = new Blob([JSON.stringify(json, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `registro_${rango}_${new Date().toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);

    alert("Archivo JSON descargado correctamente");

  } catch (error) {
    console.error("Error al exportar JSON:", error);
    alert(" Error al descargar el archivo JSON");
  }
});


// Descarga JSON para respaldo

document.getElementById('bck_btn').addEventListener('click', () => {
  fetch('/admin/backup_completo')  // ← Cambia aquí, agrega /admin
    .then(res => res.blob())
    .then(blob => {
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'backup_completo.json';
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    })
    .catch(err => {
      alert("Error al descargar el backup completo.");
      console.error(err);
    });
});

// Subir archivo JSON para backup
document.getElementById('form-restaurar').addEventListener('submit', function(e) {
  e.preventDefault();
  const archivo = document.getElementById('archivo-backup').files[0];
  
  if (!archivo) {
    return alert("⚠️ Selecciona un archivo JSON válido");
  }
  
  if (!archivo.name.endsWith('.json')) {
    return alert("⚠️ El archivo debe ser un JSON (.json)");
  }

  // Mostrar que está procesando
  const btnSubmit = e.target.querySelector('button[type="submit"]');
  const textoOriginal = btnSubmit.textContent;
  btnSubmit.disabled = true;
  btnSubmit.textContent = '⏳ Restaurando...';

  const formData = new FormData();
  formData.append('backup', archivo);

  fetch('/admin/restaurar_backup', {
    method: 'POST',
    body: formData
  })
  .then(res => res.json())
  .then(data => {
    if (data.success) {
      alert("✅ " + (data.mensaje || "Backup restaurado correctamente"));
      location.reload(); // Recargar para ver los datos restaurados
    } else {
      alert("❌ " + (data.error || "Error al restaurar el backup"));
    }
  })
  .catch(err => {
    console.error("Error al restaurar:", err);
    alert("❌ Ocurrió un error al restaurar el backup.");
  })
  .finally(() => {
    // Restaurar el botón
    btnSubmit.disabled = false;
    btnSubmit.textContent = textoOriginal;
  });
});
///Reseteo de la cuenta
document.getElementById('btn-reseteo-total').addEventListener('click', function() {
  if (!confirm("¿Estás seguro de que deseas borrar todos tus datos? Esta acción no se puede deshacer.")) {
    return;
  }

  fetch('/admin/reseteo_total', {  // ← Cambia aquí también
    method: 'POST'
  })
  .then(res => res.json())
  .then(data => {
    alert(data.mensaje || "Cuenta reiniciada.");
    location.reload();
  })
  .catch(err => {
    console.error("Error al resetear cuenta:", err);
    alert("❌ Error al reiniciar la cuenta.");
  });
});