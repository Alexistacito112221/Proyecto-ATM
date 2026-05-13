"""
DatabaseManager - Gestiona la conexion y schema de SQLite
Patron: Singleton para una unica conexion
RNF2: Respuesta rapida con conexion local
"""
import sqlite3
import os
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from contextlib import contextmanager


class DatabaseManager:
    """Gestiona la base de datos SQLite del sistema."""

    _instance = None

    def __new__(cls, db_path: Optional[str] = None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, db_path: Optional[str] = None):
        if self._initialized:
            return
        self.db_path = db_path or os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            '..', '..', 'database', 'atm_database.db'
        )
        self._initialized = True
        self._init_database()

    @contextmanager
    def get_connection(self):
        """Context manager para conexiones seguras"""
        conn = sqlite3.connect(self.db_path, timeout=10, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def _init_database(self) -> None:
        """Inicializa el esquema de la base de datos"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Tabla Clientes
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS clientes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL,
                    apellido TEXT NOT NULL,
                    identificacion TEXT UNIQUE NOT NULL,
                    telefono TEXT,
                    email TEXT,
                    direccion TEXT,
                    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    activo INTEGER DEFAULT 1
                )
            ''')

            # Tabla Cuentas
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS cuentas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    numero_cuenta TEXT UNIQUE NOT NULL,
                    cliente_id INTEGER NOT NULL,
                    tipo TEXT DEFAULT 'ahorros',
                    saldo DECIMAL(12,2) DEFAULT 0.00,
                    saldo_disponible DECIMAL(12,2) DEFAULT 0.00,
                    limite_diario_retiro DECIMAL(12,2) DEFAULT 1000.00,
                    monto_retirado_hoy DECIMAL(12,2) DEFAULT 0.00,
                    estado TEXT DEFAULT 'activa',
                    fecha_apertura TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    sucursal TEXT DEFAULT 'Principal',
                    FOREIGN KEY (cliente_id) REFERENCES clientes(id)
                )
            ''')

            # Tabla Tarjetas
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tarjetas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    numero_tarjeta TEXT UNIQUE NOT NULL,
                    nip_hash TEXT NOT NULL,
                    fecha_expiracion DATE NOT NULL,
                    cvv TEXT NOT NULL,
                    tipo TEXT DEFAULT 'debito',
                    estado TEXT DEFAULT 'activa',
                    intentos_fallidos INTEGER DEFAULT 0,
                    limite_intentos INTEGER DEFAULT 3,
                    fecha_emision TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    cliente_id INTEGER NOT NULL,
                    cuenta_id INTEGER NOT NULL,
                    FOREIGN KEY (cliente_id) REFERENCES clientes(id),
                    FOREIGN KEY (cuenta_id) REFERENCES cuentas(id)
                )
            ''')

            # Tabla Transacciones
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS transacciones (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tipo TEXT NOT NULL,
                    monto DECIMAL(12,2) DEFAULT 0.00,
                    cuenta_origen_id INTEGER,
                    cuenta_destino_id INTEGER,
                    tarjeta_id INTEGER,
                    estado TEXT DEFAULT 'pendiente',
                    fecha_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ubicacion_cajero TEXT DEFAULT 'CAJ-001',
                    descripcion TEXT,
                    referencia TEXT UNIQUE,
                    codigo_autorizacion TEXT
                )
            ''')

            # Tabla Auditoria
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS auditoria (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tipo_evento TEXT NOT NULL,
                    descripcion TEXT,
                    usuario_id INTEGER,
                    tarjeta_id INTEGER,
                    fecha_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ubicacion TEXT DEFAULT 'CAJ-001',
                    ip_terminal TEXT,
                    resultado TEXT
                )
            ''')

            # Indices para optimizacion (RNF2 - respuesta < 3 segundos)
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_tarjetas_numero ON tarjetas(numero_tarjeta)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_cuentas_numero ON cuentas(numero_cuenta)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_transacciones_cuenta ON transacciones(cuenta_origen_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_transacciones_fecha ON transacciones(fecha_hora)')

            # Insertar datos de prueba si no existen
            self._seed_data(cursor)

    def _seed_data(self, cursor) -> None:
        """Inserta datos de prueba en la base de datos"""

        # Verificar si ya hay datos
        cursor.execute('SELECT COUNT(*) FROM clientes')
        if cursor.fetchone()[0] > 0:
            return

        # Clientes de prueba
        clientes = [
            (1, 'Juan Carlos', 'Rodriguez Perez', '1712345678', '0991234567',
             'juan.rodriguez@email.com', 'Av. Principal 123, Quito', True),
            (2, 'Maria Elena', 'Torres Castro', '1798765432', '0987654321',
             'maria.torres@email.com', 'Calle Secundaria 456, Guayaquil', True),
            (3, 'Pedro Antonio', 'Lopez Martinez', '1755556666', '0961112222',
             'pedro.lopez@email.com', 'Av. Amazonas 789, Cuenca', True),
            (4, 'Ana Lucia', 'Garcia Jimenez', '1733334444', '0973334444',
             'ana.garcia@email.com', 'Calle Bolivar 321, Ambato', True),
            (5, 'Luis Fernando', 'Vargas Diaz', '1777778888', '0957778888',
             'luis.vargas@email.com', 'Av. America 555, Manta', True),
        ]

        for c in clientes:
            cursor.execute('''
                INSERT INTO clientes (id, nombre, apellido, identificacion, telefono,
                                     email, direccion, activo)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', c)

        # Cuentas de prueba
        from decimal import Decimal
        cuentas = [
            (1, '2201234567', 1, 'ahorros', 2500.00, 2500.00, 1000.00, 0.00, 'activa', 'Principal'),
            (2, '2207654321', 2, 'corriente', 5000.00, 5000.00, 2000.00, 0.00, 'activa', 'Principal'),
            (3, '2209998888', 3, 'ahorros', 150.00, 150.00, 500.00, 0.00, 'activa', 'Norte'),
            (4, '2204445555', 4, 'ahorros', 10000.00, 10000.00, 5000.00, 0.00, 'activa', 'Sur'),
            (5, '2201112222', 5, 'corriente', 75.50, 75.50, 300.00, 0.00, 'activa', 'Centro'),
        ]

        for c in cuentas:
            cursor.execute('''
                INSERT INTO cuentas (id, numero_cuenta, cliente_id, tipo, saldo,
                                    saldo_disponible, limite_diario_retiro,
                                    monto_retirado_hoy, estado, sucursal)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', c)

        # Tarjetas de prueba (NIPs hasheados: 1234, 5678, 9012, 3456, 7890)
        import hashlib
        tarjetas = [
            (1, '4532123456789012', hashlib.sha256('1234'.encode()).hexdigest(),
             '2028-12-31', '123', 'debito', 'activa', 0, 3, 1, 1),
            (2, '4532987654321098', hashlib.sha256('5678'.encode()).hexdigest(),
             '2027-06-30', '456', 'debito', 'activa', 0, 3, 2, 2),
            (3, '4532111122223333', hashlib.sha256('9012'.encode()).hexdigest(),
             '2028-03-31', '789', 'debito', 'activa', 0, 3, 3, 3),
            (4, '4532444455556666', hashlib.sha256('3456'.encode()).hexdigest(),
             '2029-09-30', '321', 'credito', 'activa', 0, 3, 4, 4),
            (5, '4532777788889999', hashlib.sha256('7890'.encode()).hexdigest(),
             '2028-01-31', '654', 'debito', 'activa', 0, 3, 5, 5),
        ]

        for t in tarjetas:
            cursor.execute('''
                INSERT INTO tarjetas (id, numero_tarjeta, nip_hash, fecha_expiracion,
                                     cvv, tipo, estado, intentos_fallidos, limite_intentos,
                                     cliente_id, cuenta_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', t)

    def reset_database(self) -> None:
        """Reinicia la base de datos a estado inicial"""
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except:
                pass
        DatabaseManager._instance = None
        DatabaseManager(db_path=self.db_path)
