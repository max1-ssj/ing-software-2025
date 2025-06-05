import flet as ft
import json
import os

inventario_file = "inventario.json"

def cargar_inventario():
    if os.path.exists(inventario_file):
        with open(inventario_file, "r") as f:
            return json.load(f)
    return []

def guardar_inventario(inventario):
    with open(inventario_file, "w") as f:
        json.dump(inventario, f, indent=2)

def normalizar_nombre(nombre):
    return nombre.strip().lower()

def vista_inventario(page: ft.Page):
    inventario = cargar_inventario()
    lista_items = ft.Column()

    modo_operacion = ft.Dropdown(
        label="Modo",
        options=[
            ft.DropdownOption("Agregar"),
            ft.DropdownOption("Modificar"),
            ft.DropdownOption("Eliminar")
        ],
        value="Agregar"
    )

    dropdown_productos = ft.Dropdown(label="Seleccionar producto", visible=False)
    input_producto = ft.TextField(label="Producto")
    input_stock = ft.TextField(label="Stock", keyboard_type="number")
    input_precio = ft.TextField(label="Precio", keyboard_type="number")

    dialog_confirmacion = ft.AlertDialog(
        modal=True,
        title=ft.Text("Confirmar eliminación"),
        content=ft.Text("¿Está seguro que desea eliminar este producto?"),
        actions=[
            ft.TextButton("Cancelar"),
            ft.ElevatedButton("Eliminar", bgcolor=ft.Colors.RED)
        ],
        actions_alignment=ft.MainAxisAlignment.END,
        on_dismiss=lambda e: page.update()
    )

    def actualizar_lista():
        lista_items.controls.clear()
        for item in inventario:
            lista_items.controls.append(
                ft.Text(f"{item['producto']}: {item['stock']} unidades - ${item['precio']:.2f}")
            )
        page.update()

    def actualizar_dropdown():
        dropdown_productos.options = [
            ft.DropdownOption(item["producto"]) for item in inventario
        ]
        dropdown_productos.value = None
        page.update()

    def cambiar_modo(e):
        input_producto.read_only = False
        input_producto.value = ""
        input_stock.value = ""
        input_precio.value = ""
        dropdown_productos.visible = modo_operacion.value in ["Modificar", "Eliminar"]
        input_producto.visible = modo_operacion.value != "Eliminar"
        input_stock.visible = modo_operacion.value != "Eliminar"
        input_precio.visible = modo_operacion.value != "Eliminar"
        actualizar_dropdown()
        page.update()

    def seleccionar_producto(e):
        nombre = dropdown_productos.value
        producto = next((p for p in inventario if p["producto"] == nombre), None)
        if producto:
            input_producto.value = producto["producto"]
            input_stock.value = str(producto["stock"])
            input_precio.value = str(producto["precio"])
            if modo_operacion.value == "Modificar":
                input_producto.read_only = True
            page.update()

    def ejecutar_operacion(e):
        if modo_operacion.value == "Eliminar":
            nombre = dropdown_productos.value
            if not nombre:
                page.snack_bar = ft.SnackBar(ft.Text("Seleccione un producto."), bgcolor=ft.Colors.RED)
                page.snack_bar.open = True
                page.update()
                return
            # Mostrar diálogo de confirmación
            dialog_confirmacion.open = True
            page.update()
            return

        nombre_original = input_producto.value.strip()
        nombre_normalizado = normalizar_nombre(nombre_original)

        if not nombre_original:
            page.snack_bar = ft.SnackBar(ft.Text("El nombre del producto no puede estar vacío."), bgcolor=ft.Colors.RED)
            page.snack_bar.open = True
            page.update()
            return

        try:
            stock = int(input_stock.value)
            precio = float(input_precio.value)
        except ValueError:
            page.snack_bar = ft.SnackBar(ft.Text("Stock o precio inválido. Use solo números."), bgcolor=ft.Colors.RED)
            page.snack_bar.open = True
            page.update()
            return

        if stock < 0 or precio < 0:
            page.snack_bar = ft.SnackBar(ft.Text("El stock y el precio no pueden ser negativos."), bgcolor=ft.Colors.RED)
            page.snack_bar.open = True
            page.update()
            return

        if modo_operacion.value == "Agregar":
            if any(normalizar_nombre(p["producto"]) == nombre_normalizado for p in inventario):
                page.snack_bar = ft.SnackBar(ft.Text("El producto ya existe."), bgcolor=ft.Colors.ORANGE)
            else:
                inventario.append({"producto": nombre_original, "stock": stock, "precio": precio})
                page.snack_bar = ft.SnackBar(ft.Text("Producto agregado."), bgcolor=ft.Colors.GREEN)

        elif modo_operacion.value == "Modificar":
            producto = next((p for p in inventario if normalizar_nombre(p["producto"]) == nombre_normalizado), None)
            if producto:
                producto["stock"] = stock
                producto["precio"] = precio
                page.snack_bar = ft.SnackBar(ft.Text("Producto modificado."), bgcolor=ft.Colors.BLUE)
            else:
                page.snack_bar = ft.SnackBar(ft.Text("Producto no encontrado."), bgcolor=ft.Colors.RED)

        guardar_inventario(inventario)
        actualizar_lista()
        actualizar_dropdown()

        input_producto.value = ""
        input_stock.value = ""
        input_precio.value = ""
        dropdown_productos.value = None
        page.snack_bar.open = True
        page.update()

    def confirmar_eliminacion(e):
        nombre = dropdown_productos.value
        if nombre:
            inventario[:] = [p for p in inventario if p["producto"] != nombre]
            guardar_inventario(inventario)
            page.snack_bar = ft.SnackBar(ft.Text("Producto eliminado."), bgcolor=ft.Colors.RED)
            actualizar_lista()
            actualizar_dropdown()
            dropdown_productos.value = None
            input_producto.value = ""
            input_stock.value = ""
            input_precio.value = ""
            dialog_confirmacion.open = False
            page.snack_bar.open = True
            page.update()

    def cancelar_eliminacion(e):
        dialog_confirmacion.open = False
        page.update()

    modo_operacion.on_change = cambiar_modo
    dropdown_productos.on_change = seleccionar_producto
    dialog_confirmacion.actions[0].on_click = cancelar_eliminacion
    dialog_confirmacion.actions[1].on_click = confirmar_eliminacion

    actualizar_lista()

    return ft.View(
        route="/inventario",
        controls=[
            ft.AppBar(
                title=ft.Text("Gestión de Inventario"),
                leading=ft.IconButton(icon=ft.Icons.ARROW_BACK, on_click=lambda _: page.go("/"))
            ),
            ft.Text("Modo de Operación", size=18, weight="bold"),
            modo_operacion,
            dropdown_productos,
            input_producto,
            input_stock,
            input_precio,
            ft.ElevatedButton("Ejecutar", on_click=ejecutar_operacion, bgcolor=ft.Colors.BLUE, color=ft.Colors.WHITE),
            ft.Divider(),
            ft.Text("Inventario Actual", size=16, weight="bold"),
            lista_items,
            dialog_confirmacion,
        ]
    )
