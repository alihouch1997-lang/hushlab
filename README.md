# Site Hushlab

Site vitrine de [Hushlab](https://hushlab.ma) — Rabat, Maroc.
Sites web, QR codes et NFC, réseaux sociaux, intelligence artificielle,
création d'entreprise.

## Démarrer en local

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements-build.txt
.venv/bin/python build.py          # CSS, images WebP, favicon, carte de partage
HUSHLAB_DEBUG=1 .venv/bin/python app.py
```

Le site répond alors sur http://localhost:5001.

## Vérifier avant chaque envoi

```bash
.venv/bin/pytest -q          # 48 tests
.venv/bin/ruff check .       # conventions et motifs à risque
.venv/bin/python build.py    # régénère les fichiers statiques
```

`build.py` est à relancer après toute modification des templates, des tokens
de design ou des photos : le CSS est compilé, pas chargé chez le visiteur.

## Organisation

| Fichier | Rôle |
|---|---|
| `contenu.py` | Tout le texte publié : services, offres, articles, coordonnées |
| `app.py` | Routes et rendu |
| `securite.py` | CSRF, en-têtes de sécurité, limitation de débit, authentification |
| `validation.py` | Nettoyage et contrôle des données entrantes |
| `donnees.py` | Stockage SQLite : demandes clients et scans de QR codes |
| `config.py` | Réglages, lus dans l'environnement |
| `design_tokens.py` | Couleurs, ombres, typographie du design system |
| `build.py` | Chaîne de build : CSS, images, icônes |

Pour corriger un texte ou un tarif, un seul fichier à ouvrir : `contenu.py`.

## Réglages

Copier `.env.exemple` en `.env` et le remplir. Aucun secret ne doit être
versionné : `.env` et `hushlab.db` sont exclus par `.gitignore`.

| Variable | Rôle |
|---|---|
| `HUSHLAB_SECRET_KEY` | Signature des jetons CSRF. Obligatoire en ligne. |
| `HUSHLAB_ADMIN_MOTDEPASSE` | Accès à `/admin`. Vide = administration fermée. |
| `HUSHLAB_DEBUG` | `1` en développement seulement, **jamais** en ligne. |
| `HUSHLAB_PROXYS` | Nombre de reverse proxys en amont. `1` chez Render. |
| `HUSHLAB_BASE` | Chemin de la base, à placer sur un disque persistant. |
| `HUSHLAB_HOTES` | Domaines autorisés, séparés par des virgules. Indispensable en ligne. |
| `SMTP_*` | Notification des demandes par email. |

## Mise en ligne

`render.yaml` décrit le service : sur Render, « New + » → « Blueprint »
crée tout à partir de ce fichier. Deux blocs marqués **À L'ACHAT** sont à
décommenter au passage en formule payante, pour que les demandes clients
survivent aux mises à jour.

Le site est servi par gunicorn (`Procfile`), jamais par le serveur de
développement de Flask.

## Sauvegarde

`hushlab.db` contient les demandes de vos clients. C'est le seul fichier
irremplaçable du projet : tout le reste se régénère avec `build.py`.
