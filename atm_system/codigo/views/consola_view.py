"""
ConsolaView - Interfaz de usuario por consola
Simula la pantalla tactil del cajero automatico
RNF3: Accesible con instrucciones claras
"""
import os
import sys
from decimal import Decimal
from typing import Optional

# Agregar raiz del proyecto al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from services.cajero_facade import CajeroFacade


class ConsolaView:
    """Interfaz de usuario por consola que simula un ATM."""

    def __init__(self):
        self.facade = CajeroFacade()
        self.sesion_activa = False
        self.datos_sesion = None
        self.ANCHO = 60

    def limpiar_pantalla(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def linea(self, char='='):
        print(char * self.ANCHO)

    def centrar(self, texto):
        espacios = (self.ANCHO - len(texto)) // 2
        return ' ' * espacios + texto

    def mostrar_encabezado(self, titulo):
        self.limpiar_pantalla()
        self.linea()
        print(self.centrar("BANCO NACIONAL"))
        print(self.centrar("CAJERO AUTOMATICO"))
        self.linea()
        if titulo:
            print(self.centrar(titulo))
            self.linea('-')

    def mostrar_error(self, mensaje):
        print(f"\n  [ERROR] {mensaje}")
        input("\n  Presione ENTER para continuar...")

    def mostrar_exito(self, mensaje):
        print(f"\n  [OK] {mensaje}")

    def pedir_input(self, mensaje):
        return input(f"  {mensaje}: ").strip()

    def pausa(self):
        input("\n  Presione ENTER para continuar...")

    # ============== PANTALLA DE INICIO ==============

    def pantalla_bienvenida(self):
        """Pantalla inicial del ATM"""
        while True:
            self.mostrar_encabezado("")
            print(self.centrar("BIENVENIDO"))
            print()
            print(self.centrar("1. Insertar tarjeta (Iniciar sesion)"))
            print(self.centrar("2. Salir"))
            print()
            self.linea()

            opcion = self.pedir_input("Seleccione una opcion")

            if opcion == '1':
                self.pantalla_autenticacion()
            elif opcion == '2':
                self.mostrar_encabezado("")
                print(self.centrar("GRACIAS POR USAR BANCO NACIONAL"))
                print(self.centrar("Hasta pronto!"))
                self.linea()
                break
            else:
                self.mostrar_error("Opcion invalida")

    # ============== AUTENTICACION ==============

    def pantalla_autenticacion(self):
        """Flujo de autenticacion (RF1)"""
        self.mostrar_encabezado("AUTENTICACION")

        print("  Por favor ingrese los datos de su tarjeta\n")

        # Ingresar numero de tarjeta
        num_tarjeta = self.pedir_input("Numero de tarjeta (16 digitos)").replace(' ', '').replace('-', '')

        # Validar formato
        valido, msg = self.facade.seguridad.validar_numero_tarjeta(num_tarjeta)
        if not valido:
            self.mostrar_error(msg)
            return

        # Verificar tarjeta
        valido, msg, tarjeta = self.facade.autenticacion.validar_tarjeta(num_tarjeta)
        if not valido:
            self.mostrar_error(msg)
            return

        # Ingresar NIP
        nip = self.pedir_input("NIP (4 digitos)")

        # Autenticar
        exito, msg, datos = self.facade.iniciar_sesion(num_tarjeta, nip)

        if exito:
            self.sesion_activa = True
            self.datos_sesion = datos
            self.mostrar_exito(msg)
            self.pausa()
            self.pantalla_principal()
        else:
            self.mostrar_error(msg)

    # ============== MENU PRINCIPAL ==============

    def pantalla_principal(self):
        """Menu principal despues de autenticacion"""
        if not self.sesion_activa or not self.datos_sesion:
            return

        cliente = self.datos_sesion['cliente']
        cuenta = self.datos_sesion['cuenta']
        tarjeta = self.datos_sesion['tarjeta']

        while True:
            self.mostrar_encabezado("MENU PRINCIPAL")
            print(f"  Cliente: {cliente['nombre']} {cliente['apellido']}")
            print(f"  Cuenta: {self.facade.seguridad.enmascarar_cuenta(cuenta['numero_cuenta'])}")
            print(f"  Tipo: {cuenta['tipo'].upper()}")
            print()
            print("  1. Consultar saldo")
            print("  2. Retirar efectivo")
            print("  3. Depositar efectivo")
            print("  4. Transferir fondos")
            print("  5. Cambiar NIP")
            print("  6. Historial de transacciones")
            print("  7. Cerrar sesion")
            print()
            self.linea()

            opcion = self.pedir_input("Seleccione una opcion")

            if opcion == '1':
                self.pantalla_consulta_saldo()
            elif opcion == '2':
                self.pantalla_retiro()
            elif opcion == '3':
                self.pantalla_deposito()
            elif opcion == '4':
                self.pantalla_transferencia()
            elif opcion == '5':
                self.pantalla_cambio_nip()
            elif opcion == '6':
                self.pantalla_historial()
            elif opcion == '7':
                self.cerrar_sesion()
                break
            else:
                self.mostrar_error("Opcion invalida")

    # ============== RF2: CONSULTA DE SALDO ==============

    def pantalla_consulta_saldo(self):
        """Pantalla de consulta de saldo (RF2)"""
        self.mostrar_encabezado("CONSULTA DE SALDO")

        exito, msg, saldo_info = self.facade.consultar_saldo(
            self.datos_sesion['cuenta']['id'],
            self.datos_sesion['tarjeta']['id']
        )

        if exito and saldo_info:
            print(f"\n  Numero de cuenta: {self.facade.seguridad.enmascarar_cuenta(saldo_info['numero_cuenta'])}")
            print(f"  Tipo de cuenta:   {saldo_info['tipo_cuenta'].upper()}")
            print()
            self.linea('-')
            print(f"  SALDO ACTUAL:       ${saldo_info['saldo']:>15,.2f}")
            print(f"  SALDO DISPONIBLE:   ${saldo_info['saldo_disponible']:>15,.2f}")
            self.linea('-')
            print(f"  Limite diario retiro: ${saldo_info['limite_diario']:>10,.2f}")
            print(f"  Retirado hoy:         ${saldo_info['retirado_hoy']:>10,.2f}")
            print(f"  Disponible hoy:       ${(saldo_info['limite_diario'] - saldo_info['retirado_hoy']):>10,.2f}")
        else:
            self.mostrar_error(msg)

        self.pausa()

    # ============== RF3: RETIRO DE EFECTIVO ==============

    def pantalla_retiro(self):
        """Pantalla de retiro de efectivo (RF3) - Caso de uso principal"""
        self.mostrar_encabezado("RETIRO DE EFECTIVO")

        # Mostrar montos rapidos
        print("  Montos rapidos:")
        print("  1. $20    2. $50    3. $100")
        print("  4. $200   5. $500   6. Otro monto")
        print()

        opcion = self.pedir_input("Seleccione opcion")
        montos = {'1': 20, '2': 50, '3': 100, '4': 200, '5': 500}

        if opcion in montos:
            monto = Decimal(str(montos[opcion]))
        elif opcion == '6':
            monto_str = self.pedir_input("Ingrese monto a retirar")
            valido, msg, monto = self.facade.validar_monto(monto_str)
            if not valido:
                self.mostrar_error(msg)
                return
        else:
            self.mostrar_error("Opcion invalida")
            return

        # Confirmar
        print(f"\n  Monto a retirar: ${monto:,.2f}")
        confirmar = self.pedir_input("Confirmar (S/N)").upper()

        if confirmar != 'S':
            print("\n  Operacion cancelada")
            self.pausa()
            return

        # Ejecutar retiro
        print("\n  Procesando...")
        exito, msg, comprobante = self.facade.retirar_efectivo(
            self.datos_sesion['cuenta']['id'],
            self.datos_sesion['tarjeta']['id'],
            monto
        )

        if exito and comprobante:
            self.mostrar_exito(msg)
            print()
            self.linea('-')

            # Mostrar comprobante
            titular = f"{self.datos_sesion['cliente']['nombre']} {self.datos_sesion['cliente']['apellido']}"
            comprobante_texto = self.facade.formatear_comprobante(comprobante, titular)
            print(comprobante_texto)

            # Ofrecer impresion
            print()
            imprimir = self.pedir_input("Desea imprimir comprobante (S/N)").upper()
            if imprimir == 'S':
                print("\n  [Imprimiendo comprobante...]")
                print("  [Por favor retire su comprobante]")
        else:
            self.mostrar_error(msg)

        self.pausa()

    # ============== DEPOSITO ==============

    def pantalla_deposito(self):
        """Pantalla de deposito de efectivo"""
        self.mostrar_encabezado("DEPOSITO DE EFECTIVO")

        monto_str = self.pedir_input("Ingrese monto a depositar")
        valido, msg, monto = self.facade.validar_monto(monto_str)
        if not valido:
            self.mostrar_error(msg)
            return

        # Confirmar
        print(f"\n  Depositar: ${monto:,.2f}")
        print(f"  En cuenta: {self.facade.seguridad.enmascarar_cuenta(self.datos_sesion['cuenta']['numero_cuenta'])}")
        confirmar = self.pedir_input("Confirmar (S/N)").upper()

        if confirmar != 'S':
            print("\n  Operacion cancelada")
            self.pausa()
            return

        print("\n  [Inserte efectivo en la bandeja...]")
        print("  [Contando billetes...]")

        exito, msg, comprobante = self.facade.depositar_efectivo(
            self.datos_sesion['cuenta']['id'],
            self.datos_sesion['tarjeta']['id'],
            monto
        )

        if exito and comprobante:
            self.mostrar_exito(msg)
            titular = f"{self.datos_sesion['cliente']['nombre']} {self.datos_sesion['cliente']['apellido']}"
            print(self.facade.formatear_comprobante(comprobante, titular))
        else:
            self.mostrar_error(msg)

        self.pausa()

    # ============== TRANSFERENCIA ==============

    def pantalla_transferencia(self):
        """Pantalla de transferencia entre cuentas"""
        self.mostrar_encabezado("TRANSFERENCIA DE FONDOS")

        cuenta_destino = self.pedir_input("Numero de cuenta destino")
        if len(cuenta_destino) < 5:
            self.mostrar_error("Numero de cuenta invalido")
            return

        monto_str = self.pedir_input("Monto a transferir")
        valido, msg, monto = self.facade.validar_monto(monto_str)
        if not valido:
            self.mostrar_error(msg)
            return

        # Confirmar
        print(f"\n  Transferir: ${monto:,.2f}")
        print(f"  A cuenta:   {self.facade.seguridad.enmascarar_cuenta(cuenta_destino)}")
        confirmar = self.pedir_input("Confirmar (S/N)").upper()

        if confirmar != 'S':
            print("\n  Operacion cancelada")
            self.pausa()
            return

        print("\n  Procesando transferencia...")
        exito, msg, comprobante = self.facade.transferir(
            self.datos_sesion['cuenta']['id'],
            cuenta_destino,
            self.datos_sesion['tarjeta']['id'],
            monto
        )

        if exito and comprobante:
            self.mostrar_exito(msg)
            titular = f"{self.datos_sesion['cliente']['nombre']} {self.datos_sesion['cliente']['apellido']}"
            print(self.facade.formatear_comprobante(comprobante, titular))
        else:
            self.mostrar_error(msg)

        self.pausa()

    # ============== CAMBIO DE NIP ==============

    def pantalla_cambio_nip(self):
        """Pantalla para cambiar el NIP"""
        self.mostrar_encabezado("CAMBIO DE NIP")

        nip_actual = self.pedir_input("NIP actual")
        nip_nuevo = self.pedir_input("Nuevo NIP (4 digitos)")
        nip_confirmar = self.pedir_input("Confirme nuevo NIP")

        exito, msg = self.facade.cambiar_nip(
            self.datos_sesion['tarjeta']['id'],
            nip_actual, nip_nuevo, nip_confirmar
        )

        if exito:
            self.mostrar_exito(msg)
        else:
            self.mostrar_error(msg)

        self.pausa()

    # ============== HISTORIAL ==============

    def pantalla_historial(self):
        """Pantalla de historial de transacciones"""
        self.mostrar_encabezado("HISTORIAL DE TRANSACCIONES")

        exito, msg, transacciones = self.facade.obtener_historial(
            self.datos_sesion['cuenta']['id'],
            15
        )

        if exito and transacciones:
            print(f"\n  {msg}\n")
            self.linea('-')
            print(f"  {'FECHA':<20} {'TIPO':<15} {'MONTO':>12} {'ESTADO':<12}")
            self.linea('-')

            for t in transacciones:
                fecha = t['fecha_hora'][:16] if t['fecha_hora'] else 'N/A'
                tipo = t['tipo'].upper()
                monto = f"${float(t['monto']):,.2f}" if t['monto'] else '$0.00'
                estado = t['estado'].upper()
                print(f"  {fecha:<20} {tipo:<15} {monto:>12} {estado:<12}")

            self.linea('-')
        else:
            print(f"\n  {msg}")

        self.pausa()

    # ============== CERRAR SESION ==============

    def cerrar_sesion(self):
        """Cierra la sesion del usuario"""
        self.sesion_activa = False
        self.datos_sesion = None
        self.mostrar_encabezado("")
        print(self.centrar("Sesion cerrada exitosamente"))
        print(self.centrar("Por favor retire su tarjeta"))
        self.linea()
        self.pausa()


def main():
    """Punto de entrada de la aplicacion"""
    app = ConsolaView()
    app.pantalla_bienvenida()


if __name__ == '__main__':
    main()
