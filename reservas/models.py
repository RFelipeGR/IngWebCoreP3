from django.db import models
from administracion.models import Horario


class Reserva(models.Model):
    horario = models.ForeignKey(Horario, on_delete=models.CASCADE)
    nombre_pasajero = models.CharField(max_length=100)
    cedula = models.CharField(max_length=10)
    asiento = models.PositiveIntegerField()
    transferida = models.BooleanField(default=False)

    # ✅ NUEVO: marca si queda en restricción (cross-coop)
    restringida = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.nombre_pasajero} - Asiento {self.asiento}"



class Negociacion(models.Model):
    origen = models.ForeignKey(Horario, related_name='neg_origen', on_delete=models.CASCADE)
    destino = models.ForeignKey(Horario, related_name='neg_destino', on_delete=models.CASCADE)

    reservas = models.JSONField()  # IDs de reservas involucradas

    # Valores enviados por la COOPERATIVA origen
    costo_por_pasajero = models.FloatField()
    comentario_origen = models.TextField(blank=True)

    # Respuesta de la COOPERATIVA destino
    costo_operativo_destino = models.FloatField(default=1.5)
    compensacion_minima = models.FloatField(default=3.0)
    comentario_destino = models.TextField(blank=True)

    # Estado
    estado = models.CharField(max_length=20, default='PROPUESTA')
    fecha = models.DateTimeField(auto_now_add=True)

    # Campo cuando ya se cierra
    precio_final = models.FloatField(null=True, blank=True)

    def pasajeros(self):
        return len(self.reservas)
