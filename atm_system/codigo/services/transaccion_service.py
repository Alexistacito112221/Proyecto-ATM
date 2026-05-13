"""
TransaccionService - Subsistema de Transacciones
SRP: Maneja todas las operaciones financieras
RF2: Consulta saldo | RF3: Retiro | RF4: Validacion | RF5: Registro
"""
from datetime import datetime
from typing import Tuple, Optional
from decimal import Decimal

from repositories.database import DatabaseManager
from repositories.transaccion_repository import TransaccionRepository
from repositories.cuenta_repository import CuentaRepository
from repositories.tarjeta_repository import TarjetaRepository
from services.seguridad_service import SeguridadService


class TransaccionService:
    """Subsistema de transacciones del cajero automatico.

    Responsabilidades:
    - Consulta de saldo
    - Retiro de efectivo
    - Deposito de efectivo
    - Transferencia entre cuentas
    - Registro de transacciones (RF5)
    """

    def __init__(self, db: DatabaseManager = None):
        self.db = db or DatabaseManager()
        self.trans_repo = TransaccionRepository(self.db)
        self.cuenta_repo = CuentaRepository(self.db)
        self.tarjeta_repo = TarjetaRepository(self.db)
        self.seguridad = SeguridadService()

    # ============== RF2: CONSULTA DE SALDO ==============

    def consultar_saldo(self, cuenta_id: int, tarjeta_id: int) -> Tuple[bool, str, Optional[dict]]:
        """Consulta el saldo de la cuenta en tiempo real"""
        try:
            cuenta = self.cuenta_repo.obtener_por_id(cuenta_id)
            if not cuenta:
                return False, "Cuenta no encontrada", None

            # Registrar transaccion de consulta
            trans_data = {
                'tipo': 'consulta_saldo',
                'monto': Decimal('0'),
                'cuenta_origen_id': cuenta_id,
                'tarjeta_id': tarjeta_id,
                'estado': 'completada',
                'ubicacion_cajero': 'CAJ-001',
                'descripcion': 'Consulta de saldo',
                'referencia': self.seguridad.generar_referencia_transaccion(cuenta_id),
                'codigo_autorizacion': self.seguridad.generar_codigo_autorizacion()
            }
            self.trans_repo.crear(trans_data)

            saldo_info = {
                'saldo': Decimal(str(cuenta['saldo'])),
                'saldo_disponible': Decimal(str(cuenta['saldo_disponible'])),
                'tipo_cuenta': cuenta['tipo'],
                'numero_cuenta': cuenta['numero_cuenta'],
                'limite_diario': Decimal(str(cuenta['limite_diario_retiro'])),
                'retirado_hoy': Decimal(str(cuenta['monto_retirado_hoy']))
            }

            return True, "Consulta exitosa", saldo_info

        except Exception as e:
            return False, f"Error al consultar saldo: {str(e)}", None

    # ============== RF3: RETIRO DE EFECTIVO ==============

    def retirar_efectivo(self, cuenta_id: int, tarjeta_id: int,
                         monto: Decimal) -> Tuple[bool, str, Optional[dict]]:
        """
        Retiro de efectivo - Caso de uso principal
        Valida: saldo suficiente, limite diario, cuenta activa
        """
        try:
            # Validar monto positivo
            if monto <= Decimal('0'):
                return self._retiro_fallido(cuenta_id, tarjeta_id, monto, "El monto debe ser mayor a cero")

            # Obtener cuenta
            cuenta = self.cuenta_repo.obtener_por_id(cuenta_id)
            if not cuenta:
                return self._retiro_fallido(cuenta_id, tarjeta_id, monto, "Cuenta no encontrada")

            saldo = Decimal(str(cuenta['saldo_disponible']))
            limite_diario = Decimal(str(cuenta['limite_diario_retiro']))
            retirado_hoy = Decimal(str(cuenta['monto_retirado_hoy']))

            # Validar saldo suficiente
            if saldo < monto:
                return self._retiro_fallido(cuenta_id, tarjeta_id, monto,
                                           f"Saldo insuficiente. Disponible: ${saldo:,.2f}")

            # Validar limite diario
            if (retirado_hoy + monto) > limite_diario:
                disponible = limite_diario - retirado_hoy
                return self._retiro_fallido(cuenta_id, tarjeta_id, monto,
                                           f"Excede limite diario. Disponible hoy: ${disponible:,.2f}")

            # Validar cuenta activa
            if cuenta['estado'] != 'activa':
                return self._retiro_fallido(cuenta_id, tarjeta_id, monto,
                                           f"Cuenta {cuenta['estado']}")

            # Generar referencia
            referencia = self.seguridad.generar_referencia_transaccion(cuenta_id)
            codigo_auth = self.seguridad.generar_codigo_autorizacion()

            # Crear transaccion pendiente
            trans_data = {
                'tipo': 'retiro',
                'monto': monto,
                'cuenta_origen_id': cuenta_id,
                'tarjeta_id': tarjeta_id,
                'estado': 'pendiente',
                'ubicacion_cajero': 'CAJ-001',
                'descripcion': f'Retiro de efectivo',
                'referencia': referencia,
                'codigo_autorizacion': codigo_auth
            }
            trans_id = self.trans_repo.crear(trans_data)

            # Actualizar saldo
            nuevo_saldo = Decimal(str(cuenta['saldo'])) - monto
            nuevo_saldo_disp = Decimal(str(cuenta['saldo_disponible'])) - monto

            if self.cuenta_repo.actualizar_saldo(cuenta_id, nuevo_saldo, nuevo_saldo_disp):
                # Registrar retiro diario
                self.cuenta_repo.registrar_retiro_diario(cuenta_id, monto)

                # Actualizar transaccion a completada
                self.trans_repo.actualizar_estado(trans_id, 'completada')

                # Generar comprobante
                comprobante = {
                    'transaccion_id': trans_id,
                    'tipo': 'retiro',
                    'monto': monto,
                    'numero_cuenta': cuenta['numero_cuenta'],
                    'saldo_anterior': Decimal(str(cuenta['saldo'])),
                    'saldo_nuevo': nuevo_saldo,
                    'codigo_autorizacion': codigo_auth,
                    'referencia': referencia
                }

                self.seguridad.registrar_auditoria(
                    self.db, "RETIRO", f"Retiro exitoso: ${monto:,.2f} - Ref: {referencia}",
                    tarjeta_id=tarjeta_id, resultado="EXITO")

                return True, f"Retiro exitoso. Por favor retire su efectivo.", comprobante
            else:
                self.trans_repo.actualizar_estado(trans_id, 'fallida', "Error al actualizar saldo")
                return False, "Error interno al procesar el retiro", None

        except Exception as e:
            return False, f"Error en retiro: {str(e)}", None

    def _retiro_fallido(self, cuenta_id: int, tarjeta_id: int,
                        monto: Decimal, razon: str) -> Tuple[bool, str, None]:
        """Registra un retiro fallido y retorna respuesta"""
        try:
            referencia = self.seguridad.generar_referencia_transaccion(cuenta_id)
            trans_data = {
                'tipo': 'retiro',
                'monto': monto,
                'cuenta_origen_id': cuenta_id,
                'tarjeta_id': tarjeta_id,
                'estado': 'fallida',
                'descripcion': f'Retiro fallido: {razon}',
                'referencia': referencia,
                'codigo_autorizacion': self.seguridad.generar_codigo_autorizacion()
            }
            self.trans_repo.crear(trans_data)
        except:
            pass
        return False, razon, None

    # ============== DEPOSITO DE EFECTIVO ==============

    def depositar_efectivo(self, cuenta_id: int, tarjeta_id: int,
                           monto: Decimal) -> Tuple[bool, str, Optional[dict]]:
        """Deposito de efectivo en cuenta"""
        try:
            cuenta = self.cuenta_repo.obtener_por_id(cuenta_id)
            if not cuenta:
                return False, "Cuenta no encontrada", None

            if cuenta['estado'] != 'activa':
                return False, f"Cuenta {cuenta['estado']}", None

            referencia = self.seguridad.generar_referencia_transaccion(cuenta_id)
            codigo_auth = self.seguridad.generar_codigo_autorizacion()

            trans_data = {
                'tipo': 'deposito',
                'monto': monto,
                'cuenta_origen_id': cuenta_id,
                'tarjeta_id': tarjeta_id,
                'estado': 'pendiente',
                'descripcion': 'Deposito de efectivo',
                'referencia': referencia,
                'codigo_autorizacion': codigo_auth
            }
            trans_id = self.trans_repo.crear(trans_data)

            nuevo_saldo = Decimal(str(cuenta['saldo'])) + monto
            nuevo_saldo_disp = Decimal(str(cuenta['saldo_disponible'])) + monto

            if self.cuenta_repo.actualizar_saldo(cuenta_id, nuevo_saldo, nuevo_saldo_disp):
                self.trans_repo.actualizar_estado(trans_id, 'completada')

                comprobante = {
                    'transaccion_id': trans_id,
                    'tipo': 'deposito',
                    'monto': monto,
                    'numero_cuenta': cuenta['numero_cuenta'],
                    'saldo_anterior': Decimal(str(cuenta['saldo'])),
                    'saldo_nuevo': nuevo_saldo,
                    'codigo_autorizacion': codigo_auth,
                    'referencia': referencia
                }
                return True, "Deposito exitoso", comprobante
            else:
                self.trans_repo.actualizar_estado(trans_id, 'fallida')
                return False, "Error al procesar el deposito", None

        except Exception as e:
            return False, f"Error en deposito: {str(e)}", None

    # ============== TRANSFERENCIA ENTRE CUENTAS ==============

    def transferir(self, cuenta_origen_id: int, cuenta_destino_numero: str,
                   tarjeta_id: int, monto: Decimal) -> Tuple[bool, str, Optional[dict]]:
        """Transferencia entre cuentas del mismo banco"""
        try:
            # Validar que no sea la misma cuenta
            cuenta_origen = self.cuenta_repo.obtener_por_id(cuenta_origen_id)
            if not cuenta_origen:
                return False, "Cuenta origen no encontrada", None

            if cuenta_origen['numero_cuenta'] == cuenta_destino_numero:
                return False, "No puede transferir a la misma cuenta", None

            # Buscar cuenta destino
            cuenta_destino = self.cuenta_repo.obtener_por_numero(cuenta_destino_numero)
            if not cuenta_destino:
                return False, "Cuenta destino no encontrada", None

            if cuenta_destino['estado'] != 'activa':
                return False, "Cuenta destino no esta activa", None

            # Verificar saldo suficiente
            saldo_origen = Decimal(str(cuenta_origen['saldo_disponible']))
            if saldo_origen < monto:
                return False, f"Saldo insuficiente. Disponible: ${saldo_origen:,.2f}", None

            # Ejecutar transferencia
            nuevo_saldo_origen = Decimal(str(cuenta_origen['saldo'])) - monto
            nuevo_saldo_origen_disp = Decimal(str(cuenta_origen['saldo_disponible'])) - monto
            nuevo_saldo_destino = Decimal(str(cuenta_destino['saldo'])) + monto
            nuevo_saldo_destino_disp = Decimal(str(cuenta_destino['saldo_disponible'])) + monto

            referencia = self.seguridad.generar_referencia_transaccion(cuenta_origen_id)
            codigo_auth = self.seguridad.generar_codigo_autorizacion()

            # Crear transaccion
            trans_data = {
                'tipo': 'transferencia',
                'monto': monto,
                'cuenta_origen_id': cuenta_origen_id,
                'cuenta_destino_id': cuenta_destino['id'],
                'tarjeta_id': tarjeta_id,
                'estado': 'completada',
                'descripcion': f"Transferencia a {cuenta_destino_numero}",
                'referencia': referencia,
                'codigo_autorizacion': codigo_auth
            }
            trans_id = self.trans_repo.crear(trans_data)

            # Actualizar ambas cuentas
            self.cuenta_repo.actualizar_saldo(cuenta_origen_id, nuevo_saldo_origen, nuevo_saldo_origen_disp)
            self.cuenta_repo.actualizar_saldo(cuenta_destino['id'], nuevo_saldo_destino, nuevo_saldo_destino_disp)

            comprobante = {
                'transaccion_id': trans_id,
                'tipo': 'transferencia',
                'monto': monto,
                'numero_cuenta_origen': cuenta_origen['numero_cuenta'],
                'numero_cuenta_destino': cuenta_destino['numero_cuenta'],
                'saldo_anterior': Decimal(str(cuenta_origen['saldo'])),
                'saldo_nuevo': nuevo_saldo_origen,
                'codigo_autorizacion': codigo_auth,
                'referencia': referencia
            }

            return True, f"Transferencia exitosa a cuenta {self.seguridad.enmascarar_cuenta(cuenta_destino_numero)}", comprobante

        except Exception as e:
            return False, f"Error en transferencia: {str(e)}", None

    # ============== HISTORIAL DE TRANSACCIONES ==============

    def obtener_historial(self, cuenta_id: int, limite: int = 10) -> Tuple[bool, str, list]:
        """Obtiene el historial de transacciones de una cuenta"""
        try:
            transacciones = self.trans_repo.listar_por_cuenta(cuenta_id, limite)
            return True, f"{len(transacciones)} transacciones encontradas", transacciones
        except Exception as e:
            return False, f"Error al obtener historial: {str(e)}", []
