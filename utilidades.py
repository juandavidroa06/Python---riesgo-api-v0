"""Utilidades transversales del servicio."""
import functools
import logging

logger = logging.getLogger("riesgo-api")


def con_registro(func):
    """Registra la ejecución en el log y PROPAGA cualquier excepción.

    Restricción B9: conserva la identidad de la función envuelta
    (functools.wraps) y jamás captura un fallo para devolver None.
    """
    @functools.wraps(func)
    def envoltura(*args, **kwargs):
        logger.info("ejecutando %s", func.__name__)
        return func(*args, **kwargs)
    return envoltura
