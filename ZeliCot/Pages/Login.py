import os
import flet as ft
import Dialog as Diag

MASTER_USERNAME = "Deg"
MASTER_PASSWORD = "Deg"
IDENTITY_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "iden.txt"))


global user_enter, pass_enter
user_enter, pass_enter = "", ""


def New_modif(e):
	global user_enter, pass_enter
	if e.control.hint_text == "Username":
		user_enter = e.control.value
	elif e.control.hint_text == "Password":
		pass_enter = e.control.value


def _read_identity():
	if not os.path.exists(IDENTITY_FILE):
		return "", ""

	with open(IDENTITY_FILE, "r", encoding="utf-8") as file:
		raw = file.readline().strip()

	if not raw:
		return "", ""

	if "|" in raw:
		username, password = raw.split("|", 1)
		return username.strip(), password

	if ":" in raw:
		username, password = raw.split(":", 1)
		return username.strip(), password

	return raw.strip(), ""


def _write_identity(username: str, password: str):
	with open(IDENTITY_FILE, "w", encoding="utf-8") as file:
		file.write(f"{username}|{password}")


def build_login_page(page: ft.Page, on_login_success=None) -> ft.Control:
	page.title = "Login"
	page.padding = 0
	page.spacing = 0
	page.bgcolor = ft.Colors.TRANSPARENT
	page.theme_mode = ft.ThemeMode.DARK

	password_visible = False

	username_field = ft.TextField(
		hint_text="Username",
		border=ft.InputBorder.NONE,
		text_size=12,
		cursor_color=ft.Colors.WHITE70,
		hint_style=ft.TextStyle(color=ft.Colors.WHITE54, size=11),
		color=ft.Colors.WHITE,
		content_padding=ft.padding.only(left=0, right=6, top=12, bottom=12),
		expand=True,
		bgcolor=ft.Colors.TRANSPARENT,
		on_change=New_modif,
	)

	password_field = ft.TextField(
		hint_text="Password",
		password=True,
		can_reveal_password=False,
		border=ft.InputBorder.NONE,
		text_size=12,
		cursor_color=ft.Colors.WHITE70,
		hint_style=ft.TextStyle(color=ft.Colors.WHITE54, size=11),
		color=ft.Colors.WHITE,
		content_padding=ft.padding.only(left=0, right=6, top=12, bottom=12),
		expand=True,
		bgcolor=ft.Colors.TRANSPARENT,
		on_change=New_modif,
	)

	def toggle_password_visibility(e):
		nonlocal password_visible
		password_visible = not password_visible
		password_field.password = not password_visible
		eye_button.icon = (
			ft.Icons.VISIBILITY_OFF_OUTLINED if password_visible else ft.Icons.VISIBILITY_OUTLINED
		)
		page.update()

	eye_button = ft.IconButton(
		icon=ft.Icons.VISIBILITY_OUTLINED,
		icon_size=16,
		icon_color=ft.Colors.WHITE,
		on_click=toggle_password_visibility,
	)

	def go_to_option():
		if callable(on_login_success):
			on_login_success()

	def attempt_login(e):
		username = (username_field.value or "").strip()
		password = password_field.value or ""

		if username == MASTER_USERNAME and password == MASTER_PASSWORD:
			Diag.success_dialog(
				page,
				title="Succes",
				message="Bienvenue Maitre Elisee\nFaites comme chez vous !",
				on_ok=lambda _e: go_to_option(),
			)
			return

		saved_username, saved_password = _read_identity()
		if saved_username and username == saved_username and password == saved_password:
			Diag.success_dialog(
				page,
				title="Succes",
				message=f"Bienvenue {username}",
				on_ok=lambda _e: go_to_option(),
			)
			return

		Diag.error_dialog(
			page,
			title="Erreur",
			message="Nom d'utilisateur ou mot de passe incorrect.",
		)

	return ft.Container(
		expand=True,
		gradient=ft.LinearGradient(
			begin=ft.Alignment(-1, -1),
			end=ft.Alignment(1, 1),
			colors=["#031B2A", "#022E3A", "#0A3556", "#071F3A"],
		),
		content=ft.SafeArea(
			expand=True,
			content=ft.Stack(
				expand=True,
				controls=[
					ft.Container(
						alignment=ft.Alignment(0, 0),
						padding=20,
						content=ft.Container(
							width=340,
							padding=ft.padding.symmetric(horizontal=22, vertical=26),
							border_radius=22,
							bgcolor=ft.Colors.with_opacity(0.22, ft.Colors.BLACK),
							blur=10,
							content=ft.Column(
								horizontal_alignment=ft.CrossAxisAlignment.CENTER,
								tight=True,
								controls=[
									ft.Text(
										"ZELICOT LOGIN",
										size=20,
										weight=ft.FontWeight.W_700,
										color=ft.Colors.WHITE,
									),
									ft.Container(height=18),
									ft.Container(
										width=40,
										height=40,
										border_radius=20,
										bgcolor=ft.Colors.with_opacity(0.26, ft.Colors.WHITE),
										alignment=ft.Alignment(0, 0),
										content=ft.Icon(
											ft.Icons.PERSON_OUTLINE,
											color=ft.Colors.WHITE,
											size=23,
										),
									),
									ft.Container(height=16),
									ft.Container(
										height=42,
										padding=ft.padding.only(left=10, right=8),
										border_radius=22,
										bgcolor=ft.Colors.with_opacity(0.18, ft.Colors.WHITE),
										content=ft.Row(
											controls=[
												ft.Icon(
													ft.Icons.PERSON_OUTLINE,
													color=ft.Colors.WHITE60,
													size=18,
												),
												username_field,
											],
											vertical_alignment=ft.CrossAxisAlignment.CENTER,
										),
									),
									ft.Container(height=12),
									ft.Container(
										height=42,
										padding=ft.padding.only(left=10, right=0),
										border_radius=22,
										bgcolor=ft.Colors.with_opacity(0.18, ft.Colors.WHITE),
										content=ft.Row(
											controls=[
												ft.Icon(
													ft.Icons.KEY_OUTLINED,
													color=ft.Colors.WHITE60,
													size=18,
												),
												password_field,
												eye_button,
											],
											vertical_alignment=ft.CrossAxisAlignment.CENTER,
										),
									),
									ft.Container(height=18),
									ft.Container(
										width=190,
										height=36,
										ink=True,
										alignment=ft.Alignment(0, 0),
										border_radius=20,
										bgcolor="#E7E7E7",
										content=ft.Text(
											"LOGIN",
											color="#021427",
											weight=ft.FontWeight.BOLD,
											size=13,
										),
										on_click=attempt_login,
									),
								],
							),
						),
					),
				],
			),
		),
	)


def main(page: ft.Page):
	page.add(build_login_page(page))




