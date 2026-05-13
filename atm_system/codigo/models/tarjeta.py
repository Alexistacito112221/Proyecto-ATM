"""
Entidad Tarjeta - Representa una tarjeta de debito/credito
SRP: Solo contiene datos y validaciones de la tarjeta
"""
from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional
import hashlib
import re


@dataclass
class Tarjeta:
    """Entidad que representa una tarjeta bancaria."""
    id: int
    numero_tarjeta: str
    nip_hash: str
    fecha_expiracion: date
    cvv: str
    tipo: str  # 'debito', 'credito'
    estado: str = 'activa'  # 'activa', 'bloqueada', 'expirada'
    intentos_fallidos: int = 0
    limite_intentos: int = 3
    fecha_emision: datetime = field(default_factory=datetime.now)
    cliente_id: int = 0
    cuenta_id: int = 0

    def __post_init__(self):
        if not self._validar_numero_tarjeta(self.numero_tarjeta):
            raise ValueError("Numero de tarjeta invalido (debe tener 16 digitos)")
        if self.intentos_fallidos < 0:
            raise ValueError("Intentos fallidos no puede ser negativo")

    @staticmethod
    def _validar_numero_tarjeta(numero: str) -> bool:
        """Validacion basica de tarjeta (16 digitos)"""
        return bool(re.match(r'^[0-9]{16}$', numero))

    @staticmethod
    def hash_nip(nip: str) -> str:
        """Cifra el NIP usando SHA-256 (simulacion de cifrado seguro)"""
        return hashlib.sha256(nip.encode()).hexdigest()

    def verificar_nip(self, nip: str) -> bool:
        """Verifica si el NIP proporcionado es correcto"""
        return self.nip_hash == self.hash_nip(nip)

    def esta_bloqueada(self) -> bool:
        return self.estado == 'bloqueada'

    def esta_expirada(self) -> bool:
        return date.today() > self.fecha_expiracion

    def esta_activa(self) -> bool:
        return self.estado == 'activa' and not self.esta_expirada()

    def incrementar_intento_fallido(self) -> None:
        self.intentos_fallidos += 1
        if self.intentos_fallidos >= self.limite_intentos:
            self.estado = 'bloqueada'

    def reiniciar_intentos(self) -> None:
        self.intentos_fallidos = 0

    def formatear_numero(self) -> str:
        """Muestra solo los ultimos 4 digitos por seguridad"""
        return f"****-****-****-{self.numero_tarjeta[-4:]}"

    def cambiar_nip(self, nuevo_nip: str) -> None:
        """Cambia el NIP del cliente"""
        if not self._validar_nip(nuevo_nip):
            raise ValueError("NIP invalido: debe ser de 4 digitos numericos")
        self.nip_hash = self.hash_nip(nuevo_nip)
        self.reiniciar_intentos()

    @staticmethod
    def _validar_nip(nip: str) -> bool:
        return bool(re.match(r'^[0-9]{4}$', nip))

    def obtener_numero_mostrable(self) -> str:
        """Retorna numero formateado para mostrar en interfaz"""
        return self.formatear_numero()
