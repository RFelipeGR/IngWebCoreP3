from django.test import TestCase
from django.utils import timezone

from administracion.models import Horario
from reservas.models import Reserva
from core.services import ejecutar_transferencia, calcular_ocupacion

class TransferenciaCoreTests(TestCase):
    def setUp(self):
        # TODO: ajusta estos campos a los que realmente tenga tu modelo Horario
        now = timezone.now()
        self.horario_origen = Horario.objects.create(
            fecha_salida=now + timezone.timedelta(hours=1),
            # aquí debes poner los campos obligatorios de tu modelo Horario:
            # ejemplo: ruta=..., bus=...
        )
        self.horario_destino = Horario.objects.create(
            fecha_salida=now + timezone.timedelta(hours=2),
            # mismos campos obligatorios que arriba
        )

        self.reserva = Reserva.objects.create(
            horario=self.horario_origen,
            nombre_pasajero="Pasajero Test",
            cedula="0102030405",
            asiento=1,
        )

    def test_calcular_ocupacion_basico(self):
        ocup, usados, cap = calcular_ocupacion(self.horario_origen)
        # Simplemente comprobamos que se ejecuta sin error
        self.assertGreaterEqual(ocup, 0)

    def test_transferencia_valida(self):
        ok, msg = ejecutar_transferencia([self.reserva], self.horario_destino)
        self.assertTrue(ok, msg)

        self.reserva.refresh_from_db()
        self.assertEqual(self.reserva.horario, self.horario_destino)
        self.assertTrue(self.reserva.transferida)
