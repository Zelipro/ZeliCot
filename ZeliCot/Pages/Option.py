import flet as ft
import Dialog as Diag
import sqlite3 as sql
import time as ti
import Save
import Login

class OptionPage:
    def __init__(self, page: ft.Page , on_login_out_success = None):
        self.conn = sql.connect("base.db") #Initiation de la base de donnee
        self.page = page
        self.is_menu_open = True
        self.current_section = "Accueil"
        self.sort_mode = "creation"
        self.selected_cotisation = None
        self.on_login_out_success = on_login_out_success
        self.is_dark_mode = False
        self.build_ui()

    def toggle_theme(self, e=None):
        self.is_dark_mode = not self.is_dark_mode
        if self.is_dark_mode:
            self.page.theme_mode = ft.ThemeMode.DARK
            self.page.bgcolor = "#1A1A2E"
            self.content_container.bgcolor = ft.Colors.with_opacity(0.92, "#1E1E2E")
            self.content_container.border = ft.border.all(1, "#333355")
            self._theme_icon.name = ft.Icons.LIGHT_MODE
            self._theme_text.value = "Mode jour"
        else:
            self.page.theme_mode = ft.ThemeMode.LIGHT
            self.page.bgcolor = "#E8F5E9"
            self.content_container.bgcolor = ft.Colors.WHITE
            self.content_container.border = ft.border.all(1, "#E2E5EC")
            self._theme_icon.name = ft.Icons.DARK_MODE
            self._theme_text.value = "Mode nuit"
        self.page.update()

    def toggle_menu(self, e=None):
        self.is_menu_open = not self.is_menu_open
        self.side_menu.visible = self.is_menu_open
        self.content_overlay.visible = self.is_menu_open
        self.page.update()

    def open_section(self, section_name: str):
        self.current_section = section_name
        self.update_main_content()
        self.is_menu_open = False
        self.side_menu.visible = False
        self.content_overlay.visible = False
        self.page.update()

    def logout_app(self, e=None):
        if callable(self.on_login_out_success):
            self.on_login_out_success()
      
    def close_dialog(self, e=None):
        if self.feedback_dialog is not None:
            self.feedback_dialog.open = False
            self.page.update()


    def show_dialog(self, message: str):
        self.feedback_dialog = ft.AlertDialog(
            title=ft.Text("Information"),
            content=ft.Text(message, color="#1C2233"),
            actions=[ft.TextButton("OK", on_click=self.close_dialog)],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        # Compatibility path for Flet versions where page.dialog is not enough.
        if self.feedback_dialog not in self.page.overlay:
            self.page.overlay.append(self.feedback_dialog)

        self.feedback_dialog.open = True
        self.page.update()
    
    def get_all_info(self, cotisation_name):
        conn = self.conn.cursor()
        conn.execute(f"SELECT name, prix FROM '{cotisation_name}'")
        All = conn.fetchall()
        conn.close()
        return All

    def get_cotisants(self, cotisation_name):
        conn = self.conn.cursor()
        conn.execute(f"SELECT name, prix, date FROM '{cotisation_name}'")
        cotisants = conn.fetchall()
        conn.close()
        return cotisants

    def get_cotisants_with_id(self, cotisation_name):
        conn = self.conn.cursor()
        conn.execute(f"SELECT id, name, prix, date FROM '{cotisation_name}'")
        cotisants = conn.fetchall()
        conn.close()
        return cotisants
    
    def get_all(self):
        conn = self.conn.cursor()
        conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY rowid ASC"
        )
        Tab = [row[0] for row in conn.fetchall()]
        conn.close()
        return Tab

    def search_person_names(self, query: str = ""):
        conn = self.conn.cursor()
        names = set()
        filter_text = (query or "").strip().lower()

        for cotisation_name in self.get_all():
            if filter_text:
                conn.execute(
                    f"SELECT DISTINCT name FROM '{cotisation_name}' WHERE lower(name) LIKE ?",
                    (f"%{filter_text}%",),
                )
            else:
                conn.execute(f"SELECT DISTINCT name FROM '{cotisation_name}'")

            for row in conn.fetchall():
                if row[0]:
                    names.add(row[0])

        conn.close()
        return sorted(list(names), key=lambda n: n.lower())

    def get_person_statistics(self, person_name: str):
        conn = self.conn.cursor()
        stats = []
        total_fois = 0
        total_montant = 0.0

        for cotisation_name in self.get_all():
            conn.execute(
                f"SELECT COUNT(*), COALESCE(SUM(prix), 0) FROM '{cotisation_name}' WHERE lower(name) = lower(?)",
                (person_name,),
            )
            count_value, sum_value = conn.fetchone()

            if count_value and count_value > 0:
                montant = float(sum_value or 0)
                total_fois += int(count_value)
                total_montant += montant
                stats.append(
                    {
                        "cotisation": cotisation_name,
                        "fois": int(count_value),
                        "montant": montant,
                    }
                )

        conn.close()
        return {
            "person_name": person_name,
            "stats": stats,
            "total_fois": total_fois,
            "total_montant": total_montant,
        }

    def get_sorted_cotisations(self, items=None):
        if items is None:
            items = self.get_all()

        if self.sort_mode == "alphabetique":
            return sorted(items, key=lambda item: item.lower())

        return list(items)

    def on_sort_change(self, e):
        self.sort_mode = e.control.value or "creation"
        self.refresh_cotisation_list()
        self.page.update()

    def on_cotisation_select(self, cotisation_name: str):
        def _on_click(e):
            self.selected_cotisation = cotisation_name
            self.show_cotisation_detail(cotisation_name)
        return _on_click

    def show_cotisation_detail(self, cotisation_name: str):
        def editer_person(e):
            self.editer_person(cotisation_name)

        def suprimer_person(e):
            self.suprimer_person(cotisation_name)

        def editer(e):
            def editer_vrai(diag0):
                new_name = diag0.content.value.strip()
                if not new_name:
                    Diag.error_dialog(page=self.page, message="Le nom ne peut pas être vide.")
                    return
                
                existing_tables = self.get_all()
                if new_name in existing_tables and new_name != cotisation_name:
                    Diag.error_dialog(page=self.page, message=f'Une cotisation nommée "{new_name}" existe déjà.')
                    return
                
                if new_name != cotisation_name:
                    conn = self.conn.cursor()
                    conn.execute(f"ALTER TABLE '{cotisation_name}' RENAME TO '{new_name}'")
                    self.conn.commit()
                    conn.close()
                
                diag0.open = False
                self.open_section("Liste des cotisations")
                
            diag5 = Diag.custom_dialog(
                page = self.page,
                title = "Modifier NAME",
                content_widget=ft.TextField(
                    label="Nouveau nom",
                    hint_text="Entrez le nouveau nom de la cotisation...",
                    border_radius=10,
                    value=cotisation_name,
                ),
                actions=[
                    ft.ElevatedButton(
                        "Enregistrer",
                        bgcolor="#2D7D4D",
                        color=ft.Colors.WHITE,
                        on_click=lambda e: editer_vrai(diag5),
                    ),
                    ft.ElevatedButton(
                        "Annuler",
                        on_click=lambda e: setattr(diag5, 'open', False) or self.page.update(),
                    ),
                ]
            )
        def delete_all(e):
            def delete_cotisation(cotisation_name):
                conn = self.conn.cursor()
                conn.execute(f"DROP TABLE IF EXISTS '{cotisation_name}'")
                self.conn.commit()
                conn.close()
                self.open_section("Liste des cotisations")
                
            diag2 = Diag.ask_dialog(
                page = self.page , 
                title = "Confirmation",
                message=f'Voulez-vous vraiment suprimer la cotisation "{cotisation_name}" ?\nToutes les données associées seront perdues.',
                on_oui = lambda e : delete_cotisation(cotisation_name) ,
                on_non = lambda e : setattr(diag2, 'open', False) or self.page.update()
            )
        def total(e):
            All = self.get_all_info(cotisation_name)
            total_prix = sum(float(elmt[1]) for elmt in All)
            
            diag3 = Diag.custom_dialog(
                page = self.page,
                title = "",
                content_widget=ft.Column(
                    [
                        ft.Icon(
                            ft.Icons.INFO_OUTLINE,
                            color="#1F5A35",
                            size=70,
                        ),
                        ft.Row(
                            [
                                ft.Text(
                                    "Total :",
                                    size = 20,
                                    color="#D0F309",
                                    weight=ft.FontWeight.W_600,
                                ),
                                ft.Text(
                                    f"{total_prix:.2f}",
                                    size=16,
                                    color="#08F014" if total_prix > 2000 else "#DC2626",
                                    weight=ft.FontWeight.W_600,
                                )
                            ],
                            alignment=ft.CrossAxisAlignment.CENTER,
                            #horizontal_alignment=ft.MainAxisAlignment.CENTER,
                            ),
 
                    ],
                    height= 150,
                    horizontal_alignment=ft.MainAxisAlignment.CENTER,
                ),
                actions=[
                    ft.ElevatedButton(
                        "Fermer",
                        bgcolor="#2D7D4D",
                        color=ft.Colors.WHITE,
                        on_click=lambda e: setattr(diag3, 'open', False) or self.page.update(),
                    )
                ]
            )
            
        def add(e):
            name_field = ft.TextField(
                label = "Nom de la personne",
                hint_text = "Entrez le nom...",
                border_radius = 10,
            )
            
            prix_field = ft.TextField(
                label = "Prix",
                hint_text = "Prix (valeur numerique)",
                border_radius = 10,
                #input_type=ft.,
                
            )
            
            def Annuler(dig):
                dig.open = False
                self.page.update()
            
            def Save(dig):
                def update(Cotisation_n , elmt , prix , diag2):
                    diag2.open = False
                    self.page.update()
                    
                name = name_field.value.strip()
                prix = prix_field.value.strip()
                if not name or not prix:
                    Diag.error_dialog(page=self.page, message="Tous les champs sont requis.")
                    return
                try:
                    prix_value = float(prix)
                except ValueError:
                    Diag.error_dialog(page=self.page, message="Le prix doit être une valeur numérique.")
                    return
                
                All = self.get_all_info(cotisation_name)
                for elmt in All:
                    if elmt[0] == name:
                        diag2 = Diag.ask_dialog(
                        page = self.page , 
                        title = "Confirmation",
                        message=f'{name} existe déjà \nVoulez-vous ajouter le prix ?\nTotal va faire = {str(float(elmt[1]) + float(prix))}',
                        #on_oui = lambda e : self.modifier(cotisation_name, elmt) ,
                        on_non = lambda e : setattr(diag2, 'open', False) or self.page.update()
                    )
                        return
                
                #Cette partie sera l'enregistrement de la personne 
                conn = self.conn.cursor()
                conn.execute(f"INSERT INTO '{cotisation_name}' (name, prix, date) VALUES (?, ?, ?)", (name, prix_value, ti.strftime("%Y-%m-%d %H:%M:%S")))
                self.conn.commit()
                conn.close()
                
                
                dig.open = False
                self.page.update()
                
                Diag.success_dialog(
                    page = self.page,
                    title = "Succès",
                    message = f"Cotisation de {name} effectué avec succès."
                    
                )
                #self.show_dialog(f"Personne '{name}' ajoutée avec succès à la cotisation '{cotisation_name}'.")

            diag1 = Diag.custom_dialog(
                page = self.page ,
                title = "Ajouter une personne",
                content_widget = ft.Column(
                    [
                        name_field,
                        prix_field,
 
                    ],
                    height = 150,
                ),
                actions = [
                        ft.ElevatedButton(
                            "Ajouter",
                            bgcolor="#2D7D4D",
                            color=ft.Colors.WHITE,
                            on_click=lambda e : Save(diag1),
                            )
                        ,
                        ft.ElevatedButton(
                            "Annuler",
                            on_click=lambda e : Annuler(diag1),
                            )
                        
                        ]
                
            )

        def liste(e):
            self.liste(cotisation_name)

        def generer_rapport(e):
            self.generer_rapport(cotisation_name)

        self.main_body.content = ft.Container(
            expand=True,
            padding=ft.padding.all(10),
            content=ft.Column(
                expand=True,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                scroll=ft.ScrollMode.AUTO,
                alignment =  ft.MainAxisAlignment.START,
                controls=[
                    ft.Row(
                        controls=[
                            ft.IconButton(
                                ft.Icons.ARROW_BACK,
                                icon_size=20,
                                on_click=lambda e: self.open_section("Liste des cotisations"),
                            ),
                            ft.Text(
                                cotisation_name,
                                size=24,
                                color="#1C2233",
                                weight=ft.FontWeight.W_600,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.START,
                    ),
                    ft.Column(
                        spacing=12,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Container(
                                width=300,
                                content=ft.ElevatedButton(
                                    "Ajouter",
                                    width=300,
                                    bgcolor="#2D7D4D",
                                    color=ft.Colors.WHITE,
                                    on_click= add,
                                ),
                            ),
                            ft.Container(
                                width=300,
                                content=ft.ElevatedButton(
                                    "Total",
                                    width=300,
                                    bgcolor="#2D7D4D",
                                    color=ft.Colors.WHITE,
                                    on_click= total,
                                ),
                            ),
                            ft.Container(
                                width=300,
                                content=ft.ElevatedButton(
                                    "Liste",
                                    width=300,
                                    bgcolor="#2D7D4D",
                                    color=ft.Colors.WHITE,
                                    on_click=liste,
                                ),
                            ),
                            ft.Container(
                                width=300,
                                content=ft.ElevatedButton(
                                    "Generer une rapport",
                                    width=300,
                                    bgcolor="#2D7D4D",
                                    color=ft.Colors.WHITE,
                                    on_click=generer_rapport,
                                ),
                            ),
                        ],
                    ),
                    ft.Divider(color="#E2E5EC", height=16),
                    ft.Column(
                        spacing=12,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Container(
                                width=300,
                                content=ft.ElevatedButton(
                                    "Suprimer la cotisation",
                                    width=300,
                                    bgcolor="#DC2626",
                                    color=ft.Colors.WHITE,
                                    on_click= delete_all,
                                ),
                            ),
                            ft.Container(
                                width=300,
                                content=ft.ElevatedButton(
                                    "Modifier la cotisation",
                                    width=300,
                                    bgcolor="#F59E0B",
                                    color=ft.Colors.WHITE,
                                    on_click= editer,
                                ),
                            ),
                            ft.Container(
                                width=300,
                                content=ft.ElevatedButton(
                                    "Modifier une personne",
                                    width=300,
                                    bgcolor="#3B82F6",
                                    color=ft.Colors.WHITE,
                                    on_click= editer_person,
                                ),
                            ),
                            ft.Container(
                                width=300,
                                content=ft.ElevatedButton(
                                    "Suprimer une personne",
                                    width=300,
                                    bgcolor="#EF4444",
                                    color=ft.Colors.WHITE,
                                    on_click=suprimer_person,
                                ),
                            ),
                        ],
                    ),
                ],
            ),
        )
        self.page.update()

    def generer_rapport(self, cotisation_name: str):
        renderers = Save.get_available_renderers()
        locations = Save.get_available_save_locations(self.page)

        if not locations:
            Diag.error_dialog(
                page=self.page,
                message="Aucun emplacement de sauvegarde disponible.",
            )
            return

        renderer_dropdown = ft.Dropdown(
            width=320,
            label="Format de sortie",
            border_radius=10,
            value=renderers[0]["id"],
            color="#152249",
            text_size=14,
            border_color="#C9D1DC",
            focused_border_color="#2D7D4D",
            label_style=ft.TextStyle(color="#6B7280", size=13),
            options=[ft.dropdown.Option(r["id"], r["label"]) for r in renderers],
        )

        location_dropdown = ft.Dropdown(
            width=320,
            label="Emplacement de sauvegarde",
            border_radius=10,
            value=locations[0]["path"],
            color="#1C2233",
            text_size=14,
            border_color="#C9D1DC",
            focused_border_color="#2D7D4D",
            label_style=ft.TextStyle(color="#6B7280", size=13),
            options=[ft.dropdown.Option(loc["path"], loc["label"]) for loc in locations],
        )

        helper_text = ft.Text(
            "Choisissez le format et l'emplacement.",
            size=12,
            color="#6B7280",
        )

        info_text = ft.Text(
            "Choisissez le moteur (ReportLab / FPDF / HTML) et le dossier de sauvegarde.",
            size=13,
            color="#374151",
        )

        dispo_text = ft.Text(
            "Moteurs detectes: " + ", ".join([r["label"] for r in renderers]),
            size=12,
            color="#2D7D4D",
            weight=ft.FontWeight.W_600,
        )

        def enregistrer(e):
            selected_renderer = renderer_dropdown.value
            selected_location = location_dropdown.value

            if not selected_renderer or not selected_location:
                Diag.error_dialog(page=self.page, message="Selection invalide.")
                return

            cotisants = self.get_cotisants(cotisation_name)

            try:
                generated_path = Save.generer_rapport(
                    page=self.page,
                    cotisation_name=cotisation_name,
                    cotisants=cotisants,
                    destination_dir=selected_location,
                    renderer=selected_renderer,
                )
                Diag.success_dialog(
                    page=self.page,
                    title="Succes",
                    message=f"Rapport enregistre: {generated_path}",
                )
            except Exception as ex:
                Diag.error_dialog(
                    page=self.page,
                    title="Erreur",
                    message=str(ex),
                )

        self.main_body.content = ft.Container(
            expand=True,
            padding=ft.padding.all(10),
            content=ft.Column(
                expand=True,
                spacing=16,
                scroll=ft.ScrollMode.AUTO,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Row(
                        controls=[
                            ft.IconButton(
                                ft.Icons.ARROW_BACK,
                                icon_size=20,
                                on_click=lambda e: self.show_cotisation_detail(cotisation_name),
                            ),
                            ft.Text(
                                "Generation du rapport",
                                size=22,
                                color="#1C2233",
                                weight=ft.FontWeight.W_600,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.START,
                    ),
                    ft.Text(
                        f"Motif: {cotisation_name}",
                        size=14,
                        color="#1C2233",
                        weight=ft.FontWeight.W_600,
                    ),
                    info_text,
                    dispo_text,
                    renderer_dropdown,
                    location_dropdown,
                    ft.Row(
                        spacing=10,
                        controls=[
                            ft.ElevatedButton(
                                "Save",
                                bgcolor="#2D7D4D",
                                color=ft.Colors.WHITE,
                                on_click=enregistrer,
                            ),
                            ft.ElevatedButton(
                                "Annuler",
                                on_click=lambda e: self.show_cotisation_detail(cotisation_name),
                            ),
                        ],
                    ),
                ],
            ),
        )

        self.page.update()

    def imprimer_statistique_personne(self, person_data: dict):
        renderers = Save.get_available_renderers()
        locations = Save.get_available_save_locations(self.page)

        if not locations:
            Diag.error_dialog(page=self.page, message="Aucun emplacement de sauvegarde disponible.")
            return

        renderer_dropdown = ft.Dropdown(
            width=320,
            label="Format de sortie",
            border_radius=10,
            value=renderers[0]["id"],
            color="#C8CCD6",
            text_size=14,
            border_color="#C9D1DC",
            focused_border_color="#2D7D4D",
            label_style=ft.TextStyle(color="#6B7280", size=13),
            options=[ft.dropdown.Option(r["id"], r["label"]) for r in renderers],
        )

        location_dropdown = ft.Dropdown(
            width=320,
            label="Emplacement de sauvegarde",
            border_radius=10,
            value=locations[0]["path"],
            color="#BBC2D6",
            text_size=14,
            border_color="#C9D1DC",
            focused_border_color="#2D7D4D",
            label_style=ft.TextStyle(color="#6B7280", size=13),
            options=[ft.dropdown.Option(loc["path"], loc["label"]) for loc in locations],
        )

        helper_text = ft.Text(
            "Choisissez le format et l'emplacement.",
            size=12,
            color="#6B7280",
        )

        def save_stat(e):
            selected_renderer = renderer_dropdown.value
            selected_location = location_dropdown.value

            if not selected_renderer or not selected_location:
                Diag.error_dialog(page=self.page, message="Selection invalide.")
                return

            try:
                output_path = Save.generer_rapport_stat_personne(
                    page=self.page,
                    person_name=person_data["person_name"],
                    stats=person_data["stats"],
                    total_fois=person_data["total_fois"],
                    total_montant=person_data["total_montant"],
                    destination_dir=selected_location,
                    renderer=selected_renderer,
                )
                Diag.success_dialog(
                    page=self.page,
                    title="Succes",
                    message=f"Rapport enregistre: {output_path}",
                )
            except Exception as ex:
                Diag.error_dialog(page=self.page, title="Erreur", message=str(ex))

        diag = Diag.custom_dialog(
            page=self.page,
            title="Impression",
            content_widget=ft.Column(
                controls=[helper_text, renderer_dropdown, location_dropdown],
                spacing=12,
                tight=True,
            ),
            actions=[
                ft.ElevatedButton(
                    "Save",
                    bgcolor="#2D7D4D",
                    color=ft.Colors.WHITE,
                    on_click=save_stat,
                ),
                ft.ElevatedButton(
                    "Annuler",
                    on_click=lambda e: setattr(diag, 'open', False) or self.page.update(),
                ),
            ],
        )

    def show_person_stat_details(self, person_name: str):
        person_data = self.get_person_statistics(person_name)
        stats_list = ft.ListView(
            expand=True,
            spacing=10,
            padding=ft.padding.only(top=8, bottom=8),
        )

        if not person_data["stats"]:
            stats_list.controls = [
                ft.Container(
                    padding=ft.padding.only(top=20),
                    content=ft.Text(
                        "Aucune cotisation trouvee pour cette personne.",
                        size=16,
                        color="#6B7280",
                        text_align=ft.TextAlign.CENTER,
                    ),
                )
            ]
        else:
            stats_list.controls = [
                ft.Container(
                    border_radius=12,
                    bgcolor="#F7FAF8",
                    border=ft.border.all(1, "#D8E6DC"),
                    padding=ft.padding.symmetric(horizontal=14, vertical=12),
                    content=ft.Column(
                        spacing=6,
                        controls=[
                            ft.Text(
                                stat_item["cotisation"],
                                size=16,
                                color="#1C2233",
                                weight=ft.FontWeight.W_600,
                            ),
                            ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                controls=[
                                    ft.Text(
                                        f"Nombre de fois: {stat_item['fois']}",
                                        size=13,
                                        color="#334155",
                                    ),
                                    ft.Text(
                                        f"Montant: {stat_item['montant']:.2f}",
                                        size=13,
                                        color="#2D7D4D",
                                    ),
                                ],
                            ),
                        ],
                    ),
                )
                for stat_item in person_data["stats"]
            ]

        self.main_body.content = ft.Container(
            expand=True,
            padding=ft.padding.all(10),
            content=ft.Column(
                expand=True,
                spacing=16,
                controls=[
                    ft.Row(
                        controls=[
                            ft.IconButton(
                                ft.Icons.ARROW_BACK,
                                icon_size=20,
                                on_click=lambda e: self.show_statistique(),
                            ),
                            ft.Text(
                                f"Statistique - {person_name}",
                                size=22,
                                color="#1C2233",
                                weight=ft.FontWeight.W_600,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.START,
                    ),
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Text(
                                f"Total cotisations: {person_data['total_fois']}",
                                size=14,
                                color="#334155",
                                weight=ft.FontWeight.W_600,
                            ),
                            ft.Text(
                                f"Total paye: {person_data['total_montant']:.2f}",
                                size=14,
                                color="#2D7D4D",
                                weight=ft.FontWeight.W_600,
                            ),
                        ],
                    ),
                    ft.ElevatedButton(
                        "Imprimer les informations",
                        width=260,
                        bgcolor="#2D7D4D",
                        color=ft.Colors.WHITE,
                        on_click=lambda e: self.imprimer_statistique_personne(person_data),
                    ),
                    ft.Container(expand=True, content=stats_list),
                ],
            ),
        )
        self.page.update()

    def show_statistique(self):
        search_field = ft.TextField(
            width=380,
            label="Rechercher une personne",
            hint_text="Tapez un nom...",
            border_radius=10,
            color="#1C2233",
            border_color="#C9D1DC",
            focused_border_color="#2D7D4D",
            prefix_icon=ft.Icons.SEARCH,
        )

        person_list = ft.ListView(
            expand=True,
            spacing=10,
            padding=ft.padding.only(top=8, bottom=8),
        )

        def on_person_click(person_name: str):
            return lambda e: self.show_person_stat_details(person_name)

        def refresh_person_list(e=None):
            query = (search_field.value or "").strip()
            names = self.search_person_names(query)

            if not names:
                person_list.controls = [
                    ft.Container(
                        padding=ft.padding.only(top=20),
                        content=ft.Text(
                            "Aucune personne trouvee.",
                            size=16,
                            color="#6B7280",
                            text_align=ft.TextAlign.CENTER,
                        ),
                    )
                ]
                self.page.update()
                return

            person_list.controls = [
                ft.Container(
                    border_radius=12,
                    bgcolor="#F7FAF8",
                    border=ft.border.all(1, "#D8E6DC"),
                    padding=ft.padding.symmetric(horizontal=14, vertical=12),
                    on_click=on_person_click(name),
                    content=ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Text(
                                name,
                                size=16,
                                color="#1C2233",
                                weight=ft.FontWeight.W_600,
                            ),
                            ft.Icon(ft.Icons.CHEVRON_RIGHT, color="#2D7D4D", size=18),
                        ],
                    ),
                )
                for name in names
            ]

            self.page.update()

        search_field.on_change = refresh_person_list

        self.main_body.content = ft.Container(
            expand=True,
            padding=ft.padding.all(10),
            content=ft.Column(
                expand=True,
                spacing=16,
                controls=[
                    ft.Text(
                        "Statistique",
                        size=22,
                        color="#1C2233",
                        weight=ft.FontWeight.W_600,
                    ),
                    search_field,
                    ft.Container(expand=True, content=person_list),
                ],
            ),
        )

        refresh_person_list()

    def suprimer_person(self, cotisation_name: str):
        person_list = ft.ListView(
            expand=True,
            spacing=10,
            padding=ft.padding.only(top=8, bottom=8),
        )

        def delete_person(person_id: int, person_name: str, diag):
            conn = self.conn.cursor()
            conn.execute(f"DELETE FROM '{cotisation_name}' WHERE id = ?", (person_id,))
            self.conn.commit()
            conn.close()

            diag.open = False
            self.page.update()

            Diag.success_dialog(
                page=self.page,
                title="Succes",
                message=f"{person_name} a ete supprimee avec succes.",
            )
            refresh_person_list()

        def ask_delete(person_id: int, person_name: str):
            diag = Diag.ask_dialog(
                page=self.page,
                title="Confirmation",
                message=f'Voulez-vous vraiment suprimer {person_name} ?',
                on_oui=lambda e: delete_person(person_id, person_name, diag),
                on_non=lambda e: setattr(diag, 'open', False) or self.page.update(),
            )

        def on_person_click(person_id: int, person_name: str):
            return lambda e: ask_delete(person_id, person_name)

        def refresh_person_list(e=None):
            people = self.get_cotisants_with_id(cotisation_name)

            if not people:
                person_list.controls = [
                    ft.Container(
                        padding=ft.padding.only(top=20),
                        content=ft.Text(
                            "Aucune personne enregistree.",
                            size=16,
                            color="#6B7280",
                            text_align=ft.TextAlign.CENTER,
                        ),
                    )
                ]
                self.page.update()
                return

            person_list.controls = [
                ft.Container(
                    border_radius=12,
                    bgcolor="#F7FAF8",
                    border=ft.border.all(1, "#D8E6DC"),
                    padding=ft.padding.symmetric(horizontal=14, vertical=12),
                    on_click=on_person_click(person_id, name),
                    content=ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Column(
                                spacing=4,
                                controls=[
                                    ft.Text(
                                        name,
                                        size=16,
                                        color="#1C2233",
                                        weight=ft.FontWeight.W_600,
                                    ),
                                    ft.Text(
                                        f"Montant: {float(prix):.2f}",
                                        size=13,
                                        color="#2D7D4D",
                                    ),
                                ],
                            ),
                            ft.Icon(ft.Icons.DELETE, color="#EF4444", size=18),
                        ],
                    ),
                )
                for person_id, name, prix, _date in people
            ]

            self.page.update()

        self.main_body.content = ft.Container(
            expand=True,
            padding=ft.padding.all(10),
            content=ft.Column(
                expand=True,
                spacing=16,
                controls=[
                    ft.Row(
                        controls=[
                            ft.IconButton(
                                ft.Icons.ARROW_BACK,
                                icon_size=20,
                                on_click=lambda e: self.show_cotisation_detail(cotisation_name),
                            ),
                            ft.Text(
                                "Suppression",
                                size=22,
                                color="#1C2233",
                                weight=ft.FontWeight.W_600,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.START,
                    ),
                    ft.Container(expand=True, content=person_list),
                ],
            ),
        )

        refresh_person_list()

    def editer_person(self, cotisation_name: str):
        person_list = ft.ListView(
            expand=True,
            spacing=10,
            padding=ft.padding.only(top=8, bottom=8),
        )

        def open_edit_dialog(person_id: int, current_name: str, current_prix):
            name_field = ft.TextField(
                label="Nom",
                hint_text="Entrez le nom...",
                border_radius=10,
                value=current_name,
            )

            prix_field = ft.TextField(
                label="Prix",
                hint_text="Prix (valeur numerique)",
                border_radius=10,
                value=str(current_prix),
            )

            def save(diag):
                new_name = (name_field.value or "").strip()
                new_prix = (prix_field.value or "").strip()

                if not new_name or not new_prix:
                    Diag.error_dialog(page=self.page, message="Tous les champs sont requis.")
                    return

                try:
                    prix_value = float(new_prix)
                except ValueError:
                    Diag.error_dialog(page=self.page, message="Le prix doit etre une valeur numerique.")
                    return

                conn = self.conn.cursor()
                conn.execute(
                    f"UPDATE '{cotisation_name}' SET name = ?, prix = ? WHERE id = ?",
                    (new_name, prix_value, person_id),
                )
                self.conn.commit()
                conn.close()

                diag.open = False
                self.page.update()
                Diag.success_dialog(
                    page=self.page,
                    title="Succes",
                    message=f"La personne {new_name} a ete modifiee avec succes.",
                )
                refresh_person_list()

            def cancel(diag):
                diag.open = False
                self.page.update()

            diag_edit = Diag.custom_dialog(
                page=self.page,
                title="Modifier une personne",
                content_widget=ft.Column(
                    controls=[name_field, prix_field],
                    height=150,
                ),
                actions=[
                    ft.ElevatedButton(
                        "Enregistrer",
                        bgcolor="#2D7D4D",
                        color=ft.Colors.WHITE,
                        on_click=lambda e: save(diag_edit),
                    ),
                    ft.ElevatedButton(
                        "Annuler",
                        on_click=lambda e: cancel(diag_edit),
                    ),
                ],
            )

        def refresh_person_list(e=None):
            people = self.get_cotisants_with_id(cotisation_name)

            if not people:
                person_list.controls = [
                    ft.Container(
                        padding=ft.padding.only(top=20),
                        content=ft.Text(
                            "Aucune personne enregistree.",
                            size=16,
                            color="#6B7280",
                            text_align=ft.TextAlign.CENTER,
                        ),
                    )
                ]
                self.page.update()
                return

            person_list.controls = [
                ft.Container(
                    border_radius=12,
                    bgcolor="#F7FAF8",
                    border=ft.border.all(1, "#D8E6DC"),
                    padding=ft.padding.symmetric(horizontal=14, vertical=12),
                    on_click=lambda e, pid=person_id, n=name, p=prix: open_edit_dialog(pid, n, p),
                    content=ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Column(
                                spacing=4,
                                controls=[
                                    ft.Text(
                                        name,
                                        size=16,
                                        color="#1C2233",
                                        weight=ft.FontWeight.W_600,
                                    ),
                                    ft.Text(
                                        f"Montant: {float(prix):.2f}",
                                        size=13,
                                        color="#2D7D4D",
                                    ),
                                ],
                            ),
                            ft.Icon(ft.Icons.EDIT, color="#3B82F6", size=18),
                        ],
                    ),
                )
                for person_id, name, prix, _date in people
            ]

            self.page.update()

        self.main_body.content = ft.Container(
            expand=True,
            padding=ft.padding.all(10),
            content=ft.Column(
                expand=True,
                spacing=16,
                controls=[
                    ft.Row(
                        controls=[
                            ft.IconButton(
                                ft.Icons.ARROW_BACK,
                                icon_size=20,
                                on_click=lambda e: self.show_cotisation_detail(cotisation_name),
                            ),
                            ft.Text(
                                f"Modification",
                                size=22,
                                color="#1C2233",
                                weight=ft.FontWeight.W_600,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.START,
                    ),
                    ft.Container(expand=True, content=person_list),
                ],
            ),
        )

        refresh_person_list()

    def liste(self, cotisation_name: str):
        search_field = ft.TextField(
            expand=True,
            label="Recherche",
            hint_text="Tapez un nom...",
            border_radius=10,
            color="#1C2233",
            border_color="#C9D1DC",
            focused_border_color="#2D7D4D",
            prefix_icon=ft.Icons.SEARCH,
        )

        sort_by_date = ft.Dropdown(
            width=220,
            value="recent",
            text_size=14,
            color="#1C2233",
            border_color="#C9D1DC",
            focused_border_color="#2D7D4D",
            options=[
                ft.dropdown.Option("recent", "Date la plus recente"),
                ft.dropdown.Option("ancien", "Date la plus ancienne"),
            ],
        )

        person_list = ft.ListView(
            expand=True,
            spacing=10,
            padding=ft.padding.only(top=8, bottom=8),
        )

        def refresh_person_list(e=None):
            query = (search_field.value or "").strip().lower()
            sort_mode = sort_by_date.value or "recent"

            people = self.get_cotisants(cotisation_name)

            if query:
                people = [
                    person
                    for person in people
                    if query in (person[0] or "").lower()
                ]

            people = sorted(
                people,
                key=lambda item: item[2] or "",
                reverse=(sort_mode == "recent"),
            )

            if not people:
                person_list.controls = [
                    ft.Container(
                        padding=ft.padding.only(top=20),
                        content=ft.Text(
                            "Aucune personne trouvee.",
                            size=16,
                            color="#6B7280",
                            text_align=ft.TextAlign.CENTER,
                        ),
                    )
                ]
                self.page.update()
                return

            person_list.controls = [
                ft.Container(
                    border_radius=12,
                    bgcolor="#F7FAF8",
                    border=ft.border.all(1, "#D8E6DC"),
                    padding=ft.padding.symmetric(horizontal=14, vertical=12),
                    content=ft.Column(
                        spacing=6,
                        controls=[
                            ft.Text(
                                name,
                                size=16,
                                color="#1C2233",
                                weight=ft.FontWeight.W_600,
                            ),
                            ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                controls=[
                                    ft.Text(
                                        f"Montant: {float(prix):.2f}",
                                        size=13,
                                        color="#2D7D4D",
                                    ),
                                    ft.Text(
                                        date,
                                        size=12,
                                        color="#6B7280",
                                    ),
                                ],
                            ),
                        ],
                    ),
                )
                for name, prix, date in people
            ]

            self.page.update()

        search_field.on_change = refresh_person_list
        sort_by_date.on_change = refresh_person_list

        self.main_body.content = ft.Container(
            expand=True,
            padding=ft.padding.all(10),
            content=ft.Column(
                expand=True,
                spacing=16,
                controls=[
                    ft.Row(
                        controls=[
                            ft.IconButton(
                                ft.Icons.ARROW_BACK,
                                icon_size=20,
                                on_click=lambda e: self.show_cotisation_detail(cotisation_name),
                            ),
                            ft.Text(
                                f"Liste - {cotisation_name}",
                                size=22,
                                color="#1C2233",
                                weight=ft.FontWeight.W_600,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.START,
                    ),
                    ft.Column(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[search_field, sort_by_date],
                    ),
                    ft.Container(expand=True, content=person_list),
                ],
            ),
        )

        refresh_person_list()

    def refresh_cotisation_list(self, items=None):
        cotisations = self.get_sorted_cotisations(items)

        if not cotisations:
            self.cotisation_list.controls = [
                ft.Container(
                    padding=ft.padding.only(top=20),
                    content=ft.Text(
                        "Aucune cotisation enregistree.",
                        size=16,
                        color="#6B7280",
                        text_align=ft.TextAlign.CENTER,
                    ),
                )
            ]
            return

        self.cotisation_list.controls = [
            ft.Container(
                border_radius=12,
                bgcolor="#F7FAF8",
                border=ft.border.all(1, "#D8E6DC"),
                padding=ft.padding.symmetric(horizontal=14, vertical=12),
                on_click=self.on_cotisation_select(name),
                content=ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Text(name, size=16, color="#1C2233", weight=ft.FontWeight.W_600),
                        ft.Icon(ft.Icons.CHEVRON_RIGHT, color="#2D7D4D", size=18),
                    ],
                ),
            )
            for name in cotisations
        ]

    def Go(self, e):
        if self.motif_field.value.strip() == "":
            Diag.error_dialog(page = self.page , message= "Le motif ne peut pas être vide.")
        else:
            Liste = self.get_all()
            if self.motif_field.value in Liste : 
                Diag.error_dialog(page = self.page , message= "Ce motif existe déjà")
            
            else:
                motif_name = self.motif_field.value
                conn = self.conn.cursor()
                conn.execute(f"CREATE TABLE IF NOT EXISTS '{motif_name}' (id INTEGER PRIMARY KEY AUTOINCREMENT , name TEXT NOT NULL , prix REAL NOT NULL , date TEXT NOT NULL)")
                self.conn.commit()
                conn.close()
                self.motif_field.value = ""
                self.refresh_cotisation_list()
                
                Diag.success_dialog(self.page , title="Succes" , message=f"Le motif '{motif_name}' est enregistre avec succes." )
    
    def update_main_content(self):
        if self.current_section == "Créer une Nouvelle cotisation":
            self.main_body.content = ft.Container(
                expand=True,
                padding=ft.padding.all(10),
                content=ft.Column(
                    controls=[
                        ft.Text(
                            "Entrer le motif de cotisation",
                            size=22,
                            color="#1C2233",
                            weight=ft.FontWeight.W_600,
                            text_align=ft.TextAlign.CENTER,
                        ),
                        self.motif_field,
                        ft.ElevatedButton(
                            "Enregistrer",
                            icon=ft.Icons.SAVE,
                            bgcolor="#2D7D4D",
                            color=ft.Colors.WHITE,
                            on_click=self.Go,
                        ),
                    ],
                    spacing=16,
                    scroll=ft.ScrollMode.AUTO,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            )
            return
        
        if self.current_section == "Liste des cotisations":
            self.sort_dropdown.value = self.sort_mode
            self.refresh_cotisation_list()
            self.main_body.content = ft.Container(
                expand=True,
                padding=ft.padding.all(10),
                content=ft.Column(
                    expand=True,
                    controls=[
                        ft.Text(
                            "Liste des cotisations",
                            size=22,
                            color="#1C2233",
                            weight=ft.FontWeight.W_600,
                        ),
                        ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=[
                                ft.Text(
                                    "Classer la liste",
                                    size=14,
                                    color="#6B7280",
                                    weight=ft.FontWeight.W_500,
                                ),
                                self.sort_dropdown,
                            ],
                        ),
                        ft.Container(
                            expand=True,
                            content=self.cotisation_list,
                        ),
                    ],
                    spacing=16,
                ),
            )
            return

        if self.current_section == "Statistique":
            self.show_statistique()
            return
        
        self.section_title.value = self.current_section
        self.main_body.content = self.section_title

    def build_ui(self):
        def section_click(section_name: str):
            return lambda e: self.open_section(section_name)

        drawer_items = [
            ft.ListTile(
                leading=ft.Icon(ft.Icons.ADD_CIRCLE_OUTLINE, color=ft.Colors.WHITE70, size=18),
                title=ft.Text("Créer une Nouvelle cotisation", color=ft.Colors.WHITE, size=13),
                dense=True,
                on_click=section_click("Créer une Nouvelle cotisation"),
            ),
            ft.ListTile(
                leading=ft.Icon(ft.Icons.FORMAT_LIST_BULLETED, color=ft.Colors.WHITE70, size=18),
                title=ft.Text("Liste des cotisations", color=ft.Colors.WHITE, size=13),
                dense=True,
                on_click=section_click("Liste des cotisations"),
            ),
            ft.ListTile(
                leading=ft.Icon(ft.Icons.INSERT_CHART_OUTLINED_ROUNDED, color=ft.Colors.WHITE70, size=18),
                title=ft.Text("Statistique", color=ft.Colors.WHITE, size=13),
                dense=True,
                on_click=section_click("Statistique"),
            ),
        ]

        menu_controls = [
            ft.Row(
                controls=[
                    ft.Container(
                        width=40,
                        height=40,
                        border_radius=20,
                        border=ft.border.all(2, ft.Colors.WHITE24),
                        alignment=ft.Alignment(0, 0),
                        bgcolor=ft.Colors.WHITE10,
                        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
                        content=ft.Icon(ft.Icons.PERSON, color=ft.Colors.WHITE, size=22),
                    ),
                    ft.Text("Elisée (Zeli)", color=ft.Colors.WHITE, size=16, weight=ft.FontWeight.W_600),
                ],
            ),
            ft.Divider(color=ft.Colors.WHITE24, height=20),
            ft.Column(spacing=4, controls=drawer_items),
        ]

        menu_controls.append(ft.Container(expand=True))

        self._theme_icon = ft.Icon(ft.Icons.DARK_MODE, color=ft.Colors.WHITE70, size=18)
        self._theme_text = ft.Text("Mode nuit", color=ft.Colors.WHITE, size=13)

        menu_controls.extend(
            [
                ft.Divider(color=ft.Colors.WHITE24, height=16),
                ft.ListTile(
                    leading=self._theme_icon,
                    title=self._theme_text,
                    dense=True,
                    on_click=self.toggle_theme,
                ),
                ft.ListTile(
                    leading=ft.Icon(ft.Icons.LOGOUT, color=ft.Colors.WHITE70, size=18),
                    title=ft.Text("Log Out", color=ft.Colors.WHITE, size=13),
                    dense=True,
                    on_click=self.logout_app,
                ),
            ]
        )

        self.side_menu = ft.Container(
            width=240,
            border_radius=ft.border_radius.only(top_right=24, bottom_right=24),
            gradient=ft.LinearGradient(
                begin=ft.Alignment(0, -1),
                end=ft.Alignment(0, 1),
                colors=["#2D7D4D", "#1F5A35"],
            ),
            padding=ft.padding.only(top=24, left=14, right=10, bottom=14),
            visible=self.is_menu_open,
            content=ft.Column(
                expand=True,
                controls=menu_controls,
            ),
        )

        self.section_title = ft.Text(
            self.current_section,
            size=36,
            color="#1C2233",
            weight=ft.FontWeight.W_700,
            text_align=ft.TextAlign.CENTER,
        )

        self.feedback_dialog = None

        self.motif_field = ft.TextField(
            width=380,
            label="Motif de cotisation",
            hint_text="Entrez le motif...",
            border_radius=10,
            color="#1C2233",
            label_style=ft.TextStyle(color="#6B7280"),
            hint_style=ft.TextStyle(color="#9CA3AF"),
            cursor_color="#1F5A35",
            border_color="#C9D1DC",
            focused_border_color="#2D7D4D",
        )

        self.sort_dropdown = ft.Dropdown(
            width=210,
            value=self.sort_mode,
            text_size=14,
            color="#1C2233",
            border_color="#C9D1DC",
            focused_border_color="#2D7D4D",
            options=[
                ft.dropdown.Option("creation", "Ordre de creation"),
                ft.dropdown.Option("alphabetique", "Ordre alphabetique"),
            ],
        )
        self.sort_dropdown.on_change = self.on_sort_change

        self.cotisation_list = ft.ListView(
            expand=True,
            spacing=10,
            padding=ft.padding.only(top=8, bottom=8),
        )

        self.main_body = ft.Container(
            expand=True,
            alignment=ft.Alignment(0, 0),
        )

        self.update_main_content()

        content_main = ft.Column(
            expand=True,
            controls=[
                ft.Row(
                    controls=[
                        ft.IconButton(
                            icon=ft.Icons.INFO_OUTLINE,
                            icon_size=30,
                            icon_color="#1F5A35",
                            tooltip="Afficher/Masquer le menu",
                            on_click=self.toggle_menu,
                        )
                    ],
                    alignment=ft.MainAxisAlignment.START,
                ),
                self.main_body,
            ],
            alignment=ft.MainAxisAlignment.START,
        )

        self.content_overlay = ft.Container(
            expand=True,
            visible=self.is_menu_open,
            bgcolor=ft.Colors.with_opacity(0.18, ft.Colors.BLACK),
            on_click=self.toggle_menu,
        )

        content_stack = ft.Stack(
            expand=True,
            controls=[
                content_main,
                self.content_overlay,
            ],
        )

        self.content_container = ft.Container(
            expand=True,
            margin=ft.margin.only(left=14, right=14, top=34, bottom=18),
            border_radius=16,
            bgcolor=ft.Colors.WHITE,
            border=ft.border.all(1, "#E2E5EC"),
            alignment=ft.Alignment(0, 0),
            content=content_stack,
        )

        self.main_container = ft.Container(
            expand=True,
            bgcolor="#E8F5E9",
            content=ft.SafeArea(
                expand=True,
                content=ft.Row(
                    expand=True,
                    spacing=0,
                    controls=[
                        self.side_menu,
                        self.content_container,
                    ],
                ),
            ),
        )
    
    def get_main_container(self):
        return self.main_container


def option_page(page: ft.Page , on_login_out_success = None) -> ft.Control:
    option_ui = OptionPage(page, on_login_out_success=on_login_out_success)
    return option_ui.get_main_container()


def main(page: ft.Page , on_login_out_success = None):
    page.title = "Option"
    page.padding = 0
    page.spacing = 0
    page.bgcolor = "#E8F5E9"
    page.add(option_page(page , on_login_out_success=on_login_out_success))
