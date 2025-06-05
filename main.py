import flet as ft
from pedidos import vista_pedidos
from cobros import vista_cobros
from inventario import vista_inventario
from reservas import vista_reservas  

def main(page: ft.Page):
    page.title = "Sistema de Restaurante"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window_width = 1000
    page.window_height = 700

    def navegar(ruta):
        page.views.clear()

        if ruta == "/":
            page.views.append(
                ft.View(
                    route="/",
                    controls=[
                        ft.AppBar(title=ft.Text("Sistema Restaurante")),
                        ft.Column(
                            [
                                ft.Text("Seleccione una opción", size=20, weight="bold"),
                                ft.ElevatedButton("Gestión de Pedidos", on_click=lambda _: page.go("/pedidos"), bgcolor=ft.Colors.BLUE, color=ft.Colors.WHITE),
                                ft.ElevatedButton("Cobros y Facturación", on_click=lambda _: page.go("/cobros"), bgcolor=ft.Colors.GREEN, color=ft.Colors.WHITE),
                                ft.ElevatedButton("Gestión de Inventario", on_click=lambda _: page.go("/inventario"), bgcolor=ft.Colors.AMBER, color=ft.Colors.WHITE),
                                ft.ElevatedButton("Gestión de Reservas", on_click=lambda _: page.go("/reservas"), bgcolor=ft.Colors.PURPLE, color=ft.Colors.WHITE),
                            ],
                            spacing=20,
                            alignment=ft.MainAxisAlignment.CENTER,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER
                        )
                    ],
                    vertical_alignment=ft.MainAxisAlignment.CENTER
                )
            )

        elif ruta == "/pedidos":
            page.views.append(vista_pedidos(page))
        elif ruta == "/cobros":
            page.views.append(vista_cobros(page))
        elif ruta == "/inventario":
            page.views.append(vista_inventario(page))
        elif ruta == "/reservas":
            page.views.append(vista_reservas(page))

        page.update()

    page.on_route_change = lambda e: navegar(e.route)
    page.go("/")

ft.app(target=main)
