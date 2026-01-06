from core.repositories import ReservaRepository, TransferLogRepository
from core.services.ocupacion_service import OcupacionService
from core.services.transferencia_service import TransferenciaFacade
from core.strategies import UmbralPorcentajeStrategy


def build_transferencia_facade():
    reserva_repo = ReservaRepository()
    log_repo = TransferLogRepository()

    ocupacion_service = OcupacionService(reserva_repo)

    # Regla actual (ajusta el número si tu umbral es otro)
    umbral_strategy = UmbralPorcentajeStrategy(umbral_minimo=30)

    return TransferenciaFacade(
        ocupacion_service=ocupacion_service,
        umbral_strategy=umbral_strategy,
        reserva_repo=reserva_repo,
        log_repo=log_repo,
    )
