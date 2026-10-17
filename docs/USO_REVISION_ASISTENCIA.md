# Consulta y revisión de asistencia

En el menú **Asistencia & HH.EE.**, seleccione las fechas inicial y final. Puede filtrar por sede, trabajador, estado de asistencia y revisión. El periodo puede abarcar dos meses. La tabla muestra 30 jornadas por página; el resumen y la exportación consideran todos los resultados filtrados.

## Administración

1. Abra **Ver detalle** para comprobar marcaciones, origen, intervalos de trabajo y refrigerio.
2. Asigne un turno a la jornada cuando corresponda. La asignación no modifica el turno habitual del trabajador.
3. Si el equipo reportó un tipo de evento equivocado, registre su corrección con motivo. El evento original se conserva.
4. Registre incidencias y propuestas de ajuste. Quedan pendientes de aprobación y no alteran los totales mientras no se aprueben.
5. Use **Marcar como observado** para solicitar revisión. Consulte el historial para conocer responsables y fechas.
6. En la bandeja de pendientes puede asociar marcas sin identidad. La asociación no cambia el identificador original. Registre una jornada sin horas si necesita documentar un día que no tenga resumen, por ejemplo vacaciones.

## Contabilidad y Gerencia

1. Revise los tramos y compare los tiempos reconstruidos con los valores guardados.
2. Compruebe y apruebe las incidencias y ajustes. Aprobarlos no aprueba automáticamente la jornada.
3. Apruebe la jornada cuando se hayan resuelto los bloqueos. Las jornadas con vacaciones o permisos sin marcas requieren la incidencia correspondiente de día completo aprobada.
4. Consulte el resumen por trabajador. Las horas se expresan en decimales: 2,50 h equivale a 2 h 30 min. El refrigerio se muestra en HH:MM:SS.
5. Exporte el resumen como CSV, compatible con Excel. Incluye recuentos de aprobadas, pendientes y observadas; no se presenta como un cierre aprobado cuando quedan pendientes.
6. Para cerrar un periodo pasado, revise todas sus jornadas, quite las incidencias pendientes y confirme el cierre. El cierre siempre abarca todas las sedes y trabajadores entre las fechas elegidas, independientemente de los demás filtros. Guarda los resultados y bloquea cambios desde los flujos del sistema.

Administración puede proponer y observar. Contabilidad y Gerencia pueden aprobar y cerrar. Los superusuarios conservan facultades de aprobación. Los demás roles solo consultan su propia asistencia.

## Interpretación de los resultados

- Los ajustes aprobados se suman al concepto elegido sin sobrescribir la cifra original.
- Descuentos y compensaciones se muestran aparte. No calculan dinero ni restan automáticamente de otro concepto.
- No sume nocturnidad y extras como tiempos independientes: pueden coincidir.
- Tiempo pendiente compara el turno programado con el trabajo reconstruido; no genera un descuento automático.
- El cambio de marcas, incidencias, ajustes o datos de una jornada aprobada exige una nueva revisión.
- Los bloques nocturnos usan fecha y hora completas. Cuando la salida se infiere al día siguiente por sus horas guardadas, se muestra un aviso para confirmarlo.
- Se muestran avisos cuando hay fechas futuras en los registros existentes. Esos datos no se borran ni se corrigen automáticamente.

## Huellero e importación

Abrir el dashboard solo consulta registros guardados. Ya no genera marcaciones simuladas. **Consultar conexión del equipo** comprueba conectividad de red; el cliente existente todavía no implementa la descarga física de registros y la pantalla lo indica. La marca web se identifica como Kiosko/DNI, sin atribuirle biometría o coordenadas ficticias.

El importador utiliza la sesión del usuario actual. La adaptación completa al libro mixto de 51 hojas sigue pendiente: estos cambios incorporan consulta y revisión, no reemplazan el algoritmo de importación. Revise sus resultados antes de aprobarlos. No se ha vuelto a importar el Excel de agosto como parte de esta implementación.

## Validación y datos

La actualización añade tablas de incidencias, ajustes, correcciones, historial y cierres, y campos de revisión al resumen diario. Se conserva el indicador de verificación anterior. La base local se respaldó antes de aplicar las migraciones; no se eliminaron jornadas ni marcaciones existentes.

Pasaron 24 pruebas automatizadas de permisos, filtros, plantillas, tramos, medianoche, revisión, ajustes, incidencias, exportación y cierre. Las pruebas crean una base separada. La renderización con registros existentes se comprobó desde Django. El navegador integrado confirmó que el servidor responde y solicita inicio de sesión; la comprobación visual del panel protegido queda pendiente. El primer intento con el servidor temporal de vista previa agotó el tiempo de espera.
