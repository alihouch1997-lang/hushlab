"""Accès aux données : demandes clients et scans de QR codes.

SQLite via la bibliothèque standard — aucun serveur à installer. Le choix se
justifie tant que le site tient sur une machine : quelques dizaines de milliers
de lignes et un seul processus d'écriture. Au-delà, la couche est assez fine
pour passer à PostgreSQL sans toucher aux vues.

Toutes les requêtes sont paramétrées : aucune valeur venue de l'utilisateur
n'est concaténée dans une chaîne SQL.
"""

import csv
import io
import sqlite3
from collections.abc import Iterator
from contextlib import closing, contextmanager
from datetime import UTC, datetime, timedelta, timezone

from config import Config

# Le Maroc est à UTC+1 toute l'année : on stocke en UTC, on affiche en local.
DECALAGE_LOCAL = timezone(timedelta(hours=1))

SCHEMA = """
CREATE TABLE IF NOT EXISTS demandes (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    nom        TEXT    NOT NULL,
    email      TEXT    NOT NULL,
    telephone  TEXT,
    service    TEXT,
    message    TEXT    NOT NULL,
    origine    TEXT,
    statut     TEXT    NOT NULL DEFAULT 'nouveau'
               CHECK (statut IN ('nouveau', 'traite')),
    cree_le    TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS scans (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    code     TEXT NOT NULL,
    cree_le  TEXT NOT NULL
);

-- Index alignés sur les requêtes réellement exécutées : filtrage par statut,
-- tri par date décroissante, agrégation des scans par code.
CREATE INDEX IF NOT EXISTS idx_demandes_statut  ON demandes(statut);
CREATE INDEX IF NOT EXISTS idx_demandes_cree_le ON demandes(cree_le DESC);
CREATE INDEX IF NOT EXISTS idx_scans_code       ON scans(code);
"""


@contextmanager
def connexion() -> Iterator[sqlite3.Connection]:
    """Ouvre une connexion, valide la transaction, puis **ferme** la connexion.

    `with sqlite3.connect(...)` valide la transaction mais ne ferme pas la
    connexion : sur un serveur au long cours, les descripteurs de fichiers
    s'accumulent jusqu'à épuisement. `closing` corrige cela.
    """
    with closing(sqlite3.connect(Config.BASE_SQLITE, timeout=5)) as cx:
        cx.row_factory = sqlite3.Row
        cx.execute("PRAGMA foreign_keys = ON")
        with cx:                       # transaction : commit ou rollback
            yield cx


def initialiser() -> None:
    """Crée les tables et les index. Idempotent : appelé à chaque démarrage."""
    with closing(sqlite3.connect(Config.BASE_SQLITE)) as cx:
        # WAL : les lectures ne bloquent plus l'écriture en cours, ce qui
        # évite les « database is locked » dès qu'un visiteur envoie le
        # formulaire pendant que l'admin consulte la liste.
        cx.execute("PRAGMA journal_mode = WAL")
        cx.execute("PRAGMA synchronous = NORMAL")
        cx.executescript(SCHEMA)


def _maintenant() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def en_heure_locale(horodatage: str) -> str:
    """Convertit un horodatage UTC stocké en date lisible à Rabat."""
    try:
        instant = datetime.fromisoformat(horodatage)
    except ValueError:
        return horodatage
    return instant.astimezone(DECALAGE_LOCAL).strftime("%d/%m/%Y à %H:%M")


# --- Demandes ---------------------------------------------------------------

def enregistrer_demande(*, nom: str, email: str, telephone: str, service: str,
                        message: str, origine: str) -> int:
    """Enregistre une demande et renvoie son identifiant."""
    with connexion() as cx:
        curseur = cx.execute(
            "INSERT INTO demandes (nom, email, telephone, service, message, origine, cree_le)"
            " VALUES (?, ?, ?, ?, ?, ?, ?)",
            (nom, email, telephone, service, message, origine, _maintenant()),
        )
        return curseur.lastrowid


def lister_demandes(*, statut: str | None = None, limite: int = 50,
                    decalage: int = 0) -> list[sqlite3.Row]:
    """Renvoie une page de demandes, les plus récentes d'abord.

    La pagination n'est pas une coquetterie : sans elle, la page
    d'administration charge un jour plusieurs milliers de lignes d'un coup.
    """
    requete = "SELECT * FROM demandes"
    parametres: list = []
    if statut:
        requete += " WHERE statut = ?"
        parametres.append(statut)
    requete += " ORDER BY id DESC LIMIT ? OFFSET ?"
    parametres += [limite, decalage]
    with connexion() as cx:
        return cx.execute(requete, parametres).fetchall()


def changer_statut(identifiant: int, statut: str) -> bool:
    """Change le statut d'une demande. Renvoie False si l'identifiant n'existe pas."""
    if statut not in {"nouveau", "traite"}:
        raise ValueError(f"Statut inconnu : {statut!r}")
    with connexion() as cx:
        curseur = cx.execute(
            "UPDATE demandes SET statut = ? WHERE id = ?", (statut, identifiant))
        return curseur.rowcount > 0


def tableau_de_bord(limite: int = 50) -> dict:
    """Tout ce qu'affiche l'administration, en **une seule** connexion.

    Trois appels séparés ouvraient trois connexions par affichage de page ;
    ici les trois requêtes partagent la même, ce qui divise par trois le coût
    d'ouverture et garantit une vue cohérente.
    """
    with connexion() as cx:
        demandes = cx.execute(
            "SELECT * FROM demandes ORDER BY id DESC LIMIT ?", (limite,)).fetchall()
        compteurs = {ligne["statut"]: ligne["n"] for ligne in cx.execute(
            "SELECT statut, COUNT(*) AS n FROM demandes GROUP BY statut")}
        scans = {ligne["code"]: ligne["n"] for ligne in cx.execute(
            "SELECT code, COUNT(*) AS n FROM scans GROUP BY code")}
    compteurs["total"] = sum(compteurs.values())
    return {"demandes": demandes, "compteurs": compteurs, "scans": scans}


def exporter_csv() -> str:
    """Export tableur de toutes les demandes, séparateur point-virgule (Excel FR)."""
    tampon = io.StringIO()
    colonnes = ["id", "cree_le", "statut", "nom", "email", "telephone",
                "service", "message", "origine"]
    plume = csv.writer(tampon, delimiter=";")
    plume.writerow(colonnes)
    with connexion() as cx:
        for ligne in cx.execute("SELECT * FROM demandes ORDER BY id DESC"):
            plume.writerow([ligne[colonne] for colonne in colonnes])
    return tampon.getvalue()


# --- Scans de QR codes ------------------------------------------------------

def enregistrer_scan(code: str) -> None:
    with connexion() as cx:
        cx.execute("INSERT INTO scans (code, cree_le) VALUES (?, ?)",
                   (code, _maintenant()))


def compter_scans() -> dict[str, int]:
    with connexion() as cx:
        return {ligne["code"]: ligne["n"] for ligne in cx.execute(
            "SELECT code, COUNT(*) AS n FROM scans GROUP BY code")}
