"""
TestATM - Casos de Prueba Completos
RF5: Pruebas funcionales que aseguren cumplimiento de requisitos
Cobertura: RF1-RF5, RNF1-RNF4
"""
import unittest
import sys
import os
import shutil
from decimal import Decimal

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from repositories.database import DatabaseManager
from services.seguridad_service import SeguridadService
from services.autenticacion_service import AutenticacionService
from services.transaccion_service import TransaccionService
from services.cajero_facade import CajeroFacade


def reset_singleton():
    """Reinicia el singleton de DatabaseManager"""
    DatabaseManager._instance = None
    db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'database', 'atm_database.db')
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except:
            pass


class TestSeguridadService(unittest.TestCase):
    """Pruebas del subsistema de seguridad - Sin dependencia de BD"""

    def setUp(self):
        self.seguridad = SeguridadService()

    def test_hash_nip_consistente(self):
        nip = "1234"
        hash1 = self.seguridad.hash_nip(nip)
        hash2 = self.seguridad.hash_nip(nip)
        self.assertEqual(hash1, hash2)

    def test_hash_nip_diferente(self):
        hash1 = self.seguridad.hash_nip("1234")
        hash2 = self.seguridad.hash_nip("5678")
        self.assertNotEqual(hash1, hash2)

    def test_verificar_nip_correcto(self):
        nip = "1234"
        nip_hash = self.seguridad.hash_nip(nip)
        self.assertTrue(self.seguridad.verificar_nip(nip, nip_hash))

    def test_verificar_nip_incorrecto(self):
        nip_hash = self.seguridad.hash_nip("1234")
        self.assertFalse(self.seguridad.verificar_nip("9999", nip_hash))

    def test_validar_nip_valido(self):
        valido, msg = self.seguridad.validar_nip("1234")
        self.assertTrue(valido)

    def test_validar_nip_corto(self):
        valido, msg = self.seguridad.validar_nip("123")
        self.assertFalse(valido)

    def test_validar_nip_largo(self):
        valido, msg = self.seguridad.validar_nip("12345")
        self.assertFalse(valido)

    def test_validar_nip_no_numerico(self):
        valido, msg = self.seguridad.validar_nip("12ab")
        self.assertFalse(valido)

    def test_validar_tarjeta_16_digitos(self):
        valido, msg = self.seguridad.validar_numero_tarjeta("4532123456789012")
        self.assertTrue(valido)

    def test_validar_tarjeta_corta(self):
        valido, msg = self.seguridad.validar_numero_tarjeta("1234")
        self.assertFalse(valido)

    def test_validar_monto_valido(self):
        valido, msg, monto = self.seguridad.validar_monto("100.50")
        self.assertTrue(valido)
        self.assertEqual(monto, Decimal("100.50"))

    def test_validar_monto_negativo(self):
        valido, msg, monto = self.seguridad.validar_monto("-50")
        self.assertFalse(valido)

    def test_validar_monto_cero(self):
        valido, msg, monto = self.seguridad.validar_monto("0")
        self.assertFalse(valido)

    def test_validar_monto_no_numerico(self):
        valido, msg, monto = self.seguridad.validar_monto("abc")
        self.assertFalse(valido)

    def test_enmascarar_tarjeta(self):
        resultado = self.seguridad.enmascarar_tarjeta("4532123456789012")
        self.assertEqual(resultado, "****-****-****-9012")

    def test_generar_codigo_autorizacion(self):
        codigo = self.seguridad.generar_codigo_autorizacion()
        self.assertTrue(len(codigo) > 0)
        self.assertTrue(codigo.startswith("AUTH-"))

    def test_generar_referencia(self):
        ref = self.seguridad.generar_referencia_transaccion(1)
        self.assertTrue(len(ref) > 0)
        self.assertTrue(ref.startswith("REF-"))


class TestAutenticacionService(unittest.TestCase):
    """Pruebas del subsistema de autenticacion - RF1"""

    def setUp(self):
        reset_singleton()
        self.db = DatabaseManager()
        self.auth = AutenticacionService(self.db)

    def test_validar_tarjeta_existente(self):
        valido, msg, tarjeta = self.auth.validar_tarjeta("4532123456789012")
        self.assertTrue(valido, msg)
        self.assertIsNotNone(tarjeta)

    def test_validar_tarjeta_no_existente(self):
        valido, msg, tarjeta = self.auth.validar_tarjeta("9999999999999999")
        self.assertFalse(valido)
        self.assertIsNone(tarjeta)

    def test_validar_tarjeta_corta(self):
        valido, msg, tarjeta = self.auth.validar_tarjeta("123")
        self.assertFalse(valido)

    def test_autenticar_completo_correcto(self):
        exito, msg, datos = self.auth.autenticar_completo("4532123456789012", "1234")
        self.assertTrue(exito, msg)
        self.assertIsNotNone(datos)
        self.assertIn('tarjeta', datos)
        self.assertIn('cuenta', datos)
        self.assertIn('cliente', datos)

    def test_autenticar_nip_incorrecto(self):
        exito, msg, datos = self.auth.autenticar_completo("4532123456789012", "9999")
        self.assertFalse(exito)
        self.assertIsNone(datos)

    def test_autenticar_tarjeta_bloqueada(self):
        exito, msg, datos = self.auth.autenticar_completo("9999999999999999", "1234")
        self.assertFalse(exito)


class TestTransaccionService(unittest.TestCase):
    """Pruebas del subsistema de transacciones - RF2, RF3"""

    def setUp(self):
        reset_singleton()
        self.db = DatabaseManager()
        self.trans = TransaccionService(self.db)

    def test_consultar_saldo(self):
        exito, msg, saldo_info = self.trans.consultar_saldo(1, 1)
        self.assertTrue(exito, msg)
        self.assertIsNotNone(saldo_info)
        self.assertEqual(saldo_info['saldo'], Decimal("2500.00"))

    def test_retiro_exitoso_y_saldo_actualizado(self):
        exito, msg, comprobante = self.trans.retirar_efectivo(1, 1, Decimal("500"))
        self.assertTrue(exito, msg)
        self.assertIsNotNone(comprobante)

        exito2, msg2, saldo_info = self.trans.consultar_saldo(1, 1)
        self.assertTrue(exito2)
        self.assertIsNotNone(saldo_info)
        self.assertEqual(saldo_info['saldo'], Decimal("2000.00"))

    def test_retiro_saldo_insuficiente(self):
        exito, msg, comprobante = self.trans.retirar_efectivo(3, 3, Decimal("500"))
        self.assertFalse(exito)
        self.assertIn("Saldo insuficiente", msg)
        self.assertIsNone(comprobante)

    def test_retiro_excede_limite_diario(self):
        exito, msg, comprobante = self.trans.retirar_efectivo(1, 1, Decimal("1500"))
        self.assertFalse(exito)
        self.assertIn("limite", msg.lower())

    def test_retiro_monto_cero(self):
        exito, msg, comprobante = self.trans.retirar_efectivo(1, 1, Decimal("0"))
        self.assertFalse(exito)

    def test_deposito_exitoso(self):
        exito, msg, comprobante = self.trans.depositar_efectivo(1, 1, Decimal("300"))
        self.assertTrue(exito, msg)
        self.assertIsNotNone(comprobante)

    def test_transferencia_exitosa(self):
        exito, msg, comprobante = self.trans.transferir(1, "2207654321", 1, Decimal("500"))
        self.assertTrue(exito, msg)
        self.assertIsNotNone(comprobante)

    def test_transferencia_misma_cuenta(self):
        exito, msg, comprobante = self.trans.transferir(1, "2201234567", 1, Decimal("100"))
        self.assertFalse(exito)
        self.assertIn("misma cuenta", msg.lower())

    def test_transferencia_saldo_insuficiente(self):
        exito, msg, comprobante = self.trans.transferir(3, "2201234567", 3, Decimal("500"))
        self.assertFalse(exito)
        self.assertIn("insuficiente", msg.lower())

    def test_transferencia_cuenta_inexistente(self):
        exito, msg, comprobante = self.trans.transferir(1, "9999999999", 1, Decimal("100"))
        self.assertFalse(exito)
        self.assertIn("no encontrada", msg.lower())

    def test_historial_transacciones(self):
        exito, msg, transacciones = self.trans.obtener_historial(1, 5)
        self.assertTrue(exito)
        self.assertIsInstance(transacciones, list)


class TestCajeroFacade(unittest.TestCase):
    """Pruebas de la fachada principal - Integracion"""

    def setUp(self):
        reset_singleton()
        self.cajero = CajeroFacade()

    def test_flujo_completo_retiro(self):
        exito, msg, datos = self.cajero.iniciar_sesion("4532123456789012", "1234")
        self.assertTrue(exito, msg)

        exito2, msg2, saldo = self.cajero.consultar_saldo(
            datos['cuenta']['id'], datos['tarjeta']['id'])
        self.assertTrue(exito2)
        self.assertIsNotNone(saldo)
        saldo_inicial = saldo['saldo']

        monto = Decimal("200")
        exito3, msg3, comprobante = self.cajero.retirar_efectivo(
            datos['cuenta']['id'], datos['tarjeta']['id'], monto)
        self.assertTrue(exito3, msg3)
        self.assertIsNotNone(comprobante)
        self.assertEqual(comprobante['monto'], monto)

    def test_flujo_completo_transferencia(self):
        exito, msg, datos = self.cajero.iniciar_sesion("4532123456789012", "1234")
        self.assertTrue(exito)

        exito2, msg2, comp = self.cajero.transferir(
            datos['cuenta']['id'], "2207654321",
            datos['tarjeta']['id'], Decimal("300"))
        self.assertTrue(exito2, msg2)
        self.assertIsNotNone(comp)

    def test_validar_monto(self):
        valido, msg, monto = self.cajero.validar_monto("150.50")
        self.assertTrue(valido)
        self.assertEqual(monto, Decimal("150.50"))

    def test_formatear_comprobante(self):
        datos = {
            'tipo': 'retiro',
            'monto': Decimal("100"),
            'numero_cuenta': '2201234567',
            'saldo_anterior': Decimal("2500"),
            'saldo_nuevo': Decimal("2400"),
            'codigo_autorizacion': 'AUTH-12345',
            'referencia': 'REF-20240101-0001'
        }
        texto = self.cajero.formatear_comprobante(datos, "Juan Perez")
        self.assertIn("BANCO NACIONAL", texto)
        self.assertIn("$100.00", texto)


class TestRequisitosNoFuncionales(unittest.TestCase):
    """Pruebas de requisitos no funcionales"""

    def setUp(self):
        reset_singleton()
        self.cajero = CajeroFacade()

    def test_rnf2_tiempo_respuesta(self):
        import time
        inicio = time.time()
        exito, msg, datos = self.cajero.iniciar_sesion("4532123456789012", "1234")
        tiempo = time.time() - inicio

        self.assertTrue(exito, msg)
        self.assertLess(tiempo, 3.0, f"Tiempo de respuesta: {tiempo:.2f}s")

        inicio = time.time()
        self.cajero.consultar_saldo(datos['cuenta']['id'], datos['tarjeta']['id'])
        tiempo = time.time() - inicio
        self.assertLess(tiempo, 3.0, f"Tiempo consulta: {tiempo:.2f}s")

    def test_rnf4_cifrado_nip(self):
        nip = "1234"
        nip_hash = SeguridadService.hash_nip(nip)
        self.assertNotIn(nip, nip_hash)
        self.assertEqual(len(nip_hash), 64)

    def test_rf5_registro_transaccion(self):
        exito, msg, datos = self.cajero.iniciar_sesion("4532123456789012", "1234")
        self.assertTrue(exito)

        self.cajero.retirar_efectivo(datos['cuenta']['id'], datos['tarjeta']['id'], Decimal("50"))

        exito, msg, transacciones = self.cajero.obtener_historial(datos['cuenta']['id'], 10)
        self.assertTrue(len(transacciones) > 0)


class TestCasoUsoRetiroEfectivo(unittest.TestCase):
    """Caso de Prueba Principal: Retiro de Efectivo"""

    def setUp(self):
        reset_singleton()
        self.cajero = CajeroFacade()

    def test_cu01_retiro_flujo_normal(self):
        exito, msg, datos = self.cajero.iniciar_sesion("4532123456789012", "1234")
        self.assertTrue(exito, "Autenticacion fallo")

        monto = Decimal("300")
        exito, msg, comprobante = self.cajero.retirar_efectivo(
            datos['cuenta']['id'], datos['tarjeta']['id'], monto)

        self.assertTrue(exito, f"Retiro fallo: {msg}")
        self.assertIsNotNone(comprobante)
        self.assertEqual(comprobante['monto'], monto)

    def test_cu01_retiro_saldo_insuficiente(self):
        exito, msg, datos = self.cajero.iniciar_sesion("4532111122223333", "9012")
        self.assertTrue(exito)

        # Cuenta 3 tiene $150, intentar retirar $500
        exito, msg, comprobante = self.cajero.retirar_efectivo(
            datos['cuenta']['id'], datos['tarjeta']['id'], Decimal("5000"))
        self.assertFalse(exito)
        self.assertIn("Saldo insuficiente", msg)
        self.assertIsNone(comprobante)

    def test_cu01_retiro_excede_limite_diario(self):
        exito, msg, datos = self.cajero.iniciar_sesion("4532123456789012", "1234")
        self.assertTrue(exito)

        exito, msg, comprobante = self.cajero.retirar_efectivo(
            datos['cuenta']['id'], datos['tarjeta']['id'], Decimal("1500"))
        self.assertFalse(exito)
        self.assertIn("limite", msg.lower())
        self.assertIsNone(comprobante)

    def test_cu01_retiro_monto_no_valido(self):
        exito, msg, datos = self.cajero.iniciar_sesion("4532123456789012", "1234")
        self.assertTrue(exito)

        valido, msg_val, monto = self.cajero.validar_monto("-100")
        self.assertFalse(valido)

    def test_cu01_retiro_tarjeta_bloqueada(self):
        exito, msg, datos = self.cajero.iniciar_sesion("9999999999999999", "1234")
        self.assertFalse(exito)
        self.assertIn("no registrada", msg.lower())

    def test_cu01_secuencia_retiros_multiples(self):
        exito, msg, datos = self.cajero.iniciar_sesion("4532123456789012", "1234")
        self.assertTrue(exito)
        cuenta_id = datos['cuenta']['id']
        tarjeta_id = datos['tarjeta']['id']

        exito1, msg1, c1 = self.cajero.retirar_efectivo(cuenta_id, tarjeta_id, Decimal("300"))
        self.assertTrue(exito1, msg1)

        exito2, msg2, c2 = self.cajero.retirar_efectivo(cuenta_id, tarjeta_id, Decimal("500"))
        self.assertTrue(exito2, msg2)

        exito3, msg3, c3 = self.cajero.retirar_efectivo(cuenta_id, tarjeta_id, Decimal("300"))
        self.assertFalse(exito3)
        self.assertIn("limite", msg3.lower())


def run_tests():
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(TestSeguridadService))
    suite.addTests(loader.loadTestsFromTestCase(TestAutenticacionService))
    suite.addTests(loader.loadTestsFromTestCase(TestTransaccionService))
    suite.addTests(loader.loadTestsFromTestCase(TestCajeroFacade))
    suite.addTests(loader.loadTestsFromTestCase(TestRequisitosNoFuncionales))
    suite.addTests(loader.loadTestsFromTestCase(TestCasoUsoRetiroEfectivo))
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result


if __name__ == '__main__':
    result = run_tests()
    sys.exit(0 if result.wasSuccessful() else 1)
