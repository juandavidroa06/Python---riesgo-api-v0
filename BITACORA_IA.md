# BITACORA_IA.md

## Prompts

Resumen de los prompts principales usados durante el taller (asistente:
Claude, Anthropic):

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

<!--
  Completar con cualquier prompt, aceptación o rechazo adicional que no
  esté cubierto aquí (por ejemplo, si usaron otro asistente de IA además
  de este, o partes del trabajo que no se hicieron en esta conversación).
-->
