"""Configuración del servicio.

Los secretos NO viven en el código (restricción B1): llegan por variables
de entorno — ver `.env.example`. Ningún valor sensible se versiona.
"""
import os

UMBRAL_ALTO_RIESGO = float(os.environ.get("RIESGO_UMBRAL_ALTO_RIESGO", "0.7"))
RUTA_MODELO = os.environ.get("RIESGO_RUTA_MODELO", "modelo.pkl")
RUTA_DATOS = os.environ.get("RIESGO_RUTA_DATOS", "datos/siniestros.csv")

# Secretos por entorno: solo existen si el despliegue los inyecta.
API_KEY = os.environ.get("RIESGO_API_KEY")
CLAVE_FIRMA = os.environ.get("RIESGO_CLAVE_FIRMA")
