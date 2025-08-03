fetch('/admin/api/logros')
    .then(res => {
      if (!res.ok) throw new Error("Respuesta no válida");
      return res.json();
    })

    .then(data => {
      const contenedor = document.getElementById('contenedor-logros');
      console.log(" Logros recibidos:", data); 
      data.forEach(logro => {
        const div = document.createElement('div');
        div.className = `insignia ${logro.nivel} ${logro.desbloqueado ? '' : 'locked'}`;
        div.innerHTML = `
          <img src="${logro.imagen_url}" alt="${logro.nombre}">
          <h3>${logro.nombre}</h3>
          <p>${logro.descripcion}</p>
        `;

        contenedor.appendChild(div);
      });
    })
    .catch(err => console.error(" Error al cargar logros:", err));

document.addEventListener("DOMContentLoaded", function () {
    const contenedor = document.getElementById("contenedor-sugerencias");
    const usuarioId = contenedor.dataset.usuario;

    fetch("/admin/api/sugerencias")
        .then(response => response.json())
        .then(data => {
            // Vaciar contenedor antes de renderizar
            contenedor.innerHTML = '';

            // Caso: backend devuelve un objeto con mensaje (insuficiente)
            if (!Array.isArray(data)) {
                document.getElementById("sugerenciasMetas").style.display = "block";
                contenedor.innerHTML = `
                    <div class="tile-card alerta-info">
                        <p>${data.mensaje || 'Aún no hay sugerencias disponibles.'}</p>
                    </div>
                `;
                return;
            }

            // Caso: array vacío
            if (data.length === 0) {
                document.getElementById("sugerenciasMetas").style.display = "none";
                return;
            }

            const categoriasProductivas = ["Productividad", "Estudio", "Trabajo", "Herramientas"];

            data.forEach(sug => {
                const tarjeta = document.createElement("div");
                tarjeta.classList.add("tile-card");

                // Color para nivel de confianza
                let colorConfianza = 'gray';
                if (sug.nivel_confianza === 'baja') colorConfianza = 'red';
                if (sug.nivel_confianza === 'media') colorConfianza = 'orange';
                if (sug.nivel_confianza === 'alta') colorConfianza = 'green';

                const esProductiva = categoriasProductivas.includes(sug.categoria_nombre);

                // Render condicional: solo meta en productivas, solo límite en no productivas
                tarjeta.innerHTML = `
                    <h3>${sug.categoria_nombre}</h3>
                    ${ esProductiva
                        ? `<p>Meta sugerida: <strong>${sug.sugerencia_meta} minutos</strong></p>`
                        : `<p>Límite sugerido: <strong>${sug.sugerencia_limite} minutos</strong></p>` }
                    <p>Confianza: <span style="color:${colorConfianza}; font-weight:bold;">
                        ${sug.nivel_confianza.toUpperCase()}
                    </span></p>
                    <button class="btn-aplicar-sugerencia" 
                            data-categoria="${sug.categoria_id}" 
                            data-meta="${sug.sugerencia_meta}"
                            data-limite="${sug.sugerencia_limite}"
                            ${sug.nivel_confianza === 'insuficiente' ? 'disabled' : ''}>
                        Aplicar sugerencia
                    </button>
                `;

                contenedor.appendChild(tarjeta);
            });

            // Eventos para aplicar sugerencias (meta o límite según categoría)
            document.querySelectorAll(".btn-aplicar-sugerencia").forEach(btn => {
                btn.addEventListener("click", async function () {
                    const categoriaId = this.dataset.categoria;
                    const meta = this.dataset.meta;
                    const limite = this.dataset.limite;
                    const nombre = this.parentElement.querySelector("h3").textContent;

                    const categoriasProductivas = ["Productividad", "Estudio", "Trabajo", "Herramientas"];
                    const esProductiva = categoriasProductivas.includes(nombre);

                    let endpoint = esProductiva 
                        ? "/admin/api/agregar_meta" 
                        : "/admin/api/agregar_limite";

                    let body = esProductiva 
                        ? `usuario_id=${usuarioId}&categoria_id=${categoriaId}&meta_minutos=${meta}`
                        : `usuario_id=${usuarioId}&categoria_id=${categoriaId}&limite_minutos=${limite}`;

                    try {
                        const res = await fetch(endpoint, {
                            method: "POST",
                            headers: { "Content-Type": "application/x-www-form-urlencoded" },
                            body: body
                        });

                        if (res.ok) {
                            location.reload();
                        } else {
                            alert("Error al aplicar sugerencia.");
                        }
                    } catch (err) {
                        console.error("Error al aplicar sugerencia:", err);
                        alert("Hubo un error al aplicar la sugerencia.");
                    }
                });
            });
        })
        .catch(err => {
            console.error("Error al cargar sugerencias:", err);
        });
});

