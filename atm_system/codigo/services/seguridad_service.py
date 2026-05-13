"""
SeguridadService - Subsistema de Seguridad
SRP: Maneja todas las operaciones relacionadas con seguridad
RNF4: Cifrado de datos durante la transmision
"""
import hashlib
import re
from datetime import datetime
from typing import Optional, Tuple
from decimal import Decimal


class SeguridadService:
    """Subsistema de seguridad del cajero automatico.

    Responsabilidades:
    - Cifrado y hash de datos sensibles
    - Validacion de formatos (tarjeta, NIP, etc.)
    - Control de intentos fallidos
    - Auditoria de eventos de seguridad
    """

    @staticmethod
    def hash_nip(nip: str) -> str:
        """Genera hash SHA-256 del NIP (RNF4 - cifrado)"""
        return hashlib.sha256(nip.encode()).hexdigest()

    @staticmethod
    def verificar_nip(nip_ingresado: str, nip_hash_almacenado: str) -> bool:
        """Verifica si el NIP ingresado coincide con el hash almacenado"""
        return SeguridadService.hash_nip(nip_ingresado) == nip_hash_almacenado

    @staticmethod
    def validar_nip(nip: str) -> Tuple[bool, str]:
        """Valida el formato del NIP (4 digitos numericos)"""
        if not nip:
            return False, "El NIP no puede estar vacio"
        if not re.match(r'^[0-9]{4}$', nip):
            return False, "El NIP debe ser exactamente 4 digitos numericos"
        return True, "NIP valido"

    @staticmethod
    def validar_numero_tarjeta(numero: str) -> Tuple[bool, str]:
        """Valida el formato del numero de tarjeta (16 digitos)"""
        if not numero:
            return False, "El numero de tarjeta no puede estar vacio"
        if not re.match(r'^[0-9]{16}$', numero):
            return False, "El numero de tarjeta debe tener 16 digitos numericos"
        return True, "Tarjeta valida"

    @staticmethod
    def validar_monto(monto: str) -> Tuple[bool, str, Decimal]:
        """Valida que el monto sea un numero positivo valido"""
        try:
            monto_decimal = Decimal(str(monto))
            if monto_decimal <= Decimal('0'):
                return False, "El monto debe ser mayor a cero", Decimal('0')
            if monto_decimal > Decimal('50000'):
                return False, "El monto maximo por transaccion es $50,000", Decimal('0')
            # Validar maximo 2 decimales
            if monto_decimal != monto_decimal.quantize(Decimal('0.01')):
                return False, "El monto no puede tener mas de 2 decimales", Decimal('0')
            return True, "Monto valido", monto_decimal
        except:
            return False, "Monto invalido. Ingrese un numero valido", Decimal('0')

    @staticmethod
    def enmascarar_tarjeta(numero: str) -> str:
        """Enmascara el numero de tarjeta mostrando solo los ultimos 4 digitos"""
        if len(numero) <= 4:
            return numero
        return f"****-****-****-{numero[-4:]}"

    @staticmethod
    def enmascarar_cuenta(numero: str) -> str:
        """Enmascara el numero de cuenta"""
        if len(numero) <= 4:
            return numero
        return "*" * (len(numero) - 4) + numero[-4:]

    @staticmethod
    def generar_codigo_autorizacion() -> str:
        """Genera un codigo de autorizacion unico"""
        import random
        timestamp = datetime.now().strftime('%H%M%S')
        random_part = random.randint(1000, 9999)
        return f"AUTH-{timestamp}-{random_part}"

    @staticmethod
    def generar_referencia_transaccion(cuenta_id: int) -> str:
        """Genera un numero de referencia unico para transacciones"""
        import random
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        random_part = random.randint(1000, 9999)
        return f"REF-{timestamp}-{cuenta_id:04d}-{random_part}"

    @staticmethod
    def validar_tarjeta_no_expirada(fecha_expiracion: str) -> bool:
        """Verifica que la tarjeta no haya expirado"""
        try:
            from datetime import date
            exp_date = datetime.strptime(fecha_expiracion, '%Y-%m-%d').date()
            return date.today() <= exp_date
        except:
            return False

    @staticmethod
    def registrar_auditoria(db, tipo_evento: str, descripcion: str,
                            usuario_id: int = None, tarjeta_id: int = None,
                            resultado: str = "") -> None:
        """Registra eventos de auditoria para trazabilidad"""
        try:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO auditoria
                    (tipo_evento, descripcion, usuario_id, tarjeta_id, resultado)
                    VALUES (?, ?, ?, ?, ?)
                ''', (tipo_evento, descripcion, usuario_id, tarjeta_id, resultado))
        except Exception:
            pass  # No fallar por errores de auditoria

    @staticmethod
    def verificar_integridad_datos(datos: dict) -> Tuple[bool, str]:
        """Verifica la integridad basica de los datos"""
        if not datos:
            return False, "Datos vacios"
        return True, "Datos integros"
