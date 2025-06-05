import flet as ft
import json
import os
from datetime import datetime

pedidos_file = "pedidos.json"
inventario_file = "inventario.json"
entregados_file = "entregados.json"

def cargar_pedidos():
    if os.path.exists(pedidos_file):
        with open(pedidos_file, "r") as f:
            return json.load(f)
    return []

def guardar_pedidos(pedidos):
    with open(pedidos_file, "w") as f:
        json.dump(pedidos, f)

def cargar_inventario():
    if os.path.exists(inventario_file):
        with open(inventario_file, "r") as f:
            return json.load(f)
    return []

def guardar_inventario(inventario):
    with open(inventario_file, "w") as f:
        json.dump(inventario, f)

def cargar_entregados():
    if os.path.exists(entregados_file):
        with open(entregados_file, "r") as f:
            return json.load(f)
    return {}

def guardar_entregados(entregados):
    with open(entregados_file, "w") as f:
        json.dump(entregados, f, indent=2)

def vista_pedidos(page: ft.Page):
    pedidos = cargar_pedidos()
    pedidos_entregados = []

    input_nombre = ft.TextField(label="Nombre del cliente")
    input_mesa = ft.TextField(label="Número de mesa (1-50)", keyboard_type="number")
    input_cantidad = ft.TextField(label="Cantidad", width=100, visible=False, keyboard_type="number")

    producto_seleccionado = ft.Text("", visible=False)
    producto_info = ft.Column([producto_seleccionado, input_cantidad])

    lista_productos = ft.Column(visible=False)
    lista_pedidos = ft.Column()
    lista_entregados = ft.Column()

    index_edicion = {"valor": -1}
    producto_actual = {"nombre": "", "stock": 0}
    stock_restaurado = {"producto": "", "cantidad": 0}

    def seleccionar_producto(e):
        lista_productos.controls.clear()
        inventario = cargar_inventario()

        for item in inventario:
            def crear_handler(producto):
                return lambda e: on_producto_elegido(producto)

            btn = ft.ElevatedButton(
                text=f"{item['producto']} (Stock: {item['stock']})",
                on_click=crear_handler(item),
                disabled=item["stock"] == 0
            )
            lista_productos.controls.append(btn)

        lista_productos.visible = True
        page.update()

    def on_producto_elegido(producto):
        producto_actual["nombre"] = producto["producto"]
        producto_actual["stock"] = producto["stock"]

        producto_seleccionado.value = f"{producto['producto']} (Stock: {producto['stock']})"
        producto_seleccionado.visible = True
        input_cantidad.visible = True
        lista_productos.visible = False

        producto_info.update()
        page.update()

    def actualizar_lista():
        lista_pedidos.controls.clear()
        for i, p in enumerate(pedidos):
            lista_pedidos.controls.append(
                ft.Row([
                    ft.Text(f"Mesa {p['mesa']} - {p['nombre']}: {p['detalle']} - Estado: {p['estado']}"),
                    ft.ElevatedButton("Modificar", on_click=lambda e, ix=i: editar(ix), bgcolor=ft.Colors.AMBER, color=ft.Colors.WHITE),
                    ft.ElevatedButton("Cancelar", on_click=lambda e, ix=i: cancelar(ix), bgcolor=ft.Colors.RED, color=ft.Colors.WHITE),
                    ft.ElevatedButton("Pedido Listo", on_click=lambda e, ix=i: entregar(ix), bgcolor=ft.Colors.GREEN, color=ft.Colors.WHITE),
                ])
            )
        page.update()

    def actualizar_lista_entregados():
        lista_entregados.controls.clear()
        for p in pedidos_entregados:
            lista_entregados.controls.append(
                ft.Text(f"Mesa {p['mesa']} - {p['nombre']}: {p['detalle']} - ✅ ENTREGADO ({p['fecha_hora']})")
            )
        page.update()

    def enviar(e):
        if input_nombre.value and producto_actual["nombre"] and input_mesa.value and input_cantidad.value:
            try:
                num_mesa = int(input_mesa.value)
                cantidad = int(input_cantidad.value)
                if not (1 <= num_mesa <= 50 and cantidad > 0):
                    raise ValueError
            except ValueError:
                page.snack_bar = ft.SnackBar(ft.Text("Número de mesa o cantidad inválida."), bgcolor=ft.Colors.RED)
                page.snack_bar.open = True
                page.update()
                return

            if cantidad > producto_actual["stock"]:
                page.snack_bar = ft.SnackBar(ft.Text(f"No hay suficiente stock. Stock disponible: {producto_actual['stock']}"), bgcolor=ft.Colors.RED)
                page.snack_bar.open = True
                page.update()
                return

            inventario = cargar_inventario()
            for item in inventario:
                if item["producto"] == producto_actual["nombre"]:
                    item["stock"] -= cantidad
                    break

            if stock_restaurado["producto"]:
                for item in inventario:
                    if item["producto"] == stock_restaurado["producto"]:
                        item["stock"] += stock_restaurado["cantidad"]
                        break
                stock_restaurado["producto"] = ""
                stock_restaurado["cantidad"] = 0

            guardar_inventario(inventario)

            detalle = f"{producto_actual['nombre']} x {cantidad}"

            if index_edicion["valor"] == -1:
                pedidos.append({
                    "nombre": input_nombre.value,
                    "detalle": detalle,
                    "producto": producto_actual["nombre"],
                    "mesa": num_mesa,
                    "estado": "En preparación"
                })
            else:
                pedidos[index_edicion["valor"]].update({
                    "nombre": input_nombre.value,
                    "detalle": detalle,
                    "producto": producto_actual["nombre"],
                    "mesa": num_mesa
                })
                index_edicion["valor"] = -1

            guardar_pedidos(pedidos)

            input_nombre.value = ""
            input_mesa.value = ""
            input_cantidad.value = ""
            input_cantidad.visible = False
            producto_seleccionado.value = ""
            producto_seleccionado.visible = False
            producto_actual["nombre"] = ""
            producto_actual["stock"] = 0
            producto_info.update()
            actualizar_lista()
            page.update()

    def cancelar(index):
        if 0 <= index < len(pedidos):
            pedidos.pop(index)
            guardar_pedidos(pedidos)
            actualizar_lista()

    def entregar(index):
        if 0 <= index < len(pedidos):
            pedido = pedidos.pop(index)
            pedido["estado"] = "Entregado"
            pedido["fecha_hora"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            pedidos_entregados.append(pedido)

            mesa = str(pedido["mesa"])
            producto_nombre = pedido.get("producto", "")
            try:
                _, cantidad_str = pedido["detalle"].split(" x ")
                cantidad = int(cantidad_str)
            except Exception:
                cantidad = 1

            inventario = cargar_inventario()
            precio_unitario = 0.0
            for item in inventario:
                if item["producto"] == producto_nombre:
                    precio_unitario = float(item.get("precio", 0.0))
                    break
            total = cantidad * precio_unitario

            entregados = cargar_entregados()
            if mesa not in entregados:
                entregados[mesa] = {
                    "productos": [],
                    "cantidad_total": 0,
                    "monto_total": 0.0
                }

            productos_mesa = entregados[mesa]["productos"]
            producto_existente = next((p for p in productos_mesa if p["producto"] == producto_nombre), None)

            if producto_existente:
                producto_existente["cantidad"] += cantidad
                producto_existente["monto_total"] += total
            else:
                productos_mesa.append({
                    "producto": producto_nombre,
                    "cantidad": cantidad,
                    "monto_total": total
                })

            entregados[mesa]["cantidad_total"] += cantidad
            entregados[mesa]["monto_total"] += total

            guardar_entregados(entregados)
            guardar_pedidos(pedidos)
            actualizar_lista()
            actualizar_lista_entregados()

    def editar(index):
        p = pedidos[index]
        input_nombre.value = p["nombre"]
        input_mesa.value = str(p["mesa"])

        # Extraemos datos del producto anterior
        try:
            producto, cantidad_str = p["detalle"].split(" x ")
            cantidad_anterior = int(cantidad_str)
        except:
            producto = p.get("producto", "")
            cantidad_anterior = 0

        inventario = cargar_inventario()
        for item in inventario:
            if item["producto"] == producto:
                item["stock"] += cantidad_anterior
                producto_actual["stock"] = item["stock"]
                producto_actual["nombre"] = producto
                producto_seleccionado.value = f"{producto} (Stock: {item['stock']})"
                producto_seleccionado.visible = True
                input_cantidad.visible = True
                stock_restaurado["producto"] = producto
                stock_restaurado["cantidad"] = cantidad_anterior
                break

        input_cantidad.value = str(cantidad_anterior)
        producto_info.update()
        index_edicion["valor"] = index
        page.update()

    actualizar_lista()

    return ft.View(
        route="/pedidos",
        controls=[
            ft.AppBar(title=ft.Text("Gestión de Pedidos"), leading=ft.IconButton(icon=ft.Icons.ARROW_BACK, on_click=lambda _: page.go("/"))),
            ft.Text("Toma de Pedidos", size=20, weight="bold"),
            input_nombre,
            ft.ElevatedButton("Seleccionar producto", on_click=seleccionar_producto),
            lista_productos,
            producto_info,
            input_mesa,
            ft.ElevatedButton("Enviar pedido", on_click=enviar, bgcolor=ft.Colors.BLUE, color=ft.Colors.WHITE),
            ft.Divider(),
            ft.Text("Pedidos en preparación", size=16, weight="bold"),
            lista_pedidos,
            ft.Divider(),
            ft.Text("Pedidos entregados", size=16, weight="bold"),
            lista_entregados,
        ]
    )
