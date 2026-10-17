(() => {
    'use strict';
    const ventana = document.getElementById('detalle-jornada-dialog') || document.getElementById('revision-trabajador-dialog');
    if (!ventana) return;
    ventana.addEventListener('close', () => window.location.assign(ventana.dataset.volver));
    ventana.showModal();
    if (window.location.hash === '#detalle-jornada') {
        ventana.querySelector('#detalle-jornada')?.scrollIntoView({block: 'start'});
    }
})();
