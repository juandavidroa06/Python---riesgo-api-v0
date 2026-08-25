"""Lógica de dominio: evaluación de riesgo de pólizas (restricción B4).

Todo el estado vive en instancias, nunca en atributos de clase mutables ni
en variables globales.
"""
import csv
from pathlib import Path
from typing import Any, Optional

import config
from utilidades import con_registro


class RegistroEvaluaciones:
    """Acumula las evaluaciones hechas por todos los evaluadores."""

    def __init__(self):
        self._evaluaciones: list[dict[str, Any]] = []

    def agregar(self, evaluacion: dict[str, Any]) -> None:
        self._evaluaciones.append(dict(evaluacion))

    def todas(self) -> list[dict[str, Any]]:
        return [dict(evaluacion) for evaluacion in self._evaluaciones]


class RepositorioSiniestros:
    """Acceso de lectura al archivo de siniestros, cargado una sola vez."""

    def __init__(self, ruta_datos: Optional[Path] = None):
        self._ruta_datos = (
            Path(ruta_datos)
            if ruta_datos is not None
            else Path(__file__).parent / config.RUTA_DATOS
        )
        self._filas: list[dict[str, Any]] = []
        self._indice: dict[int, dict[str, Any]] = {}
        self._cargar()

    def _cargar(self) -> None:
        with open(self._ruta_datos, encoding="utf-8") as fh:
            for fila in csv.DictReader(fh):
                fila_limpia = {
                    "id": int(fila["id"]),
                    "poliza": fila["poliza"],
                    "monto": float(fila["monto"]),
                    "antiguedad": int(fila["antiguedad"]),
                    "siniestros_previos": int(fila["siniestros_previos"]),
                    "pago_alto": int(fila["pago_alto"]),
                }
                self._filas.append(fila_limpia)
                self._indice[fila_limpia["id"]] = fila_limpia

    def obtener(self, id_siniestro: int) -> Optional[dict[str, Any]]:
        return self._indice.get(id_siniestro)

    def todos(self) -> list[dict[str, Any]]:
        return list(self._filas)


class EvaluadorRiesgo:
    """Evalúa el riesgo de una póliza y guarda sus propias anotaciones.

    Puede construirse solo con la póliza — contrato fijo del taller:

        EvaluadorRiesgo("POL-2026-0413")

    Los colaboradores (modelo, registro) van como argumentos opcionales.
    """

    def __init__(
        self,
        poliza: str,
        modelo=None,
        registro: Optional[RegistroEvaluaciones] = None,
        umbral: Optional[float] = None,
    ):
        self.poliza = poliza
        self.modelo = modelo
        self.registro = registro
        # El historial es de la INSTANCIA: dos evaluadores no comparten estado.
        self.historial: list[dict[str, Any]] = []
        self.umbral = config.UMBRAL_ALTO_RIESGO if umbral is None else umbral

    @con_registro
    def puntuar(self, payload: dict[str, Any]) -> float:
        if self.modelo is None:
            raise RuntimeError(f"el evaluador de {self.poliza} no tiene modelo asignado")
        rasgos = [[
            payload["monto"],
            payload["antiguedad"],
            payload["siniestros_previos"],
        ]]
        return float(self.modelo.predict_proba(rasgos)[0][1])

    def anotar(self, puntaje: float) -> None:
        entrada = {"poliza": self.poliza, "puntaje": puntaje}
        self.historial.append(entrada)
        if self.registro is not None:
            self.registro.agregar(entrada)

    def es_alto_riesgo(self, puntaje: Optional[float]) -> bool:
        return puntaje is not None and puntaje > self.umbral
