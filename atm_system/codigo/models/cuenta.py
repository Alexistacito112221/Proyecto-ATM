"""
Entidad Cuenta - Representa una cuenta bancaria
SRP: Solo contiene datos y reglas de negocio de la cuenta
"""
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from enum import Enum


class TipoCuenta(Enum):
    AHORROS = "ahorros"
    CORRIENTE = "corriente"


class EstadoCuenta(Enum):
    ACTIVA = "activa"
    BLOQUEADA = "bloqueada"
    INACTIVA = "inactiva"


@dataclass
class Cuenta:
    """Entidad que representa una cuenta bancaria."""
    id: int
    numero_cuenta: str
    cliente_id: int
    tipo: TipoCuenta = TipoCuenta.AHORROS
    saldo: Decimal = Decimal('0.00')
    saldo_disponible: Decimal = Decimal('0.00')
    limite_diario_retiro: Decimal = Decimal('1000.00')
    monto_retirado_hoy: Decimal = Decimal('0.00')
    estado: EstadoCuenta = EstadoCuenta.ACTIVA
    fecha_apertura: datetime = field(default_factory=datetime.now)
    sucursal: str = "Principal"

    def __post_init__(self):
        if self.saldo < Decimal('0'):
            raise ValueError("El saldo no puede ser negativo")
        if self.limite_diario_retiro <= Decimal('0'):
            raise ValueError("El limite diario debe ser positivo")

    def tiene_saldo_suficiente(self, monto: Decimal) -> bool:
        """Verifica si hay saldo suficiente para una operacion"""
        return self.saldo_disponible >= monto

    def verificar_limite_diario(self, monto: Decimal) -> bool:
        """Verifica si no excede el limite diario de retiro"""
        return (self.monto_retirado_hoy + monto) <= self.limite_diario_retiro

    def debitar(self, monto: Decimal) -> None:
        """Reduce el saldo de la cuenta"""
        if monto <= Decimal('0'):
            raise ValueError("El monto a debitar debe ser positivo")
        if not self.tiene_saldo_suficiente(monto):
            raise ValueError("Saldo insuficiente")
        self.saldo -= monto
        self.saldo_disponible -= monto

    def acreditar(self, monto: Decimal) -> None:
        """Aumenta el saldo de la cuenta"""
        if monto <= Decimal('0'):
            raise ValueError("El monto a acreditar debe ser positivo")
        self.saldo += monto
        self.saldo_disponible += monto

    def registrar_retiro(self, monto: Decimal) -> None:
        """Registra un retiro en el contador diario"""
        self.monto_retirado_hoy += monto

    def esta_activa(self) -> bool:
        return self.estado == EstadoCuenta.ACTIVA

    def bloquear(self) -> None:
        self.estado = EstadoCuenta.BLOQUEADA

    def desbloquear(self) -> None:
        self.estado = EstadoCuenta.ACTIVA

    def resetear_contador_diario(self) -> None:
        """Reinicia el contador de retiros diarios (ejecutar a medianoche)"""
        self.monto_retirado_hoy = Decimal('0.00')

    def obtener_saldo_formateado(self) -> str:
        return f"${self.saldo:,.2f}"

    def obtener_saldo_disponible_formateado(self) -> str:
        return f"${self.saldo_disponible:,.2f}"
