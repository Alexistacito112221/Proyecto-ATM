"""
AutenticacionService - Subsistema de Autenticacion
SRP: Maneja la autenticacion de clientes
RF1: Autenticar mediante tarjeta y NIP
"""
from datetime import datetime
from typing import Optional, Tuple
from decimal import Decimal

from repositories.database import DatabaseManager
from repositories.tarjeta_repository import TarjetaRepository
from repositories.cuenta_repository import CuentaRepository
from repositories.cliente_repository import ClienteRepository
from services.seguridad_service import SeguridadService


class AutenticacionService:
    """Subsistema de autenticacion del cajero automatico.

    Responsabilidades:
    - Validar tarjeta (formato, expiracion, estado)
    - Verificar NIP
    - Control de intentos fallidos
    - Gestion de sesiones
    """

    def __init__(self, db: DatabaseManager = None):
        self.db = db or DatabaseManager()
        self.tarjeta_repo = TarjetaRepository(self.db)
        self.cuenta_repo = CuentaRepository(self.db)
        self.cliente_repo = ClienteRepository(self.db)
        self.seguridad = SeguridadService()

    def validar_tarjeta(self, numero_tarjeta: str) -> Tuple[bool, str, Optional[dict]]:
        """Paso 1: Validar que la tarjeta existe y esta activa"""
        # Validar formato
        valido, mensaje = self.seguridad.validar_numero_tarjeta(numero_tarjeta)
        if not valido:
            return False, mensaje, None

        # Buscar tarjeta en BD
        tarjeta = self.tarjeta_repo.obtener_por_numero(numero_tarjeta)
        if not tarjeta:
            self.seguridad.registrar_auditoria(
                self.db, "AUTH_FALLIDA", f"Tarjeta no encontrada: {self.seguridad.enmascarar_tarjeta(numero_tarjeta)}",
                resultado="TARJETA_NO_ENCONTRADA")
            return False, "Tarjeta no registrada en el sistema", None

        # Verificar estado
        if tarjeta['estado'] == 'bloqueada':
            self.seguridad.registrar_auditoria(
                self.db, "AUTH_FALLIDA", f"Tarjeta bloqueada: {tarjeta['id']}",
                tarjeta_id=tarjeta['id'], resultado="TARJETA_BLOQUEADA")
            return False, "Tarjeta bloqueada. Contacte al banco.", tarjeta

        # Verificar expiracion
        if not self.seguridad.validar_tarjeta_no_expirada(tarjeta['fecha_expiracion']):
            return False, "Tarjeta expirada. Contacte al banco.", tarjeta

        return True, "Tarjeta valida", tarjeta

    def verificar_nip(self, tarjeta_id: int, nip_ingresado: str) -> Tuple[bool, str]:
        """Paso 2: Verificar el NIP del cliente"""
        # Validar formato NIP
        valido, mensaje = self.seguridad.validar_nip(nip_ingresado)
        if not valido:
            return False, mensaje

        # Obtener tarjeta
        tarjeta = self.tarjeta_repo.obtener_por_id(tarjeta_id)
        if not tarjeta:
            return False, "Error interno: Tarjeta no encontrada"

        # Verificar NIP
        if self.seguridad.verificar_nip(nip_ingresado, tarjeta['nip_hash']):
            # NIP correcto - reiniciar intentos
            self.tarjeta_repo.reiniciar_intentos(tarjeta_id)
            self.seguridad.registrar_auditoria(
                self.db, "AUTH_EXITOSA", f"NIP correcto para tarjeta: {tarjeta_id}",
                tarjeta_id=tarjeta_id, resultado="EXITO")
            return True, "Autenticacion exitosa"
        else:
            # NIP incorrecto - incrementar intentos
            self.tarjeta_repo.incrementar_intento_fallido(tarjeta_id)
            tarjeta_actualizada = self.tarjeta_repo.obtener_por_id(tarjeta_id)
            intentos_restantes = max(0, tarjeta_actualizada['limite_intentos'] - tarjeta_actualizada['intentos_fallidos'])

            self.seguridad.registrar_auditoria(
                self.db, "AUTH_FALLIDA", f"NIP incorrecto para tarjeta: {tarjeta_id}",
                tarjeta_id=tarjeta_id, resultado="NIP_INCORRECTO")

            if tarjeta_actualizada['estado'] == 'bloqueada':
                return False, "Tarjeta bloqueada por demasiados intentos fallidos. Contacte al banco."
            return False, f"NIP incorrecto. Intentos restantes: {intentos_restantes}"

    def autenticar_completo(self, numero_tarjeta: str, nip: str) -> Tuple[bool, str, Optional[dict]]:
        """Flujo completo de autenticacion (RF1)"""
        # Paso 1: Validar tarjeta
        valido, mensaje, tarjeta = self.validar_tarjeta(numero_tarjeta)
        if not valido:
            return False, mensaje, None

        # Paso 2: Verificar NIP
        nip_valido, nip_mensaje = self.verificar_nip(tarjeta['id'], nip)
        if not nip_valido:
            return False, nip_mensaje, None

        # Paso 3: Obtener datos relacionados
        cuenta = self.cuenta_repo.obtener_por_id(tarjeta['cuenta_id'])
        cliente = self.cliente_repo.obtener_por_id(tarjeta['cliente_id'])

        if not cuenta or not cliente:
            return False, "Error: Datos de cuenta o cliente no encontrados", None

        # Verificar que la cuenta este activa
        if cuenta['estado'] != 'activa':
            return False, f"Cuenta {cuenta['estado']}. Contacte al banco.", None

        return True, f"Bienvenido, {cliente['nombre']} {cliente['apellido']}", {
            'tarjeta': tarjeta,
            'cuenta': cuenta,
            'cliente': cliente
        }

    def cambiar_nip(self, tarjeta_id: int, nip_actual: str, nip_nuevo: str,
                    nip_confirmacion: str) -> Tuple[bool, str]:
        """Cambio de NIP del cliente"""
        # Verificar que el NIP nuevo y confirmacion coincidan
        if nip_nuevo != nip_confirmacion:
            return False, "El nuevo NIP y la confirmacion no coinciden"

        # Validar NIP nuevo
        valido, mensaje = self.seguridad.validar_nip(nip_nuevo)
        if not valido:
            return False, mensaje

        # Verificar NIP actual
        nip_valido, _ = self.verificar_nip(tarjeta_id, nip_actual)
        if not nip_valido:
            return False, "NIP actual incorrecto"

        # Cambiar NIP
        nuevo_hash = self.seguridad.hash_nip(nip_nuevo)
        if self.tarjeta_repo.actualizar_nip(tarjeta_id, nuevo_hash):
            self.seguridad.registrar_auditoria(
                self.db, "CAMBIO_NIP", f"NIP cambiado para tarjeta: {tarjeta_id}",
                tarjeta_id=tarjeta_id, resultado="EXITO")
            return True, "NIP cambiado exitosamente"
        return False, "Error al actualizar el NIP"
