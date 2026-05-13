"""
TarjetaRepository - Patron Repository para Tarjetas
"""
from typing import Optional, List
from .database import DatabaseManager


class TarjetaRepository:
    """Repositorio para operaciones CRUD de Tarjetas."""

    def __init__(self, db: DatabaseManager = None):
        self.db = db or DatabaseManager()

    def obtener_por_id(self, tarjeta_id: int) -> Optional[dict]:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM tarjetas WHERE id = ?', (tarjeta_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def obtener_por_numero(self, numero_tarjeta: str) -> Optional[dict]:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM tarjetas WHERE numero_tarjeta = ?', (numero_tarjeta,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def obtener_por_cliente(self, cliente_id: int) -> List[dict]:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM tarjetas WHERE cliente_id = ?', (cliente_id,))
            return [dict(row) for row in cursor.fetchall()]

    def actualizar_nip(self, tarjeta_id: int, nuevo_nip_hash: str) -> bool:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE tarjetas SET nip_hash = ?, intentos_fallidos = 0
                WHERE id = ?
            ''', (nuevo_nip_hash, tarjeta_id))
            return cursor.rowcount > 0

    def incrementar_intento_fallido(self, tarjeta_id: int) -> bool:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE tarjetas
                SET intentos_fallidos = intentos_fallidos + 1,
                    estado = CASE WHEN intentos_fallidos + 1 >= limite_intentos
                                  THEN 'bloqueada' ELSE estado END
                WHERE id = ?
            ''', (tarjeta_id,))
            return cursor.rowcount > 0

    def reiniciar_intentos(self, tarjeta_id: int) -> bool:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE tarjetas SET intentos_fallidos = 0 WHERE id = ?', (tarjeta_id,))
            return cursor.rowcount > 0

    def bloquear(self, tarjeta_id: int) -> bool:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE tarjetas SET estado = "bloqueada" WHERE id = ?', (tarjeta_id,))
            return cursor.rowcount > 0

    def listar_todas(self) -> List[dict]:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM tarjetas')
            return [dict(row) for row in cursor.fetchall()]
