
$(document).ready(function(){
    $.post('/api/tiempo', function(datos){
        datos.forEach(d => {
            $('#tabla-tiempo tbody').append(`<tr><td>${d.dominio}</td><td>${d.tiempo}</td><td>${d.fecha}</td></tr>`);
        });
    });
});
