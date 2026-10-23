# Revisión de horarios y tardanzas de agosto de 2026

Fecha de revisión: 22/10/2026. Consulta de solo lectura. No se modificaron turnos, marcaciones, cálculos ni aprobaciones.


## Resultado
El sistema tiene tres turnos configurados, pero no cubren la rotación que muestran los registros. Abisag tiene aplicado el turno administrativo de Chiclayo de 08:00 a 18:00 en las 31 fechas de agosto. El 01/08 ingresó a las 14:02:51 en Cajamarca. Comparar ese ingreso con las 08:00 produce 362 minutos completos. El sistema almacena once jornadas de Abisag con más de tres horas de tardanza. Esto no acredita once llegadas tarde: exige confirmar el turno programado de cada fecha.
Se revisaron 43 hojas individuales del Excel contable, las seis hojas de la exportación ZKTeco (4.287 marcaciones, 60 identidades por sede/equipo/código vinculadas a 50 fichas) y las 58 fichas actuales del sistema. Ocho fichas no tienen identidad presente en este archivo. Las 43 hojas contables no equivalen a las 50 fichas: hay trabajadores sin hoja individual y diferencias de nombre que requieren conciliación.
Las 991 jornadas guardadas de agosto se distribuyen en 31 con turno administrativo aplicado y 960 sin turno efectivo. Ninguna de las 58 fichas obtiene un turno por su usuario vinculado. Esto describe la configuración, no implica que todas esas fechas sean laboradas. Solo 23 jornadas de agosto reconstruyen actualmente una secuencia completa de eventos. Los valores cero del resto no demuestran puntualidad.

## Turnos configurados en el sistema

| Turno | Entrada | Salida | Tolerancia (min) | Refrigerio |
|---|---|---|---:|---|
| Administrativo Chiclayo | 08:00:00 | 18:00:00 | 15 | 13:00:00 a 14:00:00 |
| Boletería Turno Mañana | 06:00:00 | 14:30:00 | 10 | Sin definir a sin definir |
| Ruta Interprovincial (Conductores) | 07:00:00 | 21:00:00 | 30 | Sin definir a sin definir |

## Qué horarios muestra el Excel
No se encontró un catálogo de horarios oficiales de entrada y salida. Las horas registradas permiten observar patrones, pero no prueban el horario pactado ni su tolerancia. Hay ingresos en madrugada, mañana, tarde y noche, y cambios de franja dentro del mismo trabajador.

| Patrón observado | Ejemplos en las hojas | Qué confirmar |
|---|---|---|
| Madrugada, alrededor de 03:30–04:00 | Emir Monteza, Silvio, Carlos Arteaga y Manuel Mosqueira | Hora programada, duración y rotaciones |
| Mañana, alrededor de 06:00 | Abisag, Midori, Celeste, Pasapera, Quiliche, Luz Marina, Grecia | Entrada, salida, refrigerio y alternancia con tarde |
| Administrativo, alrededor de 08:00–09:30 | Pedro Chavesta, Roberto Rivera, Jorge Aguilar, Angie, Carlos Plaza, Diana, Diego, Yaneli | Diferencias por día y medias jornadas |
| Intermedio, alrededor de 10:00 | Mariasol Sánchez y registros aislados de otros | Si es turno regular, cambio autorizado o llegada tardía |
| Tarde, alrededor de 14:00 | Abisag, Mendo, Nancy y varias personas que rotan | Hora oficial de salida y refrigerio |
| Noche, alrededor de 20:00 | Alejandro Arteaga e Israel Roque | Salida al día siguiente, refrigerio y fecha de inicio |
| Noche, alrededor de 22:00 | Rivera | Salida al día siguiente y cambios de jornada |

Estos son siete grupos descriptivos para organizar la revisión, no siete turnos oficiales confirmados. Un grupo puede requerir varios horarios.

## Caso Abisag
La hoja ABISAG contiene 25 bloques contables desde el 30/07 al 27/08. Doce inician cerca de las 06:00 y trece cerca de las 14:00. En agosto son doce de mañana y once de tarde. La hoja indica descanso los martes (C2). Los registros sugieren alternancia semanal, que debe validarse con la programación de la empresa.
El 01/08 (D14:D17) tiene 14:02:51, 17:23:28, 18:15:04 y 23:11:38. Los tramos laborales suman 08:17:11 y el refrigerio 00:51:36. La tardanza es independiente de esas ocho horas trabajadas. Si la empresa confirma entrada a las 14:00, el desfase bruto sería 2 min 51 s; con una tolerancia de diez minutos no correspondería tardanza según la regla actual del sistema. Es un escenario, no una reasignación realizada.

| Fecha | Tardanza guardada (min) | Turno aplicado |
|---|---:|---|
| 2026-08-01 | 362 | Administrativo Chiclayo (08:00 - 18:00) |
| 2026-08-02 | 363 | Administrativo Chiclayo (08:00 - 18:00) |
| 2026-08-10 | 362 | Administrativo Chiclayo (08:00 - 18:00) |
| 2026-08-12 | 361 | Administrativo Chiclayo (08:00 - 18:00) |
| 2026-08-13 | 364 | Administrativo Chiclayo (08:00 - 18:00) |
| 2026-08-14 | 359 | Administrativo Chiclayo (08:00 - 18:00) |
| 2026-08-15 | 360 | Administrativo Chiclayo (08:00 - 18:00) |
| 2026-08-16 | 359 | Administrativo Chiclayo (08:00 - 18:00) |
| 2026-08-24 | 360 | Administrativo Chiclayo (08:00 - 18:00) |
| 2026-08-26 | 359 | Administrativo Chiclayo (08:00 - 18:00) |
| 2026-08-27 | 358 | Administrativo Chiclayo (08:00 - 18:00) |

## Revisión de las 43 hojas individuales
Cada número entre paréntesis cuenta bloques contables que empiezan en esa hora: 05 h abarca 05:00:00–05:59:59. No representa la hora contractual. Los bloques se delimitan por la fórmula de saldo de la hoja; pueden tener marcas faltantes, horas sustituidas o agrupaciones incorrectas. Por eso no se usan para asignar automáticamente turnos. El período incluye finales de julio y llega al 28/08.

| Hoja | Bloques | Hora observada de inicio y cantidad | Bases de duración escritas | Descanso indicado al inicio |
|---|---:|---|---|---|
| ALEJANDRO ARTEAGA | 25 | 19 h (21), 20 h (3), 21 h (1) | 08:45:00 (2), 08:00:00 (23) | DESCANSO SABADOS |
| BRUNELLA HUAMAN | 24 | 06 h (7), 13 h (4), 14 h (13) | 08:00:00 (24) | DESCANSO VIERNES |
| CARLOS ARTEAGA | 25 | 03 h (13), 04 h (2), 13 h (10) | 08:00:00 (25) | DESCANSO LUNES |
| DAYANA RAMOS | 26 | 05 h (5), 06 h (5), 13 h (9), 14 h (7) | 08:00:00 (26) | DESCANSO VIERNES |
| ELIZABETH BRIONES | 25 | 05 h (7), 06 h (9), 13 h (8), 14 h (1) | 08:00:00 (25) | DESCANSO MARTES |
| EMIR MONTEZA | 25 | 03 h (25) | 08:00:00 (25) | DESCANSO SABADOS |
| JHON DAVILA | 12 | 06 h (6), 14 h (6) | 08:00:00 (12) | DESCANSO MIERCOLES |
| JULIO CHUNG | 24 | 13 h (21), 14 h (2), 17 h (1) | 08:00:00 (24) | DESCANSO MIERCOLES |
| ISRAEL ROQUE | 25 | 13 h (2), 20 h (23) | 08:00:00 (2), 08:45:00 (23) | DESCANSO MARTES |
| LILIAN VASQUEZ | 23 | 06 h (9), 13 h (4), 14 h (10) | 08:00:00 (21), 00:00:00 (1), 08:45:00 (1) | DESCANSO DOMINGOS |
| LILIANA HURTADO | 24 | 05 h (6), 06 h (7), 13 h (3), 14 h (8) | 08:00:00 (24) | DESCANSO SABADOS |
| MARIASOL SANCHEZ | 23 | 06 h (8), 07 h (1), 09 h (1), 10 h (8), 11 h (1), 14 h (4) | 08:00:00 (23) | DESCANSO MIERCOLES; 30 DESCANSO |
| MERLY MORENO | 24 | 06 h (13), 10 h (1), 14 h (10) | 08:00:00 (24) | DESCANSO LUNES; 30 DESCANSO |
| FELIX ALLENDE | 25 | 00 h (4), 04 h (4), 06 h (1), 07 h (3), 13 h (1), 14 h (7), 18 h (1), 20 h (4) | 08:45:00 (9), 08:00:00 (15), Sin base escrita (1) | DESCANSO JUEVES; 30 DESCANSO |
| HEMELY YAMUNAQUE | 12 | 05 h (11), 06 h (1) | 08:00:00 (12) | DESCANSO DOMINGOS |
| ANGIE SANCHEZ | 24 | 09 h (23), 12 h (1) | 08:30:00 (18), 09:30:00 (3), 04:30:00 (3) | DESCANSO DOMINGO |
| CARLOS PLAZA | 21 | 06 h (1), 08 h (2), 09 h (17), 10 h (1) | 09:30:00 (10), 04:30:00 (4), 08:30:00 (7) | DESCANSO DOMINGO |
| DIANA CHOQUEHUANCA | 23 | 08 h (2), 09 h (21) | 09:30:00 (16), 04:30:00 (3), 08:30:00 (4) | DESCANSO DOMINGO |
| DIEGO VELIZ | 24 | 08 h (6), 09 h (16), 10 h (1), 14 h (1) | 08:30:00 (10), 09:30:00 (10), 04:30:00 (4) | DESCANSO DOMINGO |
| TERRONES YANELI | 24 | 09 h (23), 12 h (1) | 09:30:00 (11), 04:30:00 (5), 08:30:00 (8) | DESCANSO DOMINGO |
| SEGUNDO AGAPITO | 28 | 00 h (1), 08 h (22), 09 h (4), 10 h (1) | 08:00:00 (25), Sin base escrita (3) | DESCANSO DOMINGO |
| ROBERTO RIVERA | 25 | 07 h (9), 08 h (16) | 08:00:00 (22), Sin base escrita (2), 10:00:00 (1) | DESCANSO DOMINGO |
| MANUEL MOSQUEIRA | 25 | 04 h (11), 09 h (2), 13 h (1), 14 h (11) | 08:00:00 (25) | Sin indicación en primeras tres filas |
| PEDRO CHAVESTA | 24 | 08 h (24) | 08:00:00 (24) | Sin indicación en primeras tres filas |
| JUAN ZAPATA | 1 | 06 h (1) | 08:00:00 (1) | DESCANSO VIERNES |
| JORGE AGUILAR | 16 | 08 h (11), 09 h (5) | 08:00:00 (16) | DESCANSA MARTES MIERCOLES Y JUEVES |
| NANCY FLORES | 22 | 13 h (1), 14 h (21) | 08:00:00 (22) | DESCANSO DOMINGO |
| MIDORI | 24 | 05 h (8), 06 h (5), 13 h (5), 14 h (6) | 08:00:00 (24) | LUNES DESCANSA |
| CELESTE | 24 | 05 h (1), 06 h (10), 07 h (1), 13 h (2), 14 h (10) | 08:00:00 (24) | DOMINGO DESCANSA |
| RIVERA | 26 | 00 h (2), 14 h (2), 16 h (1), 21 h (15), 22 h (6) | 08:00:00 (26) | LUNES DESCANSA |
| PASAPERA | 25 | 05 h (6), 06 h (4), 13 h (10), 14 h (5) | 08:00:00 (25) | SÁBADO DESCANSA |
| MENDO | 25 | 14 h (25) | 08:00:00 (22), 08:45:00 (3) | VIERNES DESCANSA |
| QUILICHE | 25 | 05 h (7), 06 h (5), 13 h (12), 14 h (1) | 08:00:00 (25) | MIERCOLES DESCANSA |
| ABISAG | 25 | 05 h (3), 06 h (9), 13 h (5), 14 h (8) | 08:00:00 (25) | MARTES DESCANSA |
| LUZ MARINA | 25 | 05 h (3), 06 h (10), 13 h (9), 14 h (3) | 08:00:00 (25) | MIERCOLES DESCANSA |
| EMERITO | 25 | 00 h (3), 05 h (9), 06 h (4), 13 h (7), 14 h (2) | 08:00:00 (22), 08:45:00 (3) | SÁBADO DESCANSA |
| ANGULO | 1 | 14 h (1) | 08:00:00 (1) | MARTES DESCANSA |
| ROJAS ALAN | 24 | 03 h (5), 05 h (8), 06 h (1), 13 h (8), 14 h (2) | 08:00:00 (23), Sin base escrita (1) | JUEVES DESCANSA |
| SILVIO | 23 | 03 h (23) | Sin base escrita (23) | MIERCOLES DESCANSA |
| TERÁN | 24 | 05 h (12), 06 h (1), 13 h (11) | 08:00:00 (24) | MARTES DESCANSA |
| GRECIA | 25 | 06 h (13), 14 h (12) | 08:00:00 (25) | DESCANSO MIERCOLES |
| JUANITA | 12 | 06 h (4), 14 h (8) | Sin base escrita (12) | Sin indicación en primeras tres filas |
| EVELYN | 7 | 06 h (4), 14 h (3) | 08:00:00 (7) | DESCANSO JUEVES |

## Diferencias de base y calidad de datos
Se localizaron siete valores de duración base escritos en las filas de saldo: 00:00, 04:30, 08:00, 08:30, 08:45, 09:30 y 10:00. Son valores usados por las fórmulas contables, no siete horarios de ingreso. Hay 42 bloques sin base escrita. El valor cero de Lilian y el valor 10:00 de Roberto son excepciones para revisar, no turnos que deban crearse.
Angie, Carlos Plaza, Diana, Diego y Yaneli usan bases de 04:30, 08:30 y 09:30 según la fecha. Alejandro, Israel, Félix, Mendo y Emérito presentan también 08:45. Esto difiere de la base fija de 08:00 solicitada para el sistema. Debe decidirse si se mantiene esa regla o si la empresa confirma bases distintas. La auditoría no cambia la base vigente.
Hay agrupaciones contables que abarcan más de 24 horas; deben revisarse antes de interpretar un inicio como entrada. Ejemplos y localizadores:

| Hoja | Inicio | Fin | Celdas |
|---|---|---|---|
| CARLOS PLAZA | 2026-08-12 09:58:50 | 2026-08-13 19:01:06 | D30:D33 |
| JUAN ZAPATA | 2026-07-30 06:45:15 | 2026-07-31 06:45:37 | D5:D9 |
| RIVERA | 2026-08-16 00:00:00 | 2026-08-17 07:00:38 | D73:D80 |
| RIVERA | 2026-08-21 00:00:00 | 2026-08-22 07:02:07 | D97:D104 |

También hay diferencias de nombres: ANGIE SANCHEZ usa código 73581427, que en la exportación figura como Angie Pozo; el mismo código 16659599 aparece con Félix/Fernando, y 16788665 con Israel/Roque Vega. Las identidades se contrastaron por sede, equipo y código, sin fusionar personas por parecido del nombre. El equipo ocupa una columna diferente en Cajamarca respecto de las otras cinco hojas; se leyó por encabezado.

## Cobertura de las 58 fichas del sistema
Las cantidades de jornadas son solo de agosto de 2026. «Sin turno» incluye días no laborados y fechas pendientes de clasificar. «Marcaciones fuente» cuenta el archivo ZKTeco, cuyo intervalo es 27/07–28/08. Las fichas sin evidencia no permiten evaluar puntualidad con este archivo.

| Ficha actual | Sede | Código(s) | Marcaciones fuente | Jornadas agosto | Sin turno efectivo | Tardanzas >180 min |
|---|---|---|---:|---:|---:|---:|
| ABISAG SALAZAR | CAJAMARCA | 42 | 107 | 31 | 0 | 11 |
| ALEJANDRO ARTEAGA | CHICLAYO | 16621836 | 103 | 28 | 28 | 0 |
| ANGULO DIAZ | CAJAMARCA | 39 | 19 | 0 | 0 | 0 |
| Ana María Torres Ríos | Chiclayo - Ventanilla 01 | Sin código importado | Sin identidad en archivo | 0 | 0 | 0 |
| Angie Pozo | CHICLAYO | 73581427 | 91 | 23 | 23 | 0 |
| Blanca Pelaez | CHICLAYO | 16498340 | 33 | 19 | 19 | 0 |
| Brunella Huaman | CHICLAYO | 75886238 | 108 | 23 | 23 | 0 |
| CARLOS ARTEAGA MENDOZA | CHICLAYO | 42406447 | 66 | 15 | 15 | 0 |
| CELESTE DIAZ | CAJAMARCA | 40644415 | 101 | 22 | 22 | 0 |
| Carlos Alberto Cóndor Mendoza | Ruta Chiclayo - Cajamarca | Sin código importado | Sin identidad en archivo | 0 | 0 | 0 |
| Carlos Plaza | CHICLAYO | 73476731 | 59 | 21 | 21 | 0 |
| Cralos Arteaga | CHICLAYO | 42406447 | 74 | 24 | 24 | 0 |
| DIEGO VELIZ | CHICLAYO | 72917006 | 122 | 23 | 23 | 0 |
| Dayana Ramos | CHICLAYO | 70584629 | 119 | 24 | 24 | 0 |
| Deidamia Gracia Castro | CHICLAYO | 16664706 | 45 | 22 | 22 | 0 |
| Diana Choquehuanca | CHICLAYO | 73775980 | 56 | 22 | 22 | 0 |
| ELIZABETH BRIONES | CHICLAYO | 72169457 | 108 | 23 | 23 | 0 |
| EMERITO CRUZ | CAJAMARCA | 40737200 | 125 | 24 | 24 | 0 |
| EVELYN YESENIA LEON SANC | JAEN | 71865086 | 28 | 7 | 7 | 0 |
| Emir Monteza | CHICLAYO | 16762381 | 115 | 24 | 24 | 0 |
| Felix Allende | CHICLAYO | 16659599 | 84 | 21 | 21 | 0 |
| GRECIA CRUUZ | JAEN | 70153082 | 112 | 24 | 24 | 0 |
| Hemely Yamunaque | CHICLAYO | 41229451 | 59 | 11 | 11 | 0 |
| Israel Roque | CHICLAYO | 16788665 | 8 | 0 | 0 | 0 |
| JORGE AGUILAR | TRUJILLO | 18181133 | 66 | 16 | 16 | 0 |
| JUAN ZAPATA | PAUL HARRIS | 16789175 | 25 | 0 | 0 | 0 |
| JUANITA SANTOS ESPINOZA | JAEN | 42807281 | 56 | 11 | 11 | 0 |
| Jhon Davila | CHICLAYO | 75461010 | 64 | 11 | 11 | 0 |
| Juan Manuel Pérez Huamán | Ruta Trujillo - Jaén | Sin código importado | Sin identidad en archivo | 0 | 0 | 0 |
| Julio Chung | CHICLAYO | 41187159 | 102 | 22 | 22 | 0 |
| LUZ MARINA | CAJAMARCA | 40 | 109 | 24 | 24 | 0 |
| Lilian VASQUEZ SOTO | CHICLAYO | 75135601 | 101 | 24 | 24 | 0 |
| Liliana Hurtado | CHICLAYO | 16804278 | 111 | 24 | 24 | 0 |
| MANUEL MOSQUEIRA ALTAMIR | PAUL HARRIS | 73766146 | 172 | 23 | 23 | 0 |
| MIDORI SALAZAR | CAJAMARCA | 41 | 108 | 23 | 23 | 0 |
| Mariasol Sanchez | CHICLAYO | 70830398 | 106 | 22 | 22 | 0 |
| Mendoza Regalado | CAJAMARCA | 15 | 28 | 24 | 24 | 0 |
| Merly Moreno | CHICLAYO | 47633956 | 107 | 23 | 23 | 0 |
| Miguel Ángel Sánchez Farfán | Chiclayo - Embarque Terminal | Sin código importado | Sin identidad en archivo | 0 | 0 | 0 |
| Nancy Flores | CHICLAYO | 43984377 | 12 | 2 | 2 | 0 |
| Nancy Flores Cruz | GACELA | 43984377 | 96 | 21 | 21 | 0 |
| Nilson Silupu (Admin TI) | Chiclayo - Terminal Central | Sin código importado | Sin identidad en archivo | 0 | 0 | 0 |
| PASAPERA mendigo rufio | CAJAMARCA | 13 | 106 | 22 | 22 | 0 |
| Pedro Chavesta | PAUL HARRIS | 76305994 | 103 | 23 | 23 | 0 |
| Pedro Luis Morales Cieza | Chiclayo - Administración | Sin código importado | Sin identidad en archivo | 0 | 0 | 0 |
| QUILICHE SAENZ | CAJAMARCA | 80555327 | 149 | 23 | 23 | 0 |
| RIVERA SANCJEZ | CAJAMARCA | 34 | 116 | 28 | 28 | 0 |
| ROBERTO RIVERA | PAUL HARRIS | 16493695 | 128 | 23 | 23 | 0 |
| SEGUNDO LLONTOP | PAUL HARRIS | 42654685 | 107 | 25 | 25 | 0 |
| SIN DATOS | JAEN | 71202708 | 87 | 17 | 17 | 0 |
| Segundo Ramos (Gerente General) | Chiclayo - Gerencia General | Sin código importado | Sin identidad en archivo | 0 | 0 | 0 |
| TERRONES VASQUEZ YANELI | CHICLAYO | 73771346 | 72 | 23 | 23 | 0 |
| Yaneli Madeleyne Terrones Vásquez (CPC) | Chiclayo - Oficina Principal | Sin código importado | Sin identidad en archivo | 0 | 0 | 0 |
| fernando allende muñoz | CHICLAYO | 16659599 | 32 | 9 | 9 | 0 |
| rojas alan | CAJAMARCA | 33 | 108 | 25 | 25 | 0 |
| roque vega | CHICLAYO | 16788665 | 106 | 27 | 27 | 0 |
| silvio cruz | CAJAMARCA | 23 | 51 | 22 | 22 | 0 |
| teran diaz luis | CAJAMARCA | 2 | 117 | 23 | 23 | 0 |

## Propuesta de corrección para todos los trabajadores
1. Crear un catálogo de horarios confirmado por la contadora o responsable: sede, entrada, salida, refrigerio, tolerancia y si termina al día siguiente. Separar esas horas de la duración base de cálculo.
2. Programar el turno por trabajador y fecha, con asignación por rango o semana para quienes rotan. La jornada conserva el turno histórico aplicado, aunque después cambie el turno habitual.
3. Mostrar «Horario por confirmar» y «Tardanza pendiente de cálculo» cuando falte la programación. No presentar cero como puntualidad ni asignar 08:00 a todos. Las marcas pueden sugerir una franja para revisión, pero no justificar por sí mismas una llegada tardía ni cambiar el horario programado.
4. Unir correctamente entrada nocturna y salida del día siguiente antes de validar secuencias, calcular horas y tardanza. No interpretar automáticamente la primera marca del calendario como entrada.
5. Revisar las once fechas de Abisag, luego las jornadas sin horario de las demás fichas. Recalcular tardanza solo después de confirmar el turno, conservando las marcas originales.
6. Registrar responsable, turno anterior/nuevo y motivo. Si una jornada aprobada cambia, dejarla pendiente de nueva revisión; si pertenece a un período cerrado, respetar el flujo de reapertura. No conservar una aprobación anterior sobre resultados modificados.
7. Verificar casos de mañana, tarde, rotación, noche, refrigerio, marcación faltante y permiso/descanso antes de aplicar el proceso a todo el período.

## Fuentes y alcance
- ASISTENCIA AGOSTO 2026.xlsx: 51 hojas, incluidas 43 individuales, seis exportaciones por sede, CUADRO y Hoja1. Se inspeccionaron valores y fórmulas, no se ejecutaron macros ni se sobrescribió el archivo.
- Asistencia zkteco.xlsx: seis hojas y 4.287 marcaciones. Las 60 identidades por sede/equipo/código tienen correspondencia en el sistema con 50 fichas actuales.
- PostgreSQL de SISMOC-CUMBE: consulta de TurnoHorario, Trabajador, IdentidadBiometrica y jornadas de agosto, realizada el 22/10/2026. La reconstrucción usa eventos efectivos y correcciones del sistema.
- Código revisado: asistencia/services/revision_trabajador.py, validar_periodo; asistencia/services/revision.py, ventana_jornada y detalle_jornada. La tardanza compara la primera entrada laboral reconstruida con la entrada del turno aplicado y evalúa la tolerancia.
Las hojas individuales son evidencia contable de lo realizado y de sus cálculos. Falta la programación laboral oficial para certificar el número final de horarios, su tolerancia y las tardanzas reales.
