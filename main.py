"""
riesgo-api-v0 — Servicio de puntuación de siniestros.
Aseguradora Santo Tomás · prototipo interno.
"""
import pickle
import time
import asyncio
from pathlib import Path

from fastapi import FastAPI, HTTPException

import config
from dominio import EvaluadorRiesgo, RegistroEvaluaciones, RepositorioSiniestros
from esquemas import (
    ConteoLineasRespuesta,
    PingRespuesta,
    RespuestaHistorial,
    RespuestaPuntuacion,
    ReservaAgregadaRespuesta,
    SaludRespuesta,
    Siniestro,
    SolicitudPuntuacion,
    TarifaReferenciaRespuesta,
)


BASE = Path(__file__).parent


def cargar_modelo(ruta):
    with open(ruta, "rb") as fh:
        return pickle.load(fh)


# B6: las dependencias pesadas se construyen UNA VEZ al arrancar el proceso,
# nunca dentro de un handler. pickle solo se usa para LEER el artefacto
# confiado del modelo (B3 prohíbe serializar hacia el cliente).
MODELO = cargar_modelo(BASE / config.RUTA_MODELO)
REPOSITORIO_SINIESTROS = RepositorioSiniestros(BASE / config.RUTA_DATOS)
REGISTRO_EVALUACIONES = RegistroEvaluaciones()

app = FastAPI(title="Riesgo API", version="0.2.0")



@app.post("/score", response_model=RespuestaPuntuacion)
async def score(solicitud: SolicitudPuntuacion):
    # La validación declarativa (B5) es responsabilidad de Pydantic:
    # cualquier entrada inválida nunca llega aquí; FastAPI responde 422.
    evaluador = EvaluadorRiesgo(
        solicitud.poliza,
        modelo=MODELO,
        registro=REGISTRO_EVALUACIONES,
    )
    puntaje = evaluador.puntuar(solicitud.model_dump())
    evaluador.anotar(puntaje)
    return RespuestaPuntuacion(
        poliza=solicitud.poliza,
        puntaje=puntaje,
        alto_riesgo=evaluador.es_alto_riesgo(puntaje),
    )


@app.get("/historial", response_model=RespuestaHistorial)
async def historial():
    return RespuestaHistorial(evaluaciones=REGISTRO_EVALUACIONES.todas())


@app.get("/siniestros/{id_siniestro}", response_model=Siniestro)
async def siniestro(id_siniestro: int):
    fila = REPOSITORIO_SINIESTROS.obtener(id_siniestro)
    if fila is None:
        # B2: el error viaja en el estado (404), no en el cuerpo con 200.
        raise HTTPException(status_code=404, detail=f"no existe el siniestro {id_siniestro}")
    return Siniestro(**fila)


@app.get("/exportar", response_model=list[Siniestro])
async def exportar():
    # B3: JSON, nunca pickle hacia el cliente.
    return [Siniestro(**fila) for fila in REPOSITORIO_SINIESTROS.todos()]


# B7: comprobación de vida del servicio.
@app.get("/health", response_model=SaludRespuesta)
async def health():
    return SaludRespuesta(status="ok")


# --- Endpoints de perfil de carga -----------------------------------------
# Su declaración sync/async se decide con mediciones en la Parte C.

@app.get("/ping", response_model=PingRespuesta)
async def ping():
    return PingRespuesta(pong=True)


@app.get("/consulta-archivo", response_model=ConteoLineasRespuesta)
def consulta_archivo():
    contenido = (BASE / config.RUTA_DATOS).read_text(encoding="utf-8")
    return ConteoLineasRespuesta(
        lineas=len(contenido.splitlines())
    )


@app.get("/servicio-externo", response_model=TarifaReferenciaRespuesta)
async def servicio_externo():
    await asyncio.sleep(0.3)
    return TarifaReferenciaRespuesta(tarifa_referencia=1.18)


@app.get("/calculo-pesado", response_model=ReservaAgregadaRespuesta)
def calculo_pesado():
    total = 0.0

    for i in range(3_000_000):
        total += (i % 7) ** 0.5

    return ReservaAgregadaRespuesta(total=round(total, 2))



if __name__ == "__main__":
    import uvicorn

    # B8: arranque de producción — sin --reload, con --workers.
    uvicorn.run("main:app", host="0.0.0.0", port=8000, workers=2)
