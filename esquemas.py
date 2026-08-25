"""Contratos de entrada y salida declarados con Pydantic (restricción B5).

Toda entrada y toda salida del servicio pasa por estos modelos: las
restricciones viven en `Field()` y los validadores en `@field_validator`.
FastAPI traduce cualquier `ValidationError` en HTTP 422 automáticamente.
"""
from pydantic import BaseModel, Field, field_validator


class SolicitudPuntuacion(BaseModel):
    """Datos de entrada para puntuar una póliza."""

    poliza: str = Field(min_length=4, max_length=30, examples=["POL-2026-0413"])
    monto: float = Field(gt=0, description="Monto asegurado del siniestro; debe ser positivo.")
    antiguedad: int = Field(default=0, ge=0, description="Años de antigüedad de la póliza.")
    siniestros_previos: int = Field(ge=0, description="Número de siniestros previos.")

    @field_validator("poliza")
    @classmethod
    def limpiar_poliza(cls, valor: str) -> str:
        """Elimina espacios accidentales y rechaza una póliza vacía."""
        poliza = valor.strip()
        if not poliza:
            raise ValueError("la póliza no puede quedar vacía")
        return poliza

    @field_validator("monto")
    @classmethod
    def redondear_monto(cls, valor: float) -> float:
        """Redondea a dos decimales para evitar ruido de coma flotante.

        Nota: el validador DEBE devolver el valor; olvidar el return
        haría que todo monto valide como None.
        """
        return round(valor, 2)


class RespuestaPuntuacion(BaseModel):
    """Resultado de la evaluación."""

    poliza: str
    puntaje: float = Field(ge=0.0, le=1.0)
    alto_riesgo: bool


class Evaluacion(BaseModel):
    """Una anotación individual del historial."""

    poliza: str
    puntaje: float


class RespuestaHistorial(BaseModel):
    """Historial completo de evaluaciones realizadas."""

    evaluaciones: list[Evaluacion]


class Siniestro(BaseModel):
    """Fila del archivo de siniestros con tipos ya convertidos."""

    id: int
    poliza: str
    monto: float
    antiguedad: int
    siniestros_previos: int
    pago_alto: int


# --- Salidas de los endpoints de perfil de carga ----------------------------

class SaludRespuesta(BaseModel):
    status: str = "ok"


class PingRespuesta(BaseModel):
    pong: bool


class ConteoLineasRespuesta(BaseModel):
    lineas: int


class TarifaReferenciaRespuesta(BaseModel):
    tarifa_referencia: float


class ReservaAgregadaRespuesta(BaseModel):
    total: float
