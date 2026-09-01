"""Suite de tests du site Hushlab.

    .venv/bin/pytest -q

Chaque test de sécurité correspond à une faille réellement trouvée lors de
l'audit : ils échouent si la protection disparaît d'une révision à l'autre.
"""

import os
import pathlib
import re
import time

import pytest

os.environ.setdefault("HUSHLAB_SECRET_KEY", "cle-de-test")
os.environ.setdefault("HUSHLAB_ADMIN_MOTDEPASSE", "motdepasse-de-test")
os.environ.setdefault("HUSHLAB_BASE", "/tmp/hushlab-test.db")

import donnees  # noqa: E402
import securite  # noqa: E402
import validation  # noqa: E402
from app import app  # noqa: E402
from config import Config  # noqa: E402


@pytest.fixture()
def client(tmp_path, monkeypatch):
    """Client de test sur une base neuve, isolée à chaque test."""
    monkeypatch.setattr(Config, "BASE_SQLITE", tmp_path / "test.db")
    donnees.initialiser()
    securite.reinitialiser_limites()   # les compteurs sont partagés par processus
    # Le délai anti-robot est éprouvé par un test dédié ; ailleurs il ne ferait
    # qu'imposer deux secondes d'attente à chaque cas.
    monkeypatch.setattr(Config, "DELAI_MINIMUM_FORMULAIRE", 0)
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def _jeton(client) -> str:
    page = client.get("/").data.decode()
    return re.search(r'name="csrf" value="([^"]+)"', page).group(1)


def _demande_valide(client) -> dict:
    return {"nom": "Karim Benali", "email": "karim@resto.ma",
            "message": "Je voudrais un menu à scanner pour mon restaurant.",
            "csrf": _jeton(client), "horodatage": str(int(time.time()) - 5)}


# --- Pages publiques --------------------------------------------------------

@pytest.mark.parametrize("chemin", [
    "/", "/blog", "/blog/menu-qr-restaurant", "/sitemap.xml", "/robots.txt",
    "/qr/contact.svg", "/qr/avis-google.svg",
])
def test_pages_repondent(client, chemin):
    assert client.get(chemin).status_code == 200


def test_page_inconnue_rend_une_page_lisible(client):
    reponse = client.get("/blog/nexiste-pas")
    assert reponse.status_code == 404
    assert b"Hushlab" in reponse.data          # mise en page conservée


# --- Sécurité : en-têtes ----------------------------------------------------

@pytest.mark.parametrize("entete", [
    "Content-Security-Policy", "X-Content-Type-Options",
    "Referrer-Policy", "X-Frame-Options", "Permissions-Policy",
])
def test_entetes_de_securite_presents(client, entete):
    assert entete in client.get("/").headers


def test_csp_autorise_nos_scripts_par_nonce(client):
    reponse = client.get("/")
    politique = reponse.headers["Content-Security-Policy"]
    nonce = re.search(r"'nonce-([^']+)'", politique).group(1)
    # Le même nonce doit figurer sur les balises script de la page.
    assert f'nonce="{nonce}"' in reponse.data.decode()
    assert "object-src 'none'" in politique


def test_admin_jamais_mis_en_cache(client):
    reponse = client.get("/admin", headers=_auth())
    assert "no-store" in reponse.headers["Cache-Control"]


# --- Sécurité : CSRF --------------------------------------------------------

def test_contact_refuse_sans_jeton(client):
    donnees_envoyees = _demande_valide(client)
    del donnees_envoyees["csrf"]
    assert client.post("/contact", data=donnees_envoyees).status_code == 403


def test_contact_refuse_jeton_forge(client):
    assert client.post("/contact", data=dict(_demande_valide(client),
                                             csrf="jeton-inventé")).status_code == 403


def test_contact_refuse_origine_etrangere(client):
    reponse = client.post("/contact", data=_demande_valide(client),
                          headers={"Origin": "https://attaquant.example"})
    assert reponse.status_code == 403


def test_contact_accepte_jeton_valide(client):
    assert client.post("/contact", data=_demande_valide(client)).status_code == 302
    assert donnees.tableau_de_bord()["compteurs"]["total"] == 1


# --- Sécurité : anti-robots et limitation de débit --------------------------

def test_leurre_ignore_silencieusement(client):
    envoi = dict(_demande_valide(client), site_web="http://spam.example")
    assert client.post("/contact", data=envoi).status_code == 302
    assert donnees.tableau_de_bord()["compteurs"].get("total", 0) == 0


def test_limitation_de_debit_sur_le_formulaire(client):
    codes = [client.post("/contact", data=_demande_valide(client)).status_code
             for _ in range(Config.DEMANDES_PAR_MINUTE + 2)]
    assert 429 in codes, "aucune limitation de débit appliquée"


# --- Sécurité : administration ---------------------------------------------

def _auth(motdepasse: str = "motdepasse-de-test") -> dict:
    import base64
    jeton = base64.b64encode(f"admin:{motdepasse}".encode()).decode()
    return {"Authorization": f"Basic {jeton}"}


def test_admin_exige_le_mot_de_passe(client):
    assert client.get("/admin").status_code == 401


def test_admin_accepte_le_bon_mot_de_passe(client):
    assert client.get("/admin", headers=_auth()).status_code == 200


def test_admin_bride_les_tentatives(client):
    codes = [client.get("/admin", headers=_auth("faux")).status_code
             for _ in range(Config.ESSAIS_ADMIN_PAR_MINUTE + 2)]
    assert 429 in codes, "le mot de passe admin est attaquable par dictionnaire"


def test_changement_de_statut_protege_par_csrf(client):
    client.post("/contact", data=_demande_valide(client))
    sans_jeton = client.post("/admin/demande/1/traite", headers=_auth())
    assert sans_jeton.status_code == 403


# --- Validation des entrées -------------------------------------------------

def test_email_invalide_refuse(client):
    reponse = client.post("/contact", data=dict(_demande_valide(client),
                                                email="pas-un-email"))
    assert reponse.status_code == 400


def test_message_geant_tronque_avant_stockage():
    champs, erreurs = validation.valider_demande(
        {"nom": "Ali", "email": "a@b.ma", "message": "x" * 1_000_000}, set())
    assert not erreurs
    assert len(champs["message"]) == Config.LONGUEURS_MAX["message"]


def test_service_trafique_neutralise():
    champs, _ = validation.valider_demande(
        {"nom": "Ali", "email": "a@b.ma", "message": "x" * 20,
         "service": "<script>alert(1)</script>"}, {"sites-web"})
    assert champs["service"] == ""


def test_saut_de_ligne_retire_des_champs_simples():
    assert "\n" not in validation.nettoyer("Karim\nBcc: victime@x.ma", 120)
    assert "\r" not in validation.entete_email_sur("Karim\r\nBcc: victime@x.ma")


# --- QR codes ---------------------------------------------------------------

def test_code_qr_inconnu_renvoie_404(client):
    assert client.get("/qr/inexistant.svg").status_code == 404
    assert client.get("/r/inexistant").status_code == 404


def test_redirection_limitee_aux_destinations_declarees(client):
    reponse = client.get("/r/whatsapp")
    assert reponse.status_code == 302
    assert reponse.headers["Location"].startswith("https://wa.me/")


def test_scan_comptabilise(client):
    client.get("/r/whatsapp")
    client.get("/r/whatsapp")
    assert donnees.compter_scans()["whatsapp"] == 2


# --- Couche de données ------------------------------------------------------

def test_connexions_fermees(client):
    """Sans fermeture explicite, les descripteurs s'accumulent."""
    import gc
    import sqlite3
    for _ in range(30):
        donnees.tableau_de_bord()
    gc.collect()
    ouvertes = [o for o in gc.get_objects() if isinstance(o, sqlite3.Connection)]
    assert ouvertes == []


def test_index_utilise_pour_le_filtrage(client):
    import sqlite3
    with sqlite3.connect(Config.BASE_SQLITE) as cx:
        plan = cx.execute("EXPLAIN QUERY PLAN "
                          "SELECT * FROM demandes WHERE statut='nouveau'").fetchall()
    assert "idx_demandes_statut" in str(plan)


def test_statut_invalide_refuse_par_la_couche_donnees():
    with pytest.raises(ValueError):
        donnees.changer_statut(1, "supprime")


def test_heure_affichee_en_heure_locale():
    assert donnees.en_heure_locale("2026-08-31T14:29:00+00:00").endswith("15:29")


# --- Mise en ligne ----------------------------------------------------------

def test_sans_proxy_declare_les_entetes_transmis_sont_ignores(client):
    """Défaut sûr : sans proxy déclaré, X-Forwarded-For ne doit rien changer.

    Sinon n'importe qui falsifierait son adresse IP et contournerait la
    limitation de débit en changeant d'en-tête à chaque requête.
    """
    codes = []
    for i in range(Config.DEMANDES_PAR_MINUTE + 2):
        reponse = client.post("/contact", data=_demande_valide(client),
                              headers={"X-Forwarded-For": f"10.0.0.{i}"})
        codes.append(reponse.status_code)
    assert 429 in codes, "une IP falsifiée a contourné la limitation de débit"


def test_base_de_donnees_deplacable_hors_du_code():
    """Sur un hébergeur, la base doit vivre sur un disque persistant."""
    assert "HUSHLAB_BASE" in pathlib.Path("config.py").read_text(encoding="utf-8")


def test_commande_de_demarrage_utilise_gunicorn():
    """Le serveur de développement de Flask ne doit jamais servir en production."""
    procfile = pathlib.Path("Procfile").read_text(encoding="utf-8")
    assert procfile.startswith("web: gunicorn")
    assert "app:app" in procfile


def test_application_demarre_avec_un_proxy_declare(monkeypatch):
    """Charge app.py avec HUSHLAB_PROXYS=1, le chemin réellement utilisé en ligne.

    Sans ce test, une erreur dans la branche ProxyFix reste invisible :
    tous les autres tests tournent avec la valeur par défaut, qui la contourne.
    """
    import importlib

    import config
    monkeypatch.setenv("HUSHLAB_PROXYS", "1")
    importlib.reload(config)
    assert config.Config.PROXYS_DE_CONFIANCE == 1
    module = importlib.reload(importlib.import_module("app"))
    assert module.app.wsgi_app.__class__.__name__ == "ProxyFix"
    monkeypatch.delenv("HUSHLAB_PROXYS")
    importlib.reload(config)
    importlib.reload(module)


def test_fichiers_statiques_versionnes(client):
    """Le cache long n'est acceptable que si l'URL change quand le fichier change.

    Sans ce marqueur, un visiteur déjà venu garderait l'ancien CSS pendant
    trente jours après une mise à jour du site.
    """
    page = client.get("/").data.decode()
    assert re.search(r'/static/css/app\.css\?v=\d+', page), \
        "le CSS est servi sans marqueur de version"
    assert re.search(r'/static/img/[^"]+\?v=\d+', page), \
        "les images sont servies sans marqueur de version"


# --- Audit 2026 : failles trouvées en exécutant le code ---------------------

def test_export_csv_neutralise_les_formules(client):
    """Une cellule commençant par = + - @ s'exécute à l'ouverture dans Excel."""
    donnees.enregistrer_demande(
        nom="=cmd|'/c calc'!A1", email="a@b.ma", telephone="", service="",
        message="Message de longueur suffisante.", origine="/")
    for ligne in donnees.exporter_csv().splitlines()[1:]:
        for cellule in ligne.split(";"):
            assert not cellule.lstrip('"').startswith(("=", "+", "-", "@")), \
                f"cellule interprétable comme formule : {cellule!r}"


def test_domaine_inconnu_refuse(client, monkeypatch):
    """Sans liste blanche, un Host forgé dicte les URL canoniques et les QR."""
    monkeypatch.setattr(Config, "HOTES_AUTORISES", ("hushlab.ma", "localhost"))
    assert client.get("/", headers={"Host": "attaquant.example"}).status_code == 400
    assert client.get("/", headers={"Host": "hushlab.ma"}).status_code == 200


def test_jeton_public_refuse_sur_l_administration(client):
    """Un jeton récolté sur la page d'accueil ne doit rien ouvrir côté admin."""
    jeton_public = _jeton(client)
    reponse = client.post("/admin/demande/1/traite",
                          data={"csrf": jeton_public}, headers=_auth())
    assert reponse.status_code == 403


def test_formulaire_renvoye_instantanement_refuse(client, monkeypatch):
    """Le délai est lu dans la signature du jeton : un robot ne peut pas le reculer."""
    monkeypatch.setattr(Config, "DELAI_MINIMUM_FORMULAIRE", 2)
    envoi = _demande_valide(client)          # jeton émis à l'instant
    assert client.post("/contact", data=envoi).status_code == 403


def test_ancien_champ_horodatage_sans_effet(client, monkeypatch):
    """L'ancienne barrière se contournait en reculant un champ caché en clair."""
    monkeypatch.setattr(Config, "DELAI_MINIMUM_FORMULAIRE", 2)
    envoi = dict(_demande_valide(client), horodatage=str(int(time.time()) - 3600))
    assert client.post("/contact", data=envoi).status_code == 403, \
        "un champ horodatage forgé rouvre la barrière"


def test_administration_paginee(client):
    """Au-delà d'une page, les demandes doivent rester atteignables."""
    for i in range(30):
        donnees.enregistrer_demande(
            nom=f"Client {i}", email=f"c{i}@ex.ma", telephone="", service="",
            message="Message de longueur suffisante.", origine="/")
    page1 = client.get("/admin", headers=_auth()).data.decode()
    assert "page=2" in page1, "aucun lien vers les demandes suivantes"
    page2 = client.get("/admin?page=2", headers=_auth()).data.decode()
    assert "Client 0" in page2, "les demandes anciennes sont inatteignables"


def test_versions_statiques_lues_une_seule_fois(client):
    """Trente appels système par page pour dater les fichiers, c'était trop."""
    import pathlib as _p
    compteur = {"n": 0}
    vrai = _p.Path.stat

    def compte(self, *a, **k):
        compteur["n"] += 1
        return vrai(self, *a, **k)

    from app import _version_fichier
    _version_fichier.cache_clear()
    _p.Path.stat = compte
    try:
        client.get("/")
        premier = compteur["n"]
        compteur["n"] = 0
        client.get("/")
        second = compteur["n"]
    finally:
        _p.Path.stat = vrai
    assert second == 0, f"{second} appels stat() sur une page déjà servie"
    assert premier > 0


def test_domaine_refuse_est_journalise(client, monkeypatch, caplog):
    """Un 400 muet sur tout le site serait indiagnosticable sans ce message."""
    monkeypatch.setattr(Config, "HOTES_AUTORISES", ("hushlab.ma",))
    with caplog.at_level("WARNING"):
        client.get("/", headers={"Host": "hushlab.onrender.com"})
    trace = caplog.text
    assert "hushlab.onrender.com" in trace, "le domaine refusé n'est pas journalisé"
    assert "hushlab.ma" in trace, "les domaines attendus ne sont pas rappelés"
