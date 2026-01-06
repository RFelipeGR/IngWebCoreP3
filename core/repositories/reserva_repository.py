from reservas.models import Reserva

class ReservaRepository:
    def contar_por_horario(self, horario):
        return Reserva.objects.filter(horario=horario).count()

    def obtener_por_horario(self, horario):
        return Reserva.objects.filter(horario=horario).order_by("id")

    def mover_reservas(self, reservas_qs, nuevo_horario):
        # Update masivo simple (puedes cambiar a iterativo si necesitas log por reserva)
        return reservas_qs.update(horario=nuevo_horario)
