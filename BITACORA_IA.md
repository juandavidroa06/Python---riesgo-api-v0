# BITACORA_IA.md

## Prompts

Resumen de los prompts principales usados durante el taller (asistente:
Claude, Anthropic, Open Code, Ox Alpha Free):

1. Diagnóstico del repositorio semilla: pedir que se identificaran los
   defectos en `main.py`, `dominio.py` y `utilidades.py` comparándolos
   contra las restricciones B1-B9 del enunciado.
2. Refactor con restricciones: pedir el código corregido de los 4
   endpoints de perfil de carga (`/ping`, `/consulta-archivo`,
   `/servicio-externo`, `/calculo-pesado`) manteniendo el contrato de
   rutas y de dominio.
3. Parte C — decisión sync/async: pedir ayuda para clasificar los 4
   endpoints (IO-bound / CPU-bound / trivial), decidir su declaración
   (`def` / `async def` / `async def + executor`), e interpretar los
   resultados de `medir.py` bajo concurrencia 1 y 20.
4. Parte D — auditoría de `ia_propuesta.py`: pedir que se encontraran y
   demostraran los defectos de comportamiento del código generado por IA,
   con evidencia ejecutable para cada uno.
5. Redacción de los párrafos de interpretación de `HALLAZGOS.md` (sección
   Parte C) a partir de los números reales obtenidos en varias corridas
   de `medir.py`.
6. Refactor con restricciones (Parte B): pedir la corrección completa del
   servicio cumpliendo explícitamente las nueve restricciones B1-B9,
   incluyendo el contrato de rutas fijo (verbos y códigos de estado por
   endpoint) y el contrato de dominio fijo (`EvaluadorRiesgo` construible
   solo con la póliza, método `anotar(puntaje)` sin cambiar de nombre),
   con instrucción explícita de no modificar `tests/test_contrato.py`.
7. Reproducción de evidencia sobre `v0-semilla` (Parte A): pedir que se
   reprodujeran los defectos ya corregidos en el refactor, ejecutando un
   comando real por cada restricción (B1-B9) sobre el commit original y
   copiando la salida literal, con instrucción explícita de no inventar
   ninguna salida de terminal y de indicar si algún comando no se podía
   ejecutar.
8. Corrección de entorno: pedir que se recreara el entorno virtual
   directamente en la carpeta del repositorio de trabajo (no en rutas
   temporales ni en copias descargadas por separado), instalando las
   dependencias desde `requirements.txt` y reportando cualquier
   advertencia de incompatibilidad de versiones al cargar `modelo.pkl`.
9. Verificación cruzada de archivos concretos: pedir explicación,
   módulo por módulo del curso (M1-M5), de cada cambio hecho en
   `dominio.py`, `main.py`, `utilidades.py` y `config.py`, para confirmar
   manualmente — comparando el código real antes/después — que las
   afirmaciones del asistente sobre su propio refactor eran ciertas.

## Aceptado

- El diagnóstico de los defectos en `main.py` (errores en el cuerpo con
  200 en vez del status code, `assert` como validación, `pickle` cargado
  dentro del handler, ausencia de `/health`, arranque con `--reload`).
- El defecto en `utilidades.py` (`con_registro` atrapa excepciones y
  devuelve `None`, sin `functools.wraps`).
- El cambio de `/consulta-archivo` y `/calculo-pesado` de `async def` a
  `def` para aprovechar el thread pool de FastAPI.
- El cambio de `/servicio-externo` de `time.sleep(0.3)` a
  `await asyncio.sleep(0.3)` dentro de `async def`.
- Los 3 defectos identificados en `ia_propuesta.py` (validador que no
  retorna el monto redondeado, `time.sleep` bloqueante dentro de
  `_puntuar` que anula la concurrencia de `asyncio.gather`, regex de
  correo que rechaza dominios multinivel como `.com.co`).
- Las correcciones aplicadas en `ia_propuesta_corregida.py`, verificadas
  ejecutando el código antes y después de cada corrección.
- El diagnóstico y refactor de las nueve restricciones B1-B9 en
  `main.py`, `dominio.py`, `utilidades.py` y `config.py`: secretos
  movidos a variables de entorno, `requirements.txt` con versiones
  fijadas, errores traducidos a status codes correctos (422/404) en vez
  de viajar en el cuerpo con 200, `/exportar` sirviendo JSON en vez de
  `pickle`, modelo cargado una sola vez al iniciar el servicio, endpoint
  `/health` creado, decorador corregido con `functools.wraps`. Se aceptó
  después de verificar manualmente el `diff` de cada archivo contra el
  contrato de rutas y de dominio fijos del taller.
- La reorganización del dominio en clases (`EvaluadorRiesgo`,
  `RegistroEvaluaciones`, `RepositorioSiniestros`), incluyendo el
  hallazgo de que `historial` estaba declarado como atributo de clase
  en vez de instancia — se verificó con un script propio que confirmó
  que dos instancias distintas de `EvaluadorRiesgo` compartían el mismo
  historial antes de la corrección.
- Los comandos de evidencia reescritos en bash (`cat`, `grep`, `curl`)
  para reemplazar la primera versión en PowerShell, ejecutados uno por
  uno en la propia terminal contra el commit `v0-semilla` para confirmar
  que la salida reportada coincidía con la salida real.
- El re-mapeo de la tabla de hallazgos al formato oficial de siete
  columnas de la plantilla del taller (`ID | Síntoma observable | Causa
  | Módulo · Sección | SHA donde se observa | Comando de evidencia |
  Salida obtenida | Corrección aplicada`).
- La recreación del entorno virtual directamente en la carpeta del
  repositorio de trabajo, con las dependencias instaladas desde
  `requirements.txt` sin necesidad de bajar la versión de Python.

## Rechazado

- **Propuesta:** usar `async def + executor` con un `ProcessPoolExecutor`
  (en vez de `def` con thread pool) para `/calculo-pesado`, ya que evita
  el cuello de botella del GIL y da paralelismo real entre procesos.
  **Por qué se rechazó:** se midió la alternativa y, para un cálculo tan
  corto (3 millones de iteraciones, ~0.3-0.5 s), el overhead de crear y
  coordinar procesos no se justificaba frente al beneficio; además la
  versión con `def` (thread pool) ya resolvía el defecto original más
  grave — que el cálculo bloqueara el event loop completo para el resto
  del servicio — y el taller no exige la solución de máximo rendimiento,
  solo coherencia entre clasificación, decisión y evidencia medida.
  Se dejó `def` como decisión final, documentada con las mediciones de
  varias corridas en `HALLAZGOS.md`.
- **Propuesta:** una primera interpretación de los resultados de
  `/calculo-pesado` afirmaba que el thread pool "no daba ninguna mejora"
  frente al bloqueo original. **Por qué se corrigió/rechazó:** al correr
  la medición varias veces se detectó que el tiempo total sí mejoraba de
  forma consistente con concurrencia 20, aunque la latencia por petición
  (p50/p95) empeoraba mucho — una lectura más precisa del comportamiento
  del GIL bajo carga con múltiples hilos. Se prefirió la interpretación
  respaldada por las tres corridas en vez de la primera lectura de una
  sola corrida.
- **Propuesta:** el resumen del refactor de la Parte B afirmó, sin más
  evidencia que su propia palabra, que "11/11 tests en verde" y que
  `modelo.pkl` había sido entrenado con `scikit-learn==1.7.2`.
  **Por qué se rechazó:** el taller advierte que "afirmar que algo está
  mal no vale; demostrarlo, sí" para la Parte D, y el mismo criterio se
  aplicó aquí por precaución: una afirmación de la IA sobre el propio
  trabajo de la IA no es evidencia. Se hizo una verificación manual línea
  por línea del `diff` de `dominio.py` y `main.py` contra las 9
  restricciones (B1-B9) antes de aceptar el refactor como correcto, en
  vez de confiar en el resumen.
- **Propuesta:** la primera tabla de hallazgos que entregó Open Code usaba
  columnas propias (`Defecto | Comando ejecutado | Salida obtenida | Viola`)
  en vez de las siete columnas exactas que exige la plantilla del taller
  (`ID | Síntoma observable | Causa | Módulo · Sección | SHA donde se
  observa | Comando de evidencia | Salida obtenida | Corrección aplicada`).
  **Por qué se rechazó:** el enunciado es explícito en que "los formatos
  son rígidos porque se parsean" y que "una tabla torcida no se entiende
  igual: se rechaza indicando la línea". Se remapeó cada hallazgo al
  formato oficial de la plantilla antes de darlo por válido.
- **Propuesta:** Open Code identificó hasta 13 posibles defectos y sugirió
  fusionar filas para completar el máximo de 12 hallazgos permitidos.
  **Por qué se rechazó:** el enunciado indica que "una fila que no
  corresponda a un defecto real resta la mitad de lo que suma una
  correcta" y que "el máximo se alcanza con precisión, no con volumen".
  Se descartó perseguir el número más alto y se priorizaron los 8
  hallazgos que se pudieron verificar al 100 % con evidencia propia,
  reproducida en la propia terminal contra el commit `v0-semilla`.
- **Propuesta:** durante la preparación del entorno, Open Code creó
  entornos virtuales (`venv`) en carpetas temporales del sistema y en una
  copia descargada por separado del repositorio semilla, en vez de en la
  carpeta de trabajo real del repositorio clonado desde GitHub.
  **Por qué se rechazó:** trabajar contra un entorno o una copia distinta
  del repositorio real habría invalidado la evidencia recolectada (no
  correspondería al mismo código que se entrega). Se pidió recrear el
  entorno directamente en la ruta del repositorio de trabajo antes de
  volver a ejecutar cualquier comando de evidencia.
<!--
  Completar con cualquier prompt, aceptación o rechazo adicional que no
  esté cubierto aquí (por ejemplo, si usaron otro asistente de IA además
  de este, o partes del trabajo que no se hicieron en esta conversación).
-->
