import flet as ft
import json
import os
from datetime import datetime
from fpdf import FPDF

entregados_file = "entregados.json"
pdf_output_path = "."  # Carpeta donde se guardan los PDFs


def cargar_entregados():
    if os.path.exists(entregados_file):
        with open(entregados_file, "r") as f:
            return json.load(f)
    return {}


def guardar_entregados(entregados):
    with open(entregados_file, "w") as f:
        json.dump(entregados, f, indent=2)


def guardar_factura_pdf(mesa_id: str, datos_mesa: dict, metodo_pago: str):
    fecha_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.cell(200, 10, txt="Factura", ln=True, align="C")
    pdf.cell(200, 10, txt=f"Mesa: {mesa_id}", ln=True)
    pdf.cell(200, 10, txt=f"Fecha y Hora: {fecha_hora}", ln=True)
    pdf.cell(200, 10, txt=f"Método de pago: {metodo_pago}", ln=True)
    pdf.ln(10)
    pdf.cell(200, 10, txt="Pedidos realizados:", ln=True)

    for producto in datos_mesa.get("productos", []):
        pdf.cell(200, 10, txt=f"- {producto['producto']} x {producto['cantidad']} - Monto: ${producto['monto_total']:.2f}", ln=True)

    total = datos_mesa.get("monto_total", 0.0)
    pdf.ln(10)
    pdf.cell(200, 10, txt=f"Total a cobrar: ${total:.2f}", ln=True)

    filename = f"factura_mesa_{mesa_id}.pdf"
    output_file = os.path.join(pdf_output_path, filename)
    pdf.output(output_file)
    return output_file


def vista_cobros(page: ft.Page):
    entregados = cargar_entregados()
    lista_factura = ft.Column()
    mensaje = ft.Text()
    enlace_pdf = ft.Text()

    dropdown_mesas = ft.Dropdown(
        label="Seleccionar mesa",
        options=[ft.DropdownOption(m) for m in entregados.keys()]
    )

    def actualizar_dropdown():
        dropdown_mesas.options = [ft.DropdownOption(m) for m in entregados.keys()]
        dropdown_mesas.value = None

    def actualizar_detalle_mesa(e):
        mesa_id = dropdown_mesas.value
        lista_factura.controls.clear()
        mensaje.value = ""
        enlace_pdf.value = ""
        if not mesa_id:
            page.update()
            return

        datos_mesa = entregados.get(mesa_id)
        if not datos_mesa:
            mensaje.value = "No se encontraron datos para esa mesa."
            page.update()
            return

        lista_factura.controls.append(ft.Text(f"Pedidos en Mesa {mesa_id}:", size=16, weight="bold"))
        for producto in datos_mesa.get("productos", []):
            lista_factura.controls.append(
                ft.Text(f"- {producto['producto']} x {producto['cantidad']} - Monto: ${producto['monto_total']:.2f}")
            )

        total = datos_mesa.get("monto_total", 0.0)
        lista_factura.controls.append(ft.Divider())
        lista_factura.controls.append(ft.Text(f"Total: ${total:.2f}", weight="bold"))
        page.update()

    # Campos tarjeta
    campo_nombre = ft.TextField(
        label="Nombre en tarjeta", visible=False, max_length=26
    )
    campo_numero = ft.TextField(
        label="Número de tarjeta", visible=False, max_length=16,
        keyboard_type=ft.KeyboardType.NUMBER,
        input_filter=ft.InputFilter(allow=True, regex_string=r"\d+")
    )
    campo_vencimiento = ft.TextField(
        label="Vencimiento (MM/AA)", visible=False, max_length=5, hint_text="Ej: 08/27"
    )
    campo_cvv = ft.TextField(
        label="CVV", visible=False, password=True, max_length=3,
        keyboard_type=ft.KeyboardType.NUMBER,
        input_filter=ft.InputFilter(allow=True, regex_string=r"\d+")
    )

    def mostrar_campos_tarjeta(visible: bool):
        campo_nombre.visible = visible
        campo_numero.visible = visible
        campo_vencimiento.visible = visible
        campo_cvv.visible = visible
        page.update()

    def generar_factura(metodo_pago):
        mesa_id = dropdown_mesas.value
        if not mesa_id:
            page.snack_bar = ft.SnackBar(ft.Text("Seleccione una mesa."), bgcolor=ft.Colors.RED)
            page.snack_bar.open = True
            page.update()
            return

        datos_mesa = entregados.get(mesa_id)
        if not datos_mesa:
            page.snack_bar = ft.SnackBar(ft.Text("Datos de la mesa no encontrados."), bgcolor=ft.Colors.RED)
            page.snack_bar.open = True
            page.update()
            return

        # Validación básica de tarjeta si es necesario
        if metodo_pago == "Tarjeta":
            if not all([campo_nombre.value, campo_numero.value, campo_vencimiento.value, campo_cvv.value]):
                page.snack_bar = ft.SnackBar(ft.Text("Complete todos los campos de la tarjeta."), bgcolor=ft.Colors.RED)
                page.snack_bar.open = True
                page.update()
                return
            if len(campo_numero.value) != 16 or len(campo_cvv.value) != 3 or len(campo_vencimiento.value) != 5:
                page.snack_bar = ft.SnackBar(ft.Text("Datos de tarjeta inválidos."), bgcolor=ft.Colors.RED)
                page.snack_bar.open = True
                page.update()
                return

        # Generar PDF
        archivo = guardar_factura_pdf(mesa_id, datos_mesa, metodo_pago)

        # Eliminar la mesa del archivo entregados
        del entregados[mesa_id]
        guardar_entregados(entregados)

        # Actualizar pantalla
        actualizar_dropdown()
        lista_factura.controls.clear()
        mensaje.value = ""
        enlace_pdf.value = f"Factura generada: {archivo}"
        mostrar_campos_tarjeta(False)
        page.snack_bar = ft.SnackBar(ft.Text("Factura generada y datos eliminados."), bgcolor=ft.Colors.GREEN)
        page.snack_bar.open = True
        page.update()

    dropdown_mesas.on_change = actualizar_detalle_mesa

    return ft.View(
        route="/cobros",
        controls=[
            ft.AppBar(
                title=ft.Text("Cobros y Facturación"),
                leading=ft.IconButton(icon=ft.Icons.ARROW_BACK, on_click=lambda _: page.go("/"))
            ),
            ft.Text("Generar Factura", size=20, weight="bold"),
            dropdown_mesas,
            ft.Row([
                ft.ElevatedButton("Pagar en EFECTIVO", bgcolor=ft.Colors.GREEN, color=ft.Colors.WHITE,
                                  on_click=lambda e: generar_factura("Efectivo")),
                ft.ElevatedButton("Pagar con TARJETA", bgcolor=ft.Colors.BLUE, color=ft.Colors.WHITE,
                                  on_click=lambda e: mostrar_campos_tarjeta(True))
            ]),
            campo_nombre,
            campo_numero,
            campo_vencimiento,
            campo_cvv,
            ft.ElevatedButton("Confirmar pago con tarjeta", visible=True,
                              on_click=lambda e: generar_factura("Tarjeta")),
            ft.Divider(),
            lista_factura,
            enlace_pdf,
            mensaje
        ]
    )
