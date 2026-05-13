"""
Entidad Sesion - Representa una sesion de usuario en el ATM
SRP: Maneja el ciclo de vida de la sesion
"""
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional
from enum import Enum


class EstadoSesion(Enum):
    INICIADA = "iniciada"
    AUTENTICADA = "autenticada"
    EN_TRANSACCION = "en_transaccion"
    CERRADA = "cerrada"
    EXPIRADA = "expirada"
    BLOQUEADA = "bloqueada"


@dataclass
class Sesion:
    """Entidad que representa una sesion de usuario en el ATM."""
    id: str
    tarjeta_id: int = 0
    cuenta_id: int = 0
    cliente_id: int = 0
    estado: EstadoSesion = EstadoSesion.INICIADA
    fecha_inicio: datetime = field(default_factory=datetime.now)
    fecha_fin: Optional[datetime] = None
    duracion_maxima: int = 180  # 3 minutos en segundos
    tiempo_inactividad: int = 30  # 30 segundos de timeout
    ultima_actividad: datetime = field(default_factory=datetime.now)
    intentos_fallidos: int = 0
    ubicacion: str = "CAJ-001"
    ip_terminal: str = "127.0.0.1"

    def __post_init__(self):
        self.ultima_actividad = self.fecha_inicio

    def autenticar(self, tarjeta_id: int, cuenta_id: int, cliente_id: int) -> None:
        """Marca la sesion como autenticada"""
        self.tarjeta_id = tarjeta_id
        self.cuenta_id = cuenta_id
        self.cliente_id = cliente_id
        self.estado = EstadoSesion.AUTENTICADA
        self._actualizar_actividad()

    def iniciar_transaccion(self) -> None:
        self.estado = EstadoSesion.EN_TRANSACCION
        self._actualizar_actividad()

    def finalizar_transaccion(self) -> None:
        self.estado = EstadoSesion.AUTENTICADA
        self._actualizar_actividad()

    def cerrar(self) -> None:
        self.estado = EstadoSesion.CERRADA
        self.fecha_fin = datetime.now()

    def bloquear(self) -> None:
        self.estado = EstadoSesion.BLOQUEADA

    def _actualizar_actividad(self) -> None:
        self.ultima_actividad = datetime.now()

    def esta_expirada(self) -> bool:
        """Verifica si la sesion expiro por inactividad"""
        tiempo_inactivo = (datetime.now() - self.ultima_actividad).total_seconds()
        return tiempo_inactivo > self.tiempo_inactividad

    def esta_activa(self) -> bool:
        """Verifica si la sesion sigue activa"""
        if self.estado in (EstadoSesion.CERRADA, EstadoSesion.EXPIRADA, EstadoSesion.BLOQUEADA):
            return False
        if self.esta_expirada():
            self.estado = EstadoSesion.EXPIRADA
            return False
        tiempo_transcurrido = (datetime.now() - self.fecha_inicio).total_seconds()
        if tiempo_transcurrido > self.duracion_maxima:
            self.estado = EstadoSesion.EXPIRADA
            return False
        return True

    def tiempo_restante(self) -> int:
        """Retorna los segundos restantes de la sesion"""
        if not self.esta_activa():
            return 0
        tiempo_transcurrido = (datetime.now() - self.fecha_inicio).total_seconds()
        return max(0, self.duracion_maxima - int(tiempo_transcurrido))

    def incrementar_intento_fallido(self) -> None:
        self.intentos_fallidos += 1
        if self.intentos_fallidos >= 3:
            self.bloquear()

    def puede_realizar_operacion(self) -> bool:
        return (self.esta_activa() and
                self.estado in (EstadoSesion.AUTENTICADA, EstadoSesion.EN_TRANSACCION))

    def obtener_duracion(self) -> int:
        """Retorna la duracion de la sesion en segundos"""
        fin = self.fecha_fin or datetime.now()
        return int((fin - self.fecha_inicio).total_seconds())
