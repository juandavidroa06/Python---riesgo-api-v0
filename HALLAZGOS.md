# Hallazgos — Parte A

 **Integrantes:** Laura Rodríguez y Juan Roa

> No borren la fila de ejemplo hasta haber comprobado que su tabla se parsea.
> El formato es rígido: siete columnas, en este orden. Una tabla torcida se
> rechaza indicando la línea, no se «entiende igual».
>
> **Tuberías dentro de una celda:** si su comando lleva `|` —y varios lo llevarán,
> por `grep`, `head` o `jq`— escríbanlo `\|`. Sin escapar, Markdown lo lee como
> separador de columna y su fila pasa a tener ocho.

| ID | Síntoma observable | Causa | Módulo · Sección | SHA donde se observa | Comando de evidencia | Salida obtenida | Corrección aplicada |
|----|--------------------|-------|-------------------|-----------------------|------------------------|------------------|----------------------|
| H1 | `config.py` tiene credenciales en texto plano versionadas en el repositorio | El archivo declara `API_KEY` y `CLAVE_FIRMA` como constantes literales, con un TODO reconociendo el problema | M1 · 5. Git y GitHub para investigadores | `v0-semilla` | `cat config.py` | `API_KEY = "sk-riesgo-2026-9f3a1c7b4e21"` | Movidas a variables de entorno vía `.env`, con `.env.example` como plantilla |
| H2 | El decorador `con_registro` reporta `__name__ == "envoltura"` en vez de `"puntuar"` en la función que envuelve | No usa `functools.wraps`, así que oculta la identidad de la función original | M1 · 6. Decoradores como guardianes | `v0-semilla` | `python -c "from dominio import EvaluadorRiesgo; print(EvaluadorRiesgo.puntuar.__name__)"` | `envoltura` | Se agregó `@functools.wraps(func)` al decorador |
| H3 | `POST /score` con payload vacío responde `200 OK` con el error en el cuerpo | La validación no usa Pydantic; el error se serializa manualmente sin cambiar el status code | M2 · 2. El protocolo HTTP y la autenticación | `v0-semilla` | `curl -s -i -X POST http://localhost:8000/score -d "{}" -H "Content-Type: application/json"` | `HTTP/1.1 200 OK` … `{"error":"falta el campo poliza"}` | Entrada validada con `BaseModel`; `ValidationError` → 422 automático |
| H4 | `GET /health` responde `404 Not Found` | El endpoint no existe en el servicio | M5 · 3. El servidor web y WSGI | `v0-semilla` | `curl -s -i http://localhost:8000/health` | `HTTP/1.1 404 Not Found` … `{"detail":"Not Found"}` | Se creó el endpoint `GET /health` devolviendo `200` |
| H5 | `GET /exportar` responde con `content-type: application/octet-stream` en vez de JSON | El endpoint serializa la respuesta con `pickle.dumps()` en vez de un formato estándar de intercambio | M2 · 3. JSON frente a Pickle | `v0-semilla` | `curl -s -i http://localhost:8000/exportar` | `HTTP/1.1 200 OK` … `content-type: application/octet-stream` … `content-length: 22481` | Ahora devuelve `list[Siniestro]` serializado en JSON |
| H6 | Dos instancias de `EvaluadorRiesgo` comparten el mismo historial de anotaciones | `historial = []` está declarado como atributo de clase (fuera de `__init__`), no de instancia | M3 · 3. Componentes: atributos de clase | `v0-semilla` | `python -c "from dominio import EvaluadorRiesgo as E; a=E('POL-A'); b=E('POL-B'); a.anotar(0.5); print(b.historial)"` | `[{'poliza': 'POL-A', 'puntaje': 0.5}]` | Se movió a `self.historial = []` dentro de `__init__` |
| H7 | `POST /score` con `monto` negativo responde `500 Internal Server Error` en vez de un error controlado | El código usa un `assert` para validar el monto en vez de una validación declarativa; un `assert` puede desactivarse globalmente con `python -O`, y además no traduce a un status HTTP correcto | M4 · 6. Validadores de campo | `v0-semilla` | `curl -s -i -X POST http://localhost:8000/score -d '{"poliza":"POL-1","monto":-500,"antiguedad":2,"siniestros_previos":0}' -H "Content-Type: application/json"` | `HTTP/1.1 500 Internal Server Error` … `Internal Server Error` | Se agregó `@field_validator` en el `BaseModel` que rechaza montos negativos, traduciendo a `422` |
| H8 | `requirements.txt` no fija ninguna versión de sus dependencias | Declara los paquetes por nombre sin `==versión`, lo que permite instalar versiones distintas a las usadas para entrenar `modelo.pkl` | M2 · 5. requirements.txt y la reproducibilidad | `v0-semilla` | `cat requirements.txt` | `fastapi` · `uvicorn` · `pydantic` · `scikit-learn` · `numpy` · `pytest` · `httpx` — ninguna con `==` | Se fijaron todas las versiones, incluyendo `scikit-learn==1.7.2` para coincidir con la versión que entrenó el modelo |


**Reglas que se verifican automáticamente:**

- `Módulo · Sección` debe citar una lección que exista en los módulos 1 a 5, con el
  título tal como aparece en el menú lateral del material.
- **`SHA donde se observa`** es el commit donde el defecto todavía está: normalmente
  `v0-semilla`, la etiqueta del repositorio tal como se lo entregamos. El calificador hace
  *checkout* de ese commit para reproducir la evidencia. Si lo dejan en el commit final —donde
  ya está corregido— el comando no reproducirá nada y la fila no cuenta.
- `Comando de evidencia` se ejecuta ahí. Escríbanlo contra `localhost:8000`; el calificador
  sustituye el puerto por el que use.
- `Salida obtenida` es literal, copiada de su terminal. **Se compara con lo que salga de
  verdad**, así que una salida inventada se detecta.
- Entre 6 y 12 hallazgos. Una fila que no corresponda a un defecto real resta la mitad de lo
  que suma una correcta: el máximo se alcanza con precisión, no con volumen.

---

# Parte C — Interpretación de las mediciones

**/ping** — Clasificación: trivial. Decisión: `async def`.
No hace trabajo de I/O ni de CPU, así que su tiempo de respuesta es
prácticamente constante sin importar la concurrencia: p50 pasó de 1.6 ms
(concurrencia 1) a 19.0 ms (concurrencia 20), y p95 de 2.4 ms a 41.8 ms.
El pequeño aumento se explica por overhead de scheduling del event loop
al atender 20 peticiones a la vez, no por trabajo real. `async def` es la
decisión correcta y no requirió ningún cambio de código.

**/consulta-archivo** — Clasificación: IO-bound. Decisión: `def`.
Con `read_text()` bloqueante dentro de un `async def` (versión original),
la concurrencia empeoraba el tiempo total. Al declararlo `def`, FastAPI lo
despacha a un thread pool: el tiempo_total_s con concurrencia 20 (0.104 s)
quedó ligeramente por debajo del de concurrencia 1 (0.109 s). El p50 y el
p95 sí suben con la concurrencia (2.1→27.3 ms, 2.8→49.2 ms), pero es el
overhead normal de repartir 20 peticiones entre hilos para un archivo tan
pequeño, no un síntoma de bloqueo del servidor completo.

**/servicio-externo** — Clasificación: IO-bound. Decisión: `async def`.
Esta es la evidencia más clara de que "IO va con async" funciona cuando el
`await` es real. Con `time.sleep(0.3)` bloqueante (versión original), 20
peticiones concurrentes se encolaban una tras otra. Con `await
asyncio.sleep(0.3)`, el tiempo_total_s con concurrencia 20 cayó a 0.957 s
frente a 15.109 s con concurrencia 1 — las 20 esperas de red se solapan de
verdad. El p50 (319.7 ms) y el p95 (332.1 ms) se mantienen casi idénticos
entre sí y cercanos a los 300 ms base del `sleep`, sin cola: la prueba de
que aquí sí hay concurrencia real.

**/calculo-pesado** — Clasificación: CPU-bound. Decisión: `def`.
Corrimos esta medición tres veces con `def` para confirmar el patrón, y
resultó más matizado de lo que parecía en la primera corrida. El
tiempo_total_s con concurrencia 20 fue consistentemente MENOR que con
concurrencia 1 en las tres corridas (18.305 vs 19.340 s; 14.643 vs 26.317 s;
12.709 vs 19.729 s) — es decir, sí hay una ganancia real de throughput
agregado al repartir el cálculo entre varios hilos del pool. Sin embargo,
el p50 con concurrencia 20 fue entre 12 y 19 veces peor que con
concurrencia 1 en las tres corridas (357→7033 ms; 448→5704 ms; 374→4561 ms).
Esta combinación —throughput agregado algo mejor, latencia individual
mucho peor— es la firma típica del GIL: los 20 hilos sí logran que el
conjunto de peticiones termine antes en total (porque un hilo puede
avanzar mientras otro espera su turno de intérprete), pero cada petición
individual tarda mucho más en completarse porque compite constantemente
por el GIL con las otras 19. Un usuario esperando una sola respuesta
percibiría el servicio como mucho más lento bajo carga, aunque el sistema
en conjunto procese el lote algo más rápido. Para lograr paralelismo real
—mejor throughput SIN penalizar la latencia individual— haría falta un
`ProcessPoolExecutor` en vez de un thread pool, porque cada proceso evade
el GIL al tener su propio intérprete; no lo implementamos porque `def` ya
resuelve el defecto original más grave (bloquear el servidor completo
para otras rutas) y el taller no exige la solución de máximo rendimiento,
solo coherencia entre clasificación, decisión y evidencia medida.