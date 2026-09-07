# riesgo-api-v0

Servicio de puntuación de siniestros de la Aseguradora Santo Tomás.
Recibe los datos de una póliza y devuelve la probabilidad de que el siniestro
declarado termine en un pago alto.

## Instalación

```bash
python -m venv .venv

# Linux / macOS
source .venv/bin/activate

# Windows
.venv\Scripts\activate

pip install -r requirements.txt
```

Las dependencias están fijadas con `==` para que el entorno sea reproducible.
`modelo.pkl` viene en el repositorio: es el artefacto entrenado con
scikit-learn 1.7.2 y el servicio lo necesita para arrancar.

## Puesta en marcha

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 2
```

Ese es el arranque de producción: **sin `--reload`** (la recarga en caliente
no es apta para producción) y **con `--workers`**.

## Variables de entorno

Los secretos no viven en el código. Si tu despliegue los necesita, copia
`.env.example` a `.env`, completa los valores y cárgalos en el entorno.
`.env` está ignorado por Git.

## Endpoints

| Método | Ruta | Qué hace |
|---|---|---|
| POST | `/score` | Puntúa una póliza · 422 si la entrada es inválida |
| GET | `/historial` | Evaluaciones hechas |
| GET | `/siniestros/{id}` | Consulta un siniestro · 404 si no existe |
| GET | `/exportar` | Exporta el histórico en JSON para actuaría |
| GET | `/health` | Comprobación de vida del servicio |
| GET | `/ping` | Comprobación rápida |
| GET | `/consulta-archivo` | Cuenta los registros del archivo de siniestros |
| GET | `/servicio-externo` | Consulta la tarifa de referencia del reasegurador |
| GET | `/calculo-pesado` | Recalcula la reserva agregada |

### Ejemplos

Caso válido:

```bash
curl -X POST localhost:8000/score \
  -H "Content-Type: application/json" \
  -d '{"poliza": "POL-2026-0413", "monto": 4200000, "antiguedad": 3, "siniestros_previos": 1}'
```

```json
{"poliza": "POL-2026-0413", "puntaje": 0.61, "alto_riesgo": false}
```

Caso inválido — el error viaja en el estado HTTP (422), nunca en el cuerpo
con 200:

```bash
curl -i -X POST localhost:8000/score \
  -H "Content-Type: application/json" \
  -d '{"monto": -5}'
```

## Tests

```bash
pytest -v
```
