"""
Entidad Cliente - Representa un cliente del banco
SRP: Solo contiene datos y validaciones del cliente
"""
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime
import re


@dataclass
class Cliente:
    """Entidad que representa un cliente del banco."""
    id: int
    nombre: str
    apellido: str
    identificacion: str
    telefono: str
    email: str
    direccion: str
    fecha_registro: datetime = field(default_factory=datetime.now)
    activo: bool = True

    def __post_init__(self):
        """Validaciones del dominio"""
        if not self.nombre or len(self.nombre.strip()) < 2:
            raise ValueError("El nombre debe tener al menos 2 caracteres")
        if not self.apellido or len(self.apellido.strip()) < 2:
            raise ValueError("El apellido debe tener al menos 2 caracteres")
        if not self._validar_identificacion(self.identificacion):
            raise ValueError("Identificacion invalida")
        if not self._validar_email(self.email):
            raise ValueError("Email invalido")

    @staticmethod
    def _validar_identificacion(identificacion: str) -> bool:
        return bool(re.match(r'^[0-9]{10,13}$', identificacion))

    @staticmethod
    def _validar_email(email: str) -> bool:
        patron = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(patron, email))

    @property
    def nombre_completo(self) -> str:
        return f"{self.nombre} {self.apellido}"

    def esta_activo(self) -> bool:
        return self.activo
