class OcupacionService:
    def __init__(self, reserva_repo):
        self.reserva_repo = reserva_repo

    def calcular(self, horario):
        capacidad = getattr(horario.bus, "capacidad", 0) or 0
        usados = self.reserva_repo.contar_por_horario(horario)

        if capacidad <= 0:
            return 0.0, usados, capacidad

        ocupacion = (usados / capacidad) * 100.0
        return round(ocupacion, 2), usados, capacidad
