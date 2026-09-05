# DICTAMEN_IA.md — Auditoría de `ia_propuesta.py`

## Defecto 1

- **Qué está mal:** El validador `redondear_monto` (decorado con
  `@field_validator("monto")`) calcula `round(v, 2)` pero **no retorna el
  resultado**. En Pydantic v2, el valor que retorna un `field_validator` es
  el que queda asignado al campo. Como la función no tiene `return`,
  retorna `None` implícitamente, y por lo tanto **el campo `monto` queda
  en `None` después de validar**, sin importar qué monto se haya enviado.

- **Por qué es un defecto** (citando módulo · sección): M4 · Validación
  declarativa con Pydantic — un validador de campo debe transformar y
  devolver el valor; omitir el `return` no es un error de sintaxis (el
  código corre sin excepciones) pero rompe silenciosamente el dato central
  del modelo de negocio.

- **Cómo lo comprobamos:**
  ```python
  from ia_propuesta import SolicitudPuntuacion

  s = SolicitudPuntuacion(
      poliza="POL-2026-0413",
      correo_analista="ana@aseguradora.co",
      monto=1500000.456,
      antiguedad=3,
      siniestros_previos=1,
  )
  print(s.monto)
  ```
  Salida obtenida:
  ```
  None
  ```
  (Esperado: `1500000.46`)

- **Corrección:** Agregar `return round(v, 2)` al final del validador.

---

## Defecto 2

- **Qué está mal:** La función `_puntuar` está declarada `async def`, pero
  usa `time.sleep(0.2)` en vez de `await asyncio.sleep(0.2)` para simular
  la latencia del servicio externo. Como `time.sleep` es una llamada
  bloqueante, congela el event loop completo mientras espera, así que
  `asyncio.gather` en `evaluar_lote` **no logra ninguna concurrencia
  real**: las N solicitudes del lote se procesan una tras otra.

- **Por qué es un defecto** (citando módulo · sección): M5 · Concurrencia
  con async/await — el prompt original pedía explícitamente una función
  que evaluara el lote "concurrentemente"; con una llamada bloqueante
  dentro de una corrutina, el resultado es indistinguible de una
  implementación estrictamente secuencial, contradiciendo el propósito
  mismo de usar `async`/`await`.

- **Cómo lo comprobamos:**
  ```python
  import asyncio, time
  from ia_propuesta import evaluar_lote, SolicitudPuntuacion

  solicitudes = [
      SolicitudPuntuacion(
          poliza=f"POL-2026-{i:04d}", correo_analista="ana@aseguradora.co",
          monto=100.0, antiguedad=1, siniestros_previos=0,
      )
      for i in range(10)
  ]

  inicio = time.perf_counter()
  asyncio.run(evaluar_lote(solicitudes))
  print(time.perf_counter() - inicio)
  ```
  Salida obtenida:
  ```
  2.00
  ```
  (Esperado si fuera concurrente de verdad: ~0.2 s, no 10 × 0.2 s)

- **Corrección:** Reemplazar `time.sleep(0.2)` por `await asyncio.sleep(0.2)`.

---

## Defecto 3

- **Qué está mal:** El patrón del campo `correo_analista` —
  `r"^[A-Za-z0-9_.+-]+@[A-Za-z0-9-]+\.[A-Za-z]{2,3}$"` — solo acepta
  dominios de un único segmento seguido de un TLD de 2 a 3 letras
  (por ejemplo `empresa.co`, `empresa.com`). **Rechaza dominios de más de
  un nivel**, como los `.com.co` / `.edu.co` que son extremadamente
  comunes en Colombia, y cualquier TLD de 4+ letras (`.info`, `.email`).

- **Por qué es un defecto** (citando módulo · sección): M4 · Validación
  declarativa con Pydantic — una regla de validación demasiado estricta
  rechaza datos legítimos del dominio del negocio (correos corporativos
  reales de analistas de la aseguradora), lo cual en producción bloquearía
  a usuarios válidos en vez de proteger contra datos malformados.

- **Cómo lo comprobamos:**
  ```python
  from ia_propuesta import SolicitudPuntuacion
  from pydantic import ValidationError

  try:
      SolicitudPuntuacion(
          poliza="POL-2026-0413",
          correo_analista="ana.perez@aseguradorasantotomas.com.co",
          monto=100.0, antiguedad=1, siniestros_previos=0,
      )
      print("Aceptado")
  except ValidationError as e:
      print("Rechazado (deberia ser valido)")
      print(e)
  ```
  Salida obtenida:
  ```
  Rechazado (deberia ser valido)
  1 validation error for SolicitudPuntuacion
  correo_analista
    String should match pattern '^[A-Za-z0-9_.+-]+@[A-Za-z0-9-]+\.[A-Za-z]{2,3}$'
  ```

- **Corrección:** Ampliar el patrón para aceptar dominios multinivel y
  TLDs de 2 o más letras:
  `r"^[A-Za-z0-9_.+-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}$"`
