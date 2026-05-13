"""
Capa de Datos - Patron Repository
Abstrae el acceso a datos permitiendo cambiar la BD sin afectar la logica de negocio
"""

from .database import DatabaseManager
from .cliente_repository import ClienteRepository
from .cuenta_repository import CuentaRepository
from .tarjeta_repository import TarjetaRepository
from .transaccion_repository import TransaccionRepository

__all__ = [
    'DatabaseManager',
    'ClienteRepository',
    'CuentaRepository',
    'TarjetaRepository',
    'TransaccionRepository'
]
