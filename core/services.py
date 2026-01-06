from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from reservas.models import Reserva
from administracion.models import Horario
from core.models import TransferLog

from django.core.exceptions import ValidationError  # 👈 NUEVO



# ----------------------------------------
# 1) Cálculo de ocupación
# ----------------------------------------

def calcular_ocupacion(horario):
    """
    Devuelve (ocupacion_en_porcentaje, usados, capacidad_total)
    """
    capacidad = horario.bus.capacidad
    usados = Reserva.objects.filter(horario=horario).count()

    if capacidad == 0:
        # Sin bus o sin capacidad configurada
        return 0, 0, 0

    ocupacion = (usados / capacidad) * 100
    return ocupacion, usados, capacidad


# ----------------------------------------
# 2) Regla de negocio: umbral mínimo
#    Devuelve True si YA CUMPLE el mínimo.
# ----------------------------------------

def cumple_umbral(horario, umbral=30):
    """
    Devuelve True si la ocupación cumple el mínimo (>= umbral),
    False si está por debajo (CRÍTICO).
    """
    ocupacion, usados, capacidad = calcular_ocupacion(horario)

    if capacidad == 0:
        return False

    return ocupacion >= umbral


# ---------------------------------------------------
# 3) Buscar rutas alternativas (transferencias)
# ---------------------------------------------------

def buscar_opciones_transferencia(horario_actual, cantidad_pasajeros):
    """
    Busca horarios de la misma ruta donde sí haya espacio suficiente
    para transferir 'cantidad_pasajeros'.
    """

    # Todos los horarios de la misma ruta excepto el actual
    opciones = Horario.objects.filter(
        ruta=horario_actual.ruta
    ).exclude(id=horario_actual.id)

    opciones_filtradas = []

    for h in opciones:
        ocupacion, usados, capacidad = calcular_ocupacion(h)
        libres = capacidad - usados

        # Mostrar solo buses donde sí caben los pasajeros
        if libres >= cantidad_pasajeros:
            # Atributos auxiliares para la plantilla
            h.ocupacion_porcentaje = round(ocupacion, 2)
            h.usados = usados
            h.capacidad = capacidad
            h.libres = libres
            opciones_filtradas.append(h)

    return opciones_filtradas


# ---------------------------------------------------
# 4) Ejecutar transferencia de reservas (CORE mejorado)
# ---------------------------------------------------

@transaction.atomic
def ejecutar_transferencia(reservas, horario_destino, operador=None):
    """
    Transfiere una lista de reservas hacia 'horario_destino',
    reasignando asientos sin duplicados y con validaciones extra.
    """

    if not reservas:
        return False, "No se enviaron reservas para transferir."

    # Tomamos el horario origen de la primera reserva
    horario_origen = reservas[0].horario

    # ==================================================================
    # 🔥 VALIDACIÓN GLOBAL: evitar transferencias mixtas o inconsistentes
    # ==================================================================

    # 1. Validar que todas las reservas vienen del mismo horario
    horarios_distintos = [
        r.id for r in reservas if r.horario_id != horario_origen.id
    ]
    if horarios_distintos:
        return False, (
            "Todas las reservas deben tener el mismo horario de origen. "
            f"Reservas inválidas: {horarios_distintos}"
        )

    # 2. Validar si alguna reserva YA fue transferida
    reservas_transferidas = [
        r for r in reservas if getattr(r, "transferida", False)
    ]
    if reservas_transferidas:
        detalle = ", ".join(
            f"{r.nombre_pasajero} (Asiento {r.asiento})"
            for r in reservas_transferidas
        )
        return False, (
            "No se puede realizar la transferencia. "
            "Las siguientes reservas ya fueron transferidas previamente: "
            + detalle
        )

    # ==================================================================
    # 🔥 VALIDACIÓN DE HORARIO DESTINO (no transferir a buses ya salidos)
    # ==================================================================

    now = timezone.now()
    if hasattr(horario_destino, "fecha_salida"):
        if horario_destino.fecha_salida <= now:
            return False, "No se puede transferir a un bus que ya salió."

    # ==================================================================
    # 🔥 VALIDACIÓN DE CAPACIDAD ANTES DE TRANSFERIR
    # ==================================================================

    ocup_origen_antes, usados_origen_antes, cap_origen = calcular_ocupacion(horario_origen)
    ocup_destino_antes, usados_destino_antes, cap_destino = calcular_ocupacion(horario_destino)

    cantidad = len(reservas)
    libres_destino_antes = cap_destino - usados_destino_antes

    if libres_destino_antes < cantidad:
        return False, (
            f"No se pueden transferir {cantidad} pasajeros. "
            f"Solo hay {libres_destino_antes} asientos libres."
        )

    # ==================================================================
    # 🔥 ASIGNACIÓN DE ASIENTOS EN DESTINO
    # ==================================================================

    # Asientos ya ocupados en el horario destino
    asientos_ocupados = set(
        Reserva.objects.select_for_update()
        .filter(horario=horario_destino)
        .values_list("asiento", flat=True)
    )

    def siguiente_asiento_libre():
        for i in range(1, cap_destino + 1):
            if i not in asientos_ocupados:
                asientos_ocupados.add(i)
                return i
        return None

    # ==================================================================
    # 🔥 TRANSFERENCIA REAL (cambia asiento + horario)
    # ==================================================================

    coop_origen = horario_origen.bus.cooperativa_id
    coop_destino = horario_destino.bus.cooperativa_id
    es_cross_coop = (coop_origen != coop_destino)

    
    for r in reservas:
        nuevo_asiento = siguiente_asiento_libre()
        if nuevo_asiento is None:
            raise ValueError("Error inesperado: no se encontró asiento libre en el bus destino.")

        # 🚨 Validación extra por seguridad (antes de guardar)
        if Reserva.objects.filter(horario=horario_destino, asiento=nuevo_asiento).exists():
            raise ValidationError(f"El asiento {nuevo_asiento} ya está ocupado en el horario destino.")

        # ✅ Guardar dentro del loop (esto era tu error)
        r.asiento = nuevo_asiento
        r.horario = horario_destino
        r.transferida = True
        r.restringida = es_cross_coop
        r.save()



    # ==================================================================
    # 🔥 VALIDACIÓN DE CAPACIDAD DESPUÉS DE TRANSFERIR
    # ==================================================================

    ocup_origen_despues, usados_origen_despues, _ = calcular_ocupacion(horario_origen)
    ocup_destino_despues, usados_destino_despues, _ = calcular_ocupacion(horario_destino)
    libres_destino_despues = cap_destino - usados_destino_despues

    if libres_destino_despues < 0:
        raise ValueError("La transferencia provocó sobrecapacidad en el bus destino.")

    # ==================================================================
    # 🔥 REGISTRO EN LOG DE AUDITORÍA
    # ==================================================================

    TransferLog.objects.create(
        operador=operador,
        origen=horario_origen,
        destino=horario_destino,
        reservas=[r.id for r in reservas],
        cantidad_pasajeros=cantidad,
        capacidad_origen_antes=cap_origen - usados_origen_antes,
        capacidad_origen_despues=cap_origen - usados_origen_despues,
        capacidad_destino_antes=libres_destino_antes,
        capacidad_destino_despues=libres_destino_despues,
        estado="OK",
        mensaje="Transferencia realizada correctamente."
    )

    return True, "Transferencia realizada correctamente."


def obtener_tarifa_ruta(ruta):
    """
    Devuelve una tarifa aproximada en dólares
    según la ruta origen-destino.
    Si no está en el mapa, usa un valor por defecto.
    """
    clave = (ruta.origen, ruta.destino)
    return TARIFAS_POR_RUTA.get(clave, Decimal("15.00"))


def factor_urgencia(ocupacion):
    """
    Entre más ocupación tenga el bus que transfiere,
    más urgente es la situación, mayor el factor.
    """
    if ocupacion < 30:
        return Decimal("1.0")
    elif ocupacion < 80:
        return Decimal("1.2")
    else:
        return Decimal("1.5")


def calcular_costos_negociacion(horario_origen, horario_destino, cantidad_pasajeros):
    """
    Calcula todos los valores de la negociación entre cooperativas.
    Devuelve un diccionario listo para usar en la plantilla.
    """
    tarifa_origen = obtener_tarifa_ruta(horario_origen.ruta)
    tarifa_destino = obtener_tarifa_ruta(horario_destino.ruta)

    # Diferencia de tarifas (lo que "pierde" o "gana" la otra empresa)
    diferencia = tarifa_destino - tarifa_origen

    # Costos operativos estimados (simples, solo para demo de CORE)
    costos_operativos = Decimal("4.80")

    ocupacion, usados, capacidad = calcular_ocupacion(horario_origen)
    f_urgencia = factor_urgencia(ocupacion)

    # Compensación sugerida por pasajero
    # (tarifa destino + costos + max(0, diferencia)) * factor
    base = tarifa_destino + costos_operativos + max(Decimal("0.00"), diferencia)
    compensacion_por_pasajero = base * f_urgencia

    total_sugerido = compensacion_por_pasajero * Decimal(cantidad_pasajeros)

    return {
        "tarifa_origen": tarifa_origen,
        "tarifa_destino": tarifa_destino,
        "diferencia": diferencia,
        "costos_operativos": costos_operativos,
        "ocupacion": ocupacion,
        "usados": usados,
        "capacidad": capacidad,
        "factor_urgencia": f_urgencia,
        "compensacion_por_pasajero": compensacion_por_pasajero,
        "total_sugerido": total_sugerido,
    }
