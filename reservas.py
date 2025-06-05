import flet as ft
import os
import json
from datetime import datetime, time
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

reservas_file = "reservas.json"

def cargar_reservas():
    if os.path.exists(reservas_file):
        with open(reservas_file, "r") as f:
            return json.load(f)
    return []

def guardar_reservas(reservas):
    with open(reservas_file, "w") as f:
        json.dump(reservas, f, indent=2)

def generar_comprobante_pdf(reserva):
    nombre_archivo = f"comprobante_mesa{reserva['mesa']}_{reserva['fecha']}_{reserva['hora'].replace(':', '')}.pdf"
    c = canvas.Canvas(nombre_archivo, pagesize=letter)
    c.setFont("Helvetica", 14)
    c.drawString(100, 700, "🧾 COMPROBANTE DE RESERVA")
    c.drawString(100, 670, f"Cliente: {reserva['cliente']}")
    c.drawString(100, 650, f"Mesa: {reserva['mesa']}")
    c.drawString(100, 630, f"Fecha: {reserva['fecha']}")
    c.drawString(100, 610, f"Hora: {reserva['hora']}")
    c.drawString(100, 580, "¡Gracias por su reserva!")
    c.save()
    return nombre_archivo

def vista_reservas(page: ft.Page):
    reservas = cargar_reservas()
    mensaje = ft.Text()
    lista_reservas = ft.Column()

    input_cliente = ft.TextField(label="Nombre del Cliente", width=300)
    input_mesa = ft.TextField(label="Número de Mesa", keyboard_type="number", width=200)
    input_mes = ft.TextField(label="Mes (1-12)", keyboard_type="number", width=200)
    input_dia = ft.TextField(label="Día (1-31)", keyboard_type="number", width=200)
    input_hora = ft.TextField(label="Hora (formato HH:MM)", keyboard_type="datetime", width=200)

    def reservar_mesa(e):
        mensaje.value = ""

        try:
            nombre_cliente = input_cliente.value.strip()
            int_mesa = int(input_mesa.value.strip())
            int_mes = int(input_mes.value.strip())
            int_dia = int(input_dia.value.strip())
            hora_texto = input_hora.value.strip()

            if not (nombre_cliente and hora_texto):
                raise ValueError("Faltan campos")

            hora_obj = datetime.strptime(hora_texto, "%H:%M")
            int_hora = hora_obj.hour
            int_minuto = hora_obj.minute

        except ValueError:
            mensaje.value = "Datos inválidos. Verifica que todos los campos estén completos y con el formato correcto."
            mensaje.color = ft.Colors.RED
            page.update()
            return

        if not (1 <= int_mesa <= 50):
            mensaje.value = "Número de mesa fuera de rango (1-50)."
            mensaje.color = ft.Colors.RED
            page.update()
            return
        if not (1 <= int_mes <= 12):
            mensaje.value = "Mes fuera de rango (1-12)."
            mensaje.color = ft.Colors.RED
            page.update()
            return
        if not (1 <= int_dia <= 31):
            mensaje.value = "Día fuera de rango (1-31)."
            mensaje.color = ft.Colors.RED
            page.update()
            return

        anio_actual = datetime.now().year

        try:
            fecha_completa = datetime(anio_actual, int_mes, int_dia, int_hora, int_minuto)
        except ValueError as err:
            mensaje.value = f"Fecha inválida: {err}"
            mensaje.color = ft.Colors.RED
            page.update()
            return

        hora_reserva = time(int_hora, int_minuto)
        inicio_turno = time(18, 0)
        fin_turno = time(2, 30)

        if not (inicio_turno <= hora_reserva or hora_reserva <= fin_turno):
            mensaje.value = "Horario no permitido. Solo se aceptan reservas entre las 18:00 y las 02:30."
            mensaje.color = ft.Colors.RED
            page.update()
            return

        if hora_reserva <= fin_turno:
            fecha_completa = fecha_completa.replace(day=fecha_completa.day - 1)

        fecha_str = fecha_completa.strftime("%Y-%m-%d")
        hora_str = hora_obj.strftime("%H:%M")

        for r in reservas:
            if r["mesa"] == int_mesa and r["fecha"] == fecha_str:
                mensaje.value = f"La mesa {int_mesa} ya tiene una reserva para el día {fecha_str}."
                mensaje.color = ft.Colors.RED
                page.update()
                return

        nueva_reserva = {
            "cliente": nombre_cliente,
            "mesa": int_mesa,
            "fecha": fecha_str,
            "hora": hora_str
        }

        reservas.append(nueva_reserva)
        guardar_reservas(reservas)

        mensaje.value = f"✅ Reserva para {nombre_cliente} confirmada."
        mensaje.color = ft.Colors.GREEN

        for campo in [input_cliente, input_mesa, input_mes, input_dia, input_hora]:
            campo.value = ""

        actualizar_lista()
        page.update()

    def ver_comprobante(index):
        reserva = reservas[index]
        archivo = generar_comprobante_pdf(reserva)
        mensaje.value = f"📄 Comprobante generado: {archivo}"
        mensaje.color = ft.Colors.GREEN
        page.update()

    def eliminar_reserva(index):
        del reservas[index]
        guardar_reservas(reservas)
        mensaje.value = "Reserva eliminada exitosamente."
        mensaje.color = ft.Colors.ORANGE
        actualizar_lista()
        page.update()

    def actualizar_lista():
        lista_reservas.controls.clear()
        reservas_ordenadas = sorted(reservas, key=lambda r: (r["fecha"], r["hora"], r["mesa"]))
        for i, r in enumerate(reservas_ordenadas):
            fila = ft.Row([
                ft.Text(f"{r['cliente']} - Mesa {r['mesa']} - {r['fecha']} a las {r['hora']}"),
                ft.IconButton(icon=ft.Icons.PICTURE_AS_PDF, tooltip="Generar PDF", on_click=lambda e, ix=i: ver_comprobante(ix)),
                ft.IconButton(icon=ft.Icons.DELETE, tooltip="Eliminar reserva", on_click=lambda e, ix=i: eliminar_reserva(ix)),
            ])
            lista_reservas.controls.append(fila)
        page.update()

    actualizar_lista()

    return ft.View(
        route="/reservas",
        controls=[
            ft.AppBar(
                title=ft.Text("Gestión de Reservas"),
                leading=ft.IconButton(icon=ft.Icons.ARROW_BACK, on_click=lambda _: page.go("/"))
            ),
            ft.Text("Reservar Mesa", size=20, weight="bold"),
            input_cliente,
            ft.Row([input_mesa, input_mes, input_dia]),
            input_hora,
            ft.ElevatedButton("Reservar", on_click=reservar_mesa, bgcolor=ft.Colors.BLUE, color=ft.Colors.WHITE),
            mensaje,
            ft.Divider(),
            ft.Text("Reservas actuales", size=16, weight="bold"),
            lista_reservas
        ]
    )
