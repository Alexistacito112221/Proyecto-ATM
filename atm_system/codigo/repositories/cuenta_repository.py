"""
CuentaRepository - Patron Repository para Cuentas
"""
from typing import Optional, List
from decimal import Decimal
from .database import DatabaseManager


class CuentaRepository:
    """Repositorio para operaciones CRUD de Cuentas."""

    def __init__(self, db: DatabaseManager = None):
        self.db = db or DatabaseManager()

    def obtener_por_id(self, cuenta_id: int) -> Optional[dict]:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM cuentas WHERE id = ?', (cuenta_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def obtener_por_numero(self, numero_cuenta: str) -> Optional[dict]:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM cuentas WHERE numero_cuenta = ?', (numero_cuenta,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def obtener_por_cliente(self, cliente_id: int) -> List[dict]:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM cuentas WHERE cliente_id = ?', (cliente_id,))
            return [dict(row) for row in cursor.fetchall()]

    def actualizar_saldo(self, cuenta_id: int, nuevo_saldo: Decimal,
                         nuevo_saldo_disponible: Decimal) -> bool:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE cuentas SET saldo = ?, saldo_disponible = ?
                WHERE id = ?
            ''', (float(nuevo_saldo), float(nuevo_saldo_disponible), cuenta_id))
            return cursor.rowcount > 0

    def registrar_retiro_diario(self, cuenta_id: int, monto: Decimal) -> bool:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE cuentas SET monto_retirado_hoy = monto_retirado_hoy + ?
                WHERE id = ?
            ''', (float(monto), cuenta_id))
            return cursor.rowcount > 0

    def resetear_retiros_diarios(self) -> None:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE cuentas SET monto_retirado_hoy = 0')

    def listar_todas(self) -> List[dict]:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM cuentas WHERE estado = "activa"')
            return [dict(row) for row in cursor.fetchall()]

    def bloquear(self, cuenta_id: int) -> bool:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE cuentas SET estado = "bloqueada" WHERE id = ?', (cuenta_id,))
            return cursor.rowcount > 0
