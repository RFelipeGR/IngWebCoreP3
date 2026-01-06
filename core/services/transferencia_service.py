from django.db import transaction
from django.utils import timezone

class TransferenciaFacade:
    """
    Facade: expone un método único para la transferencia completa.
    Controller llama solo a esto.
    """
    def __init__(self, ocupacion_service, umbral_strategy, reserva_repo, log_repo):
        self.ocupacion_service = ocupacion_service
        self.umbral_strategy = umbral_strategy
        self.reserva_repo = reserva_repo
        self.log_repo = log_repo

    @transaction.atomic
    def ejecutar(self, horario_origen, horario_destino, motivo="AUTO"):
        # 1) calcular ocupación origen
        ocupacion, usados, capacidad = self.ocupacion_service.calcular(horario_origen)

        # 2) validar regla (Strategy)
        if not self.umbral_strategy.cumple(ocupacion):
            return {
                "ok": False,
                "msg": "No cumple umbral, no se transfiere.",
                "ocupacion": ocupacion,
                "usados": usados,
                "capacidad": capacidad,
            }

        # 3) validar cupos destino (regla simple, sin complicarte)
        ocup_dest, usados_dest, cap_dest = self.ocupacion_service.calcular(horario_destino)
        libres_dest = (cap_dest - usados_dest) if cap_dest else 0

        reservas_origen = self.reserva_repo.obtener_por_horario(horario_origen)
        total_a_mover = reservas_origen.count()

        if total_a_mover > libres_dest:
            return {
                "ok": False,
                "msg": "Destino sin cupos suficientes.",
                "a_mover": total_a_mover,
                "libres_dest": libres_dest,
            }

        # 4) mover reservas
        self.reserva_repo.mover_reservas(reservas_origen, horario_destino)

        # 5) log (SRP: log en repo)
        self.log_repo.crear_log(
            horario_origen=horario_origen,
            horario_destino=horario_destino,
            cantidad=total_a_mover,
            motivo=motivo,
            fecha=timezone.now(),
            ocupacion_origen=ocupacion,
        )

        return {
            "ok": True,
            "msg": "Transferencia ejecutada correctamente.",
            "movidas": total_a_mover,
            "ocupacion_origen": ocupacion,
        }
