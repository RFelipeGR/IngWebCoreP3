# Django
from urllib import request
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib import messages

# Models
from administracion.models import Operador, Horario
from reservas.models import Reserva, Negociacion

# Servicios
from core.services import (
    buscar_opciones_transferencia,
    ejecutar_transferencia,
    calcular_costos_negociacion,
    calcular_ocupacion,
    cumple_umbral,
)

# Otros
from django.http import HttpResponse



# -----------------------------------------------------------
# 📌 IMPORTS LIMPIOS
# -----------------------------------------------------------

from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib import messages

from administracion.models import Operador, Horario
from reservas.models import Reserva, Negociacion

from core.services import (
    buscar_opciones_transferencia,
    ejecutar_transferencia,
    calcular_ocupacion,
    calcular_costos_negociacion,
    cumple_umbral,
)

# -----------------------------------------------------------
# 📌 PANEL PRINCIPAL DEL OPERADOR
# -----------------------------------------------------------

@login_required
def panel_operador(request):
    try:
        operador = Operador.objects.get(user=request.user)
    except Operador.DoesNotExist:
        return redirect("login")

    cooperativa = operador.cooperativa
    horarios = Horario.objects.filter(bus__cooperativa=cooperativa)

    data = []
    for h in horarios:
        ocupacion, usados, capacidad = calcular_ocupacion(h)
        estado = "OK" if cumple_umbral(h) else "CRÍTICO"

        data.append({
            "horario": h,
            "usados": usados,
            "libres": capacidad - usados,
            "total": capacidad,
            "ocupacion": round(ocupacion, 2),
            "estado": estado,
        })

    solicitudes = Negociacion.objects.filter(
        destino__bus__cooperativa=cooperativa,
        estado="PENDIENTE"
    )

    solicitudes_detalladas = []
    for n in solicitudes:
        cantidad = len(n.reservas)
        precio = n.costo_por_pasajero
        total_ingreso = cantidad * precio
        costo_destino = cantidad * n.costo_operativo_destino

        gastos_admin = total_ingreso * 0.05
        comision = total_ingreso * 0.08

        solicitudes_detalladas.append({
            "obj": n,
            "cantidad": cantidad,
            "precio": precio,
            "total_origen": round(total_ingreso, 2),
            "costo_operativo_destino": round(costo_destino, 2),
            "ganancia_destino": round(total_ingreso - costo_destino, 2),
            "gastos_admin": round(gastos_admin, 2),
            "comision_sistema": round(comision, 2),
            "margen_origen": round(total_ingreso - gastos_admin - comision, 2),
            "margen_destino": round((total_ingreso - costo_destino) - gastos_admin, 2),
        })

    return render(request, "reservas/panel_operador.html", {
        "cooperativa": cooperativa,
        "data": data,
        "solicitudes": solicitudes_detalladas,
    })

# -----------------------------------------------------------
# 📌 TRANSFERENCIAS INTERNAS
# -----------------------------------------------------------

@login_required
def iniciar_negociacion(request, reserva_id):
    operador = Operador.objects.get(user=request.user)

    reserva = get_object_or_404(
        Reserva,
        id=reserva_id,
        horario__bus__cooperativa=operador.cooperativa
    )

    opciones = buscar_opciones_transferencia(reserva.horario, 1)

    return render(request, "reservas/negociacion.html", {
        "reserva": reserva,
        "opciones": opciones
    })


@login_required
def transferir_pasajeros(request, reserva_id, horario_id):
    operador = Operador.objects.get(user=request.user)

    reserva = get_object_or_404(
        Reserva,
        id=reserva_id,
        horario__bus__cooperativa=operador.cooperativa
    )

    horario_destino = get_object_or_404(Horario, id=horario_id)

    if request.method == "POST":
        cantidad = int(request.POST.get("cantidad"))
        ejecutar_transferencia(reserva, horario_destino, cantidad)
        return render(request, "reservas/transferencia_exitosa.html")

    return redirect('panel_operador')


@login_required
def transferencias(request, id):
    origen = get_object_or_404(Horario, id=id)
    reservas = Reserva.objects.filter(horario=origen).order_by("asiento")

    # Cargar opciones de la misma ruta sin filtrar por capacidad todavía
    opciones = Horario.objects.filter(ruta=origen.ruta).exclude(id=origen.id)

    # Calcular datos de ocupación para mostrarlos en el select
    for h in opciones:
        ocupacion, usados, capacidad = calcular_ocupacion(h)
        h.libres = capacidad - usados
        h.capacidad = capacidad
        h.ocupacion_porcentaje = round(ocupacion, 2)

    # =====================================================================
    # 🔥 PROCESAR POST (EL USUARIO INTENTÓ TRANSFERIR)
    # =====================================================================
    if request.method == "POST":
        seleccionados = request.POST.getlist("reservas")
        destino = get_object_or_404(Horario, id=request.POST.get("destino"))

        reservas_objs = Reserva.objects.filter(id__in=seleccionados)

        # 🔥 VALIDACIÓN GLOBAL: NO PERMITIR TRANSFERENCIA MIXTA
        reservas_transferidas = [
            r for r in reservas_objs if getattr(r, "transferida", False)
        ]

        if reservas_transferidas:
            # Armamos un texto más amigable: "Pasajero X (Asiento Y)"
            detalle = ", ".join(
                f"{r.nombre_pasajero} (Asiento {r.asiento})"
                for r in reservas_transferidas
            )

            messages.error(
                request,
                "No se puede transferir. Las siguientes reservas ya fueron transferidas previamente: "
                + detalle
            )
            return redirect(request.path)


        # ✔ MISMA COOPERATIVA → TRANSFERIR DIRECTAMENTE
        if origen.bus.cooperativa == destino.bus.cooperativa:

            ok, msg = ejecutar_transferencia(reservas_objs, destino)

            if not ok:
                messages.error(request, msg)
                return redirect(request.path)

            messages.success(request, "Transferencia realizada correctamente.")
            return redirect("panel_operador")

        # ✔ OTRA COOPERATIVA → CREAR NEGOCIACIÓN
        Negociacion.objects.create(
            origen=origen,
            destino=destino,
            reservas=seleccionados,
            costo_por_pasajero=float(request.POST.get("costo_por_pasajero")),
            comentario_origen=request.POST.get("comentario_origen", ""),
            estado="PENDIENTE",
        )

        messages.success(request, "Solicitud de negociación enviada.")
        return redirect("panel_operador")

    # =====================================================================
    # Mostrar página normalmente
    # =====================================================================
    return render(request, "reservas/transferencias.html", {
        "horario": origen,
        "reservas": reservas,
        "opciones": opciones,
    })


# -----------------------------------------------------------
# 📌 DETALLES Y ESTADÍSTICAS
# -----------------------------------------------------------

@login_required
def detalle_reserva(request, id):
    horario = get_object_or_404(Horario, id=id)
    reservas = Reserva.objects.filter(horario=horario).order_by("asiento")

    return render(request, "reservas/detalle_reserva.html", {
        "horario": horario,
        "reservas": reservas,
    })


@login_required
def estadisticas_reserva(request, id):
    horario = get_object_or_404(Horario, id=id)

    ocupacion, usados, total = calcular_ocupacion(horario)
    estado = "OK" if cumple_umbral(horario) else "CRÍTICO"

    return render(request, "reservas/estadisticas_reserva.html", {
        "horario": horario,
        "ocupacion": round(ocupacion, 2),
        "usados": usados,
        "total": total,
        "estado": estado,
    })

# -----------------------------------------------------------
# 📌 NEGOCIACIONES ENTRE COOPERATIVAS
# -----------------------------------------------------------

def negociacion(request):
    data = request.session.get("transferencia")
    if not data:
        return redirect("panel_operador")

    origen = Horario.objects.get(id=data["origen"])
    destino = Horario.objects.get(id=data["destino"])
    cantidad = len(data["reservas"])

    costo_promedio = 3.5
    costo_oper_dest = 1.2 * cantidad
    compensacion = costo_promedio * cantidad
    ganancia_dest = compensacion - costo_oper_dest

    if request.method == "POST":
        ejecutar_transferencia(
            Reserva.objects.filter(id__in=data["reservas"]),
            destino
        )
        del request.session["transferencia"]
        return redirect("panel_operador")

    return render(request, "reservas/negociacion.html", {
        "origen": origen,
        "destino": destino,
        "cantidad": cantidad,
        "costo_promedio": costo_promedio,
        "compensacion_minima": compensacion,
        "costo_operativo_destino": costo_oper_dest,
        "ganancia_neta_destino": ganancia_dest,
    })


def solicitudes_negociacion(request):
    coop = request.user.operador.cooperativa
    solicitudes = Negociacion.objects.filter(
        destino__bus__cooperativa=coop,
        estado="PENDIENTE"
    )
    return render(request, "reservas/solicitudes_negociacion.html", {
        "solicitudes": solicitudes
    })


def responder_negociacion(request, id):
    nego = get_object_or_404(Negociacion, id=id)

    if request.method == "POST":
        if "aceptar" in request.POST:
            ejecutar_transferencia(
                Reserva.objects.filter(id__in=nego.reservas),
                nego.destino
            )
            nego.estado = "ACEPTADA"
            nego.save()
            return redirect("solicitudes_negociacion")

        if "contraoferta" in request.POST:
            nego.propuesta_destino = float(request.POST["oferta"])
            nego.estado = "CONTRAOFERTA"
            nego.creada_por = "DESTINO"
            nego.save()
            return redirect("solicitudes_negociacion")

    return render(request, "reservas/responder_negociacion.html", {"nego": nego})


def aceptar_negociacion(request, id):
    negociacion = get_object_or_404(Negociacion, id=id)
    reservas = Reserva.objects.filter(id__in=negociacion.reservas)

    for r in reservas:
        r.horario = negociacion.destino
        r.save()

    negociacion.estado = "ACEPTADA"
    negociacion.save()

    return redirect("panel_operador")


def rechazar_negociacion(request, id):
    negociacion = get_object_or_404(Negociacion, id=id)
    negociacion.estado = "RECHAZADA"
    negociacion.comentario_destino = "Se rechazó la oferta."
    negociacion.save()
    return redirect("panel_operador")


def negociar(request, id):
    nego = get_object_or_404(Negociacion, id=id)
    total = len(nego.reservas)
    ingreso = nego.costo_por_pasajero * total
    costo = nego.costo_operativo_destino * total

    return render(request, "reservas/negociacion_detalle.html", {
        "neg": nego,
        "ingreso_b": round(ingreso, 2),
        "ganancia_b": round(ingreso - costo, 2),
    })

# -----------------------------------------------------------
# 📌 LOGOUT
# -----------------------------------------------------------

def operador_logout(request):
    logout(request)
    return redirect('login')
