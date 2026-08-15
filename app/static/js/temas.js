// temas.js

document.addEventListener("DOMContentLoaded", () => {
  const temaSelect = document.getElementById('selector-tema');
  // Se usa el ID del HTML N
  const modoToggle = document.getElementById('modoNocheToggle'); 
  const guardado = localStorage.getItem("tema_usuario");

  if (guardado) {
    const [temaClass, modoClass] = guardado.split(" ");

    document.body.classList.forEach(cls => {
      if (cls.startsWith("theme-") || cls === "day" || cls === "night") {
        document.body.classList.remove(cls);
      }
    });

    document.body.classList.add(temaClass, modoClass);

    if (temaSelect) temaSelect.value = temaClass.replace("theme-", "");
    if (modoToggle) modoToggle.checked = modoClass === "night";
  }

  if (temaSelect && modoToggle) {
    function aplicarTema() {
      const tema = temaSelect.value;
      const modo = modoToggle.checked ? 'night' : 'day';
      const nuevaClase = `theme-${tema} ${modo}`;

      document.body.classList.forEach(cls => {
        if (cls.startsWith("theme-") || cls === "day" || cls === "night") {
          document.body.classList.remove(cls);
        }
      });

      nuevaClase.split(" ").forEach(cls => {
        document.body.classList.add(cls);
      });

      localStorage.setItem("tema_usuario", nuevaClase);
      console.log("🎨 Tema guardado y aplicado:", nuevaClase);
      
      // Disparar evento para que Chart.js se actualice (Mejora clave)
      const event = new CustomEvent('temaCambiado');
      document.body.dispatchEvent(event);
    }

    // Registrar la función globalmente para uso externo (como botones)
    window.aplicarTema = aplicarTema;

    temaSelect.addEventListener("change", aplicarTema);
    modoToggle.addEventListener("change", aplicarTema);
  }
});