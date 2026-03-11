# ZeliCot

Application de gestion de cotisations développée en Python avec [Flet](https://flet.dev/), compatible bureau (Linux/Windows/macOS) et Android.

---

## Fonctionnalités

- **Authentification** — Page de connexion avec compte maître et compte utilisateur sauvegardable.
- **Gestion des cotisations** — Créer, renommer et supprimer des motifs de cotisation.
- **Gestion des cotisants** — Ajouter, modifier et supprimer des cotisants (nom, montant, date) dans chaque cotisation.
- **Liste triable** — Tri par ordre de création ou par ordre alphabétique.
- **Statistiques** — Vue par personne : nombre de participations et montant total versé sur l'ensemble des cotisations.
- **Export de rapports** — Génération de rapports en HTML (natif) ou en PDF via ReportLab ou FPDF.
- **Mode sombre / clair** — Bascule de thème intégrée.

---

## Structure du projet

```
ZeliCot/
├── main.py              # Point d'entrée, navigation entre les pages
├── base.db              # Base de données SQLite (créée au 1er lancement)
├── iden.txt             # Identifiants utilisateur sauvegardés (créé à la connexion)
├── assets/              # Ressources (icône, splash, etc.)
└── Pages/
    ├── Login.py         # Page d'authentification
    ├── Option.py        # Page principale (gestion des cotisations)
    ├── Save.py          # Génération et export des rapports
    └── Dialog.py        # Composants de dialogues réutilisables
```

---

## Prérequis

- Python 3.10+
- [Flet](https://pypi.org/project/flet/) : `pip install flet`
- *(Optionnel)* [ReportLab](https://pypi.org/project/reportlab/) pour l'export PDF : `pip install reportlab`
- *(Optionnel)* [FPDF2](https://pypi.org/project/fpdf2/) pour l'export PDF alternatif : `pip install fpdf2`

---

## Lancement

```bash
# Cloner / se placer dans le dossier
cd ZeliCot

# Installer les dépendances
pip install flet

# Lancer l'application
python main.py
```

---

## Connexion

| Compte | Identifiant | Mot de passe |
|--------|-------------|--------------|
| Maître | `Deg` | `Deg` |
| Utilisateur | *(configurable)* | *(configurable)* |

Les identifiants du compte utilisateur sont sauvegardés localement dans `iden.txt`.

---

## Export des rapports

Les rapports sont exportés dans le dossier choisi (Documents, Téléchargements, Bureau, etc.).

| Format | Dépendance requise |
|--------|-------------------|
| HTML | Aucune (natif) |
| PDF (ReportLab) | `pip install reportlab` |
| PDF (FPDF) | `pip install fpdf2` |

---

## Build Android (APK)

Flet permet de packager l'application en APK natif Android :

```bash
pip install flet
flet build apk
```

Consultez la [documentation officielle Flet](https://flet.dev/docs/publish/android) pour les détails de configuration (SDK Android, etc.).

---

## Technologies utilisées

- [Flet](https://flet.dev/) — Framework UI Python multi-plateformes
- [SQLite3](https://docs.python.org/3/library/sqlite3.html) — Base de données embarquée
- [ReportLab](https://www.reportlab.com/) / [FPDF2](https://py-fpdf2.readthedocs.io/) — Génération PDF (optionnel)
