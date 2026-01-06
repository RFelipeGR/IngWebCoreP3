from administracion.models import Horario

class HorarioRepository:
    def get(self, horario_id: int):
        return Horario.objects.get(id=horario_id)
