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

// Ventana independiente: cancelar conserva los cambios del cuadro diario.
(() => {
    const dialog = document.getElementById('marcacion-manual-dialog');
    const open = document.getElementById('abrir-marcacion-manual');
    if (!dialog || !open) return;
    open.addEventListener('click', () => {
        if (!dialog.open) dialog.showModal();
    });
    dialog.querySelectorAll('[data-cerrar-manual]').forEach(button => {
        button.addEventListener('click', () => dialog.close());
    });
    dialog.addEventListener('close', () => open.focus());
})();
