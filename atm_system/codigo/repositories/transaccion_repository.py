"""
TransaccionRepository - Patron Repository para Transacciones
"""
from typing import Optional, List
from decimal import Decimal
from .database import DatabaseManager


class TransaccionRepository:
    """Repositorio para operaciones CRUD de Transacciones."""

    def __init__(self, db: DatabaseManager = None):
        self.db = db or DatabaseManager()

    def crear(self, trans_data: dict) -> int:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO transacciones
                (tipo, monto, cuenta_origen_id, cuenta_destino_id, tarjeta_id,
                 estado, ubicacion_cajero, descripcion, referencia, codigo_autorizacion)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                trans_data['tipo'], float(trans_data.get('monto', 0)),
                trans_data.get('cuenta_origen_id'),
                trans_data.get('cuenta_destino_id'),
                trans_data.get('tarjeta_id'),
                trans_data.get('estado', 'pendiente'),
                trans_data.get('ubicacion_cajero', 'CAJ-001'),
                trans_data.get('descripcion', ''),
                trans_data['referencia'],
                trans_data['codigo_autorizacion']
            ))
            return cursor.lastrowid

    def obtener_por_id(self, trans_id: int) -> Optional[dict]:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM transacciones WHERE id = ?', (trans_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def listar_por_cuenta(self, cuenta_id: int, limite: int = 10) -> List[dict]:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM transacciones
                WHERE cuenta_origen_id = ? OR cuenta_destino_id = ?
                ORDER BY fecha_hora DESC
                LIMIT ?
            ''', (cuenta_id, cuenta_id, limite))
            return [dict(row) for row in cursor.fetchall()]

    def actualizar_estado(self, trans_id: int, estado: str, descripcion: str = '') -> bool:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            if descripcion:
                cursor.execute('''
                    UPDATE transacciones SET estado = ?, descripcion = ?
                    WHERE id = ?
                ''', (estado, descripcion, trans_id))
            else:
                cursor.execute(
                    'UPDATE transacciones SET estado = ? WHERE id = ?', (estado, trans_id))
            return cursor.rowcount > 0

    def listar_todas(self, limite: int = 100) -> List[dict]:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT * FROM transacciones ORDER BY fecha_hora DESC LIMIT ?', (limite,))
            return [dict(row) for row in cursor.fetchall()]
