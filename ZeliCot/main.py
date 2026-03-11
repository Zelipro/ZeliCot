import sys
import os

# Ajouter le dossier Pages/ au chemin de recherche des modules
_pages_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Pages")
if _pages_dir not in sys.path:
    sys.path.insert(0, _pages_dir)

import flet as ft
import Login
import Option


def main(page: ft.Page):
    # ── Paramètres globaux de la page (important pour Android) ──────────────
    page.title = "ZeliCot"
    page.padding = 0
    page.spacing = 0
    page.bgcolor = ft.Colors.TRANSPARENT
    page.theme_mode = ft.ThemeMode.DARK

    # Adapte la mise en page quand le clavier Android remonte
    page.on_keyboard_hide = lambda e: page.update()

    # ── Navigation ───────────────────────────────────────────────────────────
    def go_to_option():
        """Charge la page principale après connexion."""
        page.controls.clear()
        page.bgcolor = "#E8F5E9"
        page.theme_mode = ft.ThemeMode.LIGHT
        page.add(Option.option_page(page , on_login_out_success=go_to_login))
        page.update()

    def go_to_login():
        """Retourne sur la page de login (logout)."""
        page.controls.clear()
        page.bgcolor = ft.Colors.TRANSPARENT
        page.theme_mode = ft.ThemeMode.DARK
        page.add(Login.build_login_page(page, on_login_success=go_to_option))
        page.update()

    # ── Démarrage : on commence toujours par le login ────────────────────────
    go_to_login()


# ── Point d'entrée ───────────────────────────────────────────────────────────
# Pour Android (APK Flet), ft.app() doit être appelé sans view= ou avec
# view=ft.AppView.FLET_APP pour que l'app s'affiche en plein écran natif.
if __name__ == "__main__":
    ft.app(
        target=main,
        assets_dir="assets",   # dossier pour icône, splash, etc. (créé si besoin)
    )
