(() => {
    'use strict';
    const detalle = document.getElementById('detalle-jornada');
    const manual = detalle?.querySelector('.formulario-marcacion-manual');
    const clasificacion = detalle?.querySelector('.correcciones-cuadro-excel');
    if (!manual || !clasificacion) return;
    manual.addEventListener('submit', () => {
        manual.querySelectorAll('[data-evento-copiado]').forEach(campo => campo.remove());
        for (const [nombre, valor] of new FormData(clasificacion)) {
            if (!/^(evento|original)_\d+$/.test(nombre)) continue;
            const campo = document.createElement('input');
            campo.type = 'hidden'; campo.name = nombre; campo.value = valor;
            campo.dataset.eventoCopiado = 'true';
            manual.appendChild(campo);
        }
    });
})();
