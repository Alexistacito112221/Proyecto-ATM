"""
Entidad Comprobante - Representa un comprobante de transaccion
SRP: Solo contiene datos del comprobante
"""
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Optional


@dataclass
class Comprobante:
    """Entidad que representa un comprobante de transaccion."""
    id: int = 0
    transaccion_id: int = 0
    numero_comprobante: str = ""
    fecha_emision: datetime = field(default_factory=datetime.now)
    tipo_transaccion: str = ""
    monto: Decimal = Decimal('0.00')
    cuenta_origen: str = ""
    cuenta_destino: Optional[str] = None
    titular: str = ""
    ubicacion_cajero: str = "CAJ-001"
    saldo_anterior: Decimal = Decimal('0.00')
    saldo_nuevo: Decimal = Decimal('0.00')
    codigo_autorizacion: str = ""
    mensaje: str = ""

    def __post_init__(self):
        if not self.numero_comprobante:
            self.numero_comprobante = self._generar_numero()

    def _generar_numero(self) -> str:
        """Genera un numero de comprobante unico"""
        timestamp = self.fecha_emision.strftime('%Y%m%d%H%M%S')
        return f"CMP-{timestamp}-{self.transaccion_id:06d}"

    def generar_texto(self) -> str:
        """Genera el texto del comprobante para impresion"""
        lineas = [
            "=" * 50,
            "     BANCO NACIONAL - COMPROBANTE",
            "=" * 50,
            f"  No. Comprobante: {self.numero_comprobante}",
            f"  Fecha: {self.fecha_emision.strftime('%d/%m/%Y %H:%M:%S')}",
            f"  Cajero: {self.ubicacion_cajero}",
            "-" * 50,
            f"  TIPO: {self.tipo_transaccion.upper()}",
            f"  CUENTA: {self._enmascarar_cuenta(self.cuenta_origen)}",
            f"  TITULAR: {self.titular}",
        ]

        if self.cuenta_destino:
            lineas.append(f"  DESTINO: {self._enmascarar_cuenta(self.cuenta_destino)}")

        lineas.extend([
            f"  MONTO: ${self.monto:,.2f}",
            "-" * 50,
            f"  Saldo Anterior: ${self.saldo_anterior:,.2f}",
            f"  Saldo Nuevo:    ${self.saldo_nuevo:,.2f}",
            f"  Cod. Autorizacion: {self.codigo_autorizacion}",
            "=" * 50,
            f"  {self.mensaje}",
            "=" * 50,
            "     Gracias por usar Banco Nacional",
            "          www.banconacional.com",
            "=" * 50,
        ])

        return "\n".join(lineas)

    @staticmethod
    def _enmascarar_cuenta(numero: str) -> str:
        """Enmascara el numero de cuenta mostrando solo los ultimos 4 digitos"""
        if len(numero) <= 4:
            return numero
        return "*" * (len(numero) - 4) + numero[-4:]

    def imprimir(self) -> str:
        """Retorna el texto del comprobante listo para 'impresion'"""
        return self.generar_texto()
