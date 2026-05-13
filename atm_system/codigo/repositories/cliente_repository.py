"""
ClienteRepository - Patron Repository para Clientes
Separa la logica de acceso a datos de la logica de negocio
"""
from typing import Optional, List
from .database import DatabaseManager


class ClienteRepository:
    """Repositorio para operaciones CRUD de Clientes."""

    def __init__(self, db: DatabaseManager = None):
        self.db = db or DatabaseManager()

    def obtener_por_id(self, cliente_id: int) -> Optional[dict]:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT * FROM clientes WHERE id = ?', (cliente_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def obtener_por_identificacion(self, identificacion: str) -> Optional[dict]:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT * FROM clientes WHERE identificacion = ?', (identificacion,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def listar_todos(self) -> List[dict]:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM clientes WHERE activo = 1')
            return [dict(row) for row in cursor.fetchall()]

    def crear(self, cliente_data: dict) -> int:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO clientes (nombre, apellido, identificacion, telefono,
                                     email, direccion, activo)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                cliente_data['nombre'], cliente_data['apellido'],
                cliente_data['identificacion'], cliente_data.get('telefono', ''),
                cliente_data.get('email', ''), cliente_data.get('direccion', ''),
                1
            ))
            return cursor.lastrowid
