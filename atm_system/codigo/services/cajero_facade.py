"""
CajeroFacade - Fachada Principal del Sistema
Patron: Fachada (Facade) - Proporciona una interfaz unificada simplificada
Simplifica el uso de los subsistemas complejos del ATM
"""
from datetime import datetime
from typing import Tuple, Optional
from decimal import Decimal

from repositories.database import DatabaseManager
from services.seguridad_service import SeguridadService
from services.autenticacion_service import AutenticacionService
from services.transaccion_service import TransaccionService


class CajeroFacade:
    """Fachada principal del cajero automatico.

    Esta clase proporciona una interfaz unificada y simplificada
    para interactuar con todos los subsistemas del ATM:
    - Autenticacion
    - Transacciones
    - Seguridad

    Patron: Fachada (Facade Pattern)
    """

    def __init__(self):
        self.db = DatabaseManager()
        self.seguridad = SeguridadService()
        self.autenticacion = AutenticacionService(self.db)
        self.transacciones = TransaccionService(self.db)

    # ============== FLUJO DE AUTENTICACION ==============

    def iniciar_sesion(self, numero_tarjeta: str, nip: str) -> Tuple[bool, str, Optional[dict]]:
        """
        Flujo completo de autenticacion (RF1)
        Retorna: (exito, mensaje, datos_sesion)
        """
        return self.autenticacion.autenticar_completo(numero_tarjeta, nip)

    # ============== OPERACIONES BANCARIAS ==============

    def consultar_saldo(self, cuenta_id: int, tarjeta_id: int) -> Tuple[bool, str, Optional[dict]]:
        """RF2: Consulta de saldo en tiempo real"""
        return self.transacciones.consultar_saldo(cuenta_id, tarjeta_id)

    def retirar_efectivo(self, cuenta_id: int, tarjeta_id: int,
                         monto: Decimal) -> Tuple[bool, str, Optional[dict]]:
        """RF3: Retiro de efectivo con validaciones"""
        return self.transacciones.retirar_efectivo(cuenta_id, tarjeta_id, monto)

    def depositar_efectivo(self, cuenta_id: int, tarjeta_id: int,
                           monto: Decimal) -> Tuple[bool, str, Optional[dict]]:
        """Deposito de efectivo"""
        return self.transacciones.depositar_efectivo(cuenta_id, tarjeta_id, monto)

    def transferir(self, cuenta_origen_id: int, cuenta_destino_numero: str,
                   tarjeta_id: int, monto: Decimal) -> Tuple[bool, str, Optional[dict]]:
        """Transferencia entre cuentas"""
        return self.transacciones.transferir(cuenta_origen_id, cuenta_destino_numero, tarjeta_id, monto)

    def cambiar_nip(self, tarjeta_id: int, nip_actual: str,
                    nip_nuevo: str, nip_confirmacion: str) -> Tuple[bool, str]:
        """Cambio de NIP"""
        return self.autenticacion.cambiar_nip(tarjeta_id, nip_actual, nip_nuevo, nip_confirmacion)

    def obtener_historial(self, cuenta_id: int, limite: int = 10) -> Tuple[bool, str, list]:
        """Obtiene historial de transacciones"""
        return self.transacciones.obtener_historial(cuenta_id, limite)

    # ============== UTILIDADES ==============

    def validar_monto(self, monto_str: str) -> Tuple[bool, str, Decimal]:
        """Valida un monto ingresado"""
        return self.seguridad.validar_monto(monto_str)

    def formatear_comprobante(self, comprobante_data: dict, titular: str) -> str:
        """Genera el texto del comprobante"""
        from models.comprobante import Comprobante

        comp = Comprobante(
            transaccion_id=comprobante_data.get('transaccion_id', 0),
            numero_comprobante=comprobante_data.get('referencia', ''),
            tipo_transaccion=comprobante_data.get('tipo', ''),
            monto=comprobante_data.get('monto', Decimal('0')),
            cuenta_origen=comprobante_data.get('numero_cuenta',
                         comprobante_data.get('numero_cuenta_origen', '')),
            cuenta_destino=comprobante_data.get('numero_cuenta_destino'),
            titular=titular,
            saldo_anterior=comprobante_data.get('saldo_anterior', Decimal('0')),
            saldo_nuevo=comprobante_data.get('saldo_nuevo', Decimal('0')),
            codigo_autorizacion=comprobante_data.get('codigo_autorizacion', ''),
            mensaje="Transaccion completada exitosamente"
        )
        return comp.generar_texto()

    def obtener_info_cuenta(self, cuenta_id: int) -> Optional[dict]:
        """Obtiene informacion basica de una cuenta"""
        from repositories.cuenta_repository import CuentaRepository
        return CuentaRepository(self.db).obtener_por_id(cuenta_id)

    def resetear_bd(self) -> str:
        """Reinicia la base de datos a estado inicial (para pruebas)"""
        try:
            self.db.reset_database()
            return "Base de datos reiniciada exitosamente"
        except Exception as e:
            return f"Error al reiniciar BD: {str(e)}"
