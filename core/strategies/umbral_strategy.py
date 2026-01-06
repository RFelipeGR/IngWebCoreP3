from abc import ABC, abstractmethod

class UmbralStrategy(ABC):
    @abstractmethod
    def cumple(self, ocupacion_porcentaje: float) -> bool:
        """Retorna True si se debe ejecutar acción según la ocupación."""
        raise NotImplementedError


class UmbralPorcentajeStrategy(UmbralStrategy):
    def __init__(self, umbral_minimo: float):
        self.umbral_minimo = float(umbral_minimo)

    def cumple(self, ocupacion_porcentaje: float) -> bool:
        # Ej: si ocupación es menor al umbral -> CRÍTICO
        return float(ocupacion_porcentaje) < self.umbral_minimo


class UmbralRangoStrategy(UmbralStrategy):
    """Ejemplo extra para demostrar OCP sin complicarte."""
    def __init__(self, minimo: float, maximo: float):
        self.minimo = float(minimo)
        self.maximo = float(maximo)

    def cumple(self, ocupacion_porcentaje: float) -> bool:
        x = float(ocupacion_porcentaje)
        return self.minimo <= x <= self.maximo
