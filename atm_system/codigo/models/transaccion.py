"""
Entidad Transaccion - Representa una transaccion bancaria
SRP: Solo contiene datos de la transaccion
"""
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional


class TipoTransaccion(Enum):
    RETIRO = "retiro"
    DEPOSITO = "deposito"
    TRANSFERENCIA = "transferencia"
    CONSULTA_SALDO = "consulta_saldo"
    CAMBIO_NIP = "cambio_nip"
    PAGO = "pago"


class EstadoTransaccion(Enum):
    PENDIENTE = "pendiente"
    COMPLETADA = "completada"
    FALLIDA = "fallida"
    REVERSADA = "reversada"
    CANCELADA = "cancelada"


@dataclass
class Transaccion:
    """Entidad que representa una transaccion bancaria."""
    id: int = 0
    tipo: TipoTransaccion = TipoTransaccion.CONSULTA_SALDO
    monto: Decimal = Decimal('0.00')
    cuenta_origen_id: int = 0
    cuenta_destino_id: Optional[int] = None
    tarjeta_id: int = 0
    estado: EstadoTransaccion = EstadoTransaccion.PENDIENTE
    fecha_hora: datetime = field(default_factory=datetime.now)
    ubicacion_cajero: str = "CAJ-001"
    descripcion: str = ""
    referencia: str = ""
    codigo_autorizacion: str = ""

    def __post_init__(self):
        if self.monto < Decimal('0'):
            raise ValueError("El monto no puede ser negativo")
        if not self.referencia:
            self.referencia = self._generar_referencia()
        if not self.codigo_autorizacion:
            self.codigo_autorizacion = self._generar_codigo_autorizacion()

    def _generar_referencia(self) -> str:
        """Genera un numero de referencia unico"""
        timestamp = self.fecha_hora.strftime('%Y%m%d%H%M%S')
        return f"REF-{timestamp}-{self.cuenta_origen_id:04d}"

    def _generar_codigo_autorizacion(self) -> str:
        """Genera un codigo de autorizacion"""
        import random
        return f"AUTH-{random.randint(100000, 999999)}"

    def completar(self) -> None:
        self.estado = EstadoTransaccion.COMPLETADA

    def marcar_fallida(self, razon: str = "") -> None:
        self.estado = EstadoTransaccion.FALLIDA
        if razon:
            self.descripcion = f"FALLIDA: {razon}"

    def reversar(self) -> None:
        self.estado = EstadoTransaccion.REVERSADA

    def es_completada(self) -> bool:
        return self.estado == EstadoTransaccion.COMPLETADA

    def obtener_monto_formateado(self) -> str:
        return f"${self.monto:,.2f}"

    def obtener_fecha_formateada(self) -> str:
        return self.fecha_hora.strftime('%d/%m/%Y %H:%M:%S')

    def resumen(self) -> str:
        return (f"Transaccion: {self.tipo.value} | "
                f"Monto: {self.obtener_monto_formateado()} | "
                f"Estado: {self.estado.value} | "
                f"Referencia: {self.referencia}")
