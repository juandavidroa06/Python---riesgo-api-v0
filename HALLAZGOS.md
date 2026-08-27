# Hallazgos — Parte A

**Grupo:** <número> · **Integrantes:** <nombre 1>, <nombre 2>, <nombre 3>

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

> Un párrafo por endpoint. Expliquen **los tiempos que ustedes obtuvieron**, no la
> teoría general. Si un resultado los sorprendió, dígan­lo: eso se premia.

## `/ping`

## `/consulta-archivo`

## `/servicio-externo`

## `/calculo-pesado`
