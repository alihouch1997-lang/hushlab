"""Suite de tests du site Hushlab.

    .venv/bin/pytest -q

Chaque test de sécurité correspond à une faille réellement trouvée lors de
l'audit : ils échouent si la protection disparaît d'une révision à l'autre.
"""

import os
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


def test_envoi_instantane_ignore(client):
    envoi = dict(_demande_valide(client), horodatage=str(int(time.time())))
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
