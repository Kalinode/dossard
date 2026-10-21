"""Cas limites de la règle : ex aequo = même rang, le rang suivant saute (1, 2, 2, 4)."""

import pytest


@pytest.fixture
def classement(client, make_competition, make_event, make_athlete, make_registration):
    """Fabrique : épreuve close avec un résultat par performance ; renvoie le classement."""

    def _make(unit: str, performances: list[float]) -> list[dict]:
        competition = make_competition(status="open")
        event = make_event(competition["id"], unit=unit)
        inscriptions = [
            make_registration(event["id"], make_athlete(f"Athlete{i}")["id"])
            for i in range(len(performances))
        ]
        client.patch(f"/competitions/{competition['id']}", json={"status": "closed"})
        for inscription, performance in zip(inscriptions, performances, strict=True):
            response = client.put(
                f"/registrations/{inscription['id']}/result", json={"performance": performance}
            )
            assert response.status_code == 200
        response = client.get(f"/events/{event['id']}/ranking")
        assert response.status_code == 200
        return response.json()

    return _make


def _rangs(classement: list[dict]) -> list[int]:
    return [e["rank"] for e in classement]


def test_ex_aequo_au_milieu_rang_suivant_saute():
    """Référence de la règle : 1, 2, 2, 4 (test pur sur la fonction de classement)."""
    from app.ranking import rank_results
    from app.schemas import ResultUnit

    lignes = [
        {
            "bib": i,
            "athlete_id": i,
            "last_name": "N",
            "first_name": "P",
            "club": None,
            "performance": p,
        }
        for i, p in enumerate([11.9, 12.1, 12.1, 12.4], start=1)
    ]
    assert [e.rank for e in rank_results(lignes, ResultUnit.TIME_S)] == [1, 2, 2, 4]


def test_ex_aequo_en_tete_temps(classement):
    """Deux premiers ex aequo : 1, 1, 3."""
    assert _rangs(classement("time_s", [11.9, 11.9, 12.5])) == [1, 1, 3]


def test_ex_aequo_en_queue_temps(classement):
    """Deux derniers ex aequo : 1, 2, 2."""
    assert _rangs(classement("time_s", [11.9, 12.5, 12.5])) == [1, 2, 2]


def test_trois_ex_aequo_saut_de_deux_places(classement):
    """Trois ex aequo au rang 2 : le suivant prend le rang 5."""
    assert _rangs(classement("time_s", [11.0, 12.0, 12.0, 12.0, 13.0])) == [1, 2, 2, 2, 5]


def test_tous_ex_aequo(classement):
    """Tous égaux : tout le monde est premier."""
    assert _rangs(classement("time_s", [12.0, 12.0, 12.0])) == [1, 1, 1]


def test_deux_groupes_d_ex_aequo(classement):
    """Deux groupes d'ex aequo : 1, 1, 3, 3, 5."""
    assert _rangs(classement("time_s", [10.0, 10.0, 11.0, 11.0, 12.0])) == [1, 1, 3, 3, 5]


def test_ex_aequo_distances_ordre_decroissant(classement):
    """Distances : meilleure = plus grande ; les ex aequo partagent le rang."""
    resultat = classement("distance_m", [6.5, 6.85, 6.5, 5.9])
    assert [(e["rank"], e["performance"]) for e in resultat] == [
        (1, 6.85),
        (2, 6.5),
        (2, 6.5),
        (4, 5.9),
    ]


def test_ex_aequo_points_ordre_decroissant(classement):
    """Points : ordre décroissant, ex aequo au même rang."""
    resultat = classement("points", [8000, 8000, 7500])
    assert [(e["rank"], e["performance"]) for e in resultat] == [(1, 8000), (1, 8000), (3, 7500)]


def test_performances_tres_proches_ne_sont_pas_ex_aequo(classement):
    """Un écart d'un centième ne fait pas un ex aequo."""
    assert _rangs(classement("time_s", [12.00, 12.01, 12.02])) == [1, 2, 3]


def test_un_seul_resultat_rang_un(classement):
    """Un seul classé : rang 1."""
    assert _rangs(classement("time_s", [12.0])) == [1]


def test_classement_vide_epreuve_sans_resultat(client, make_competition, make_event):
    """Épreuve sans résultat : liste vide, pas d'erreur."""
    competition = make_competition(status="open")
    event = make_event(competition["id"])

    response = client.get(f"/events/{event['id']}/ranking")

    assert response.status_code == 200
    assert response.json() == []


def test_correction_de_resultat_cree_un_ex_aequo(
    client, make_competition, make_event, make_athlete, make_registration
):
    """Corriger un résultat (PUT) pour égaler un autre recalcule les rangs."""
    competition = make_competition(status="open")
    event = make_event(competition["id"])
    a = make_registration(event["id"], make_athlete("A")["id"])
    b = make_registration(event["id"], make_athlete("B")["id"])
    client.patch(f"/competitions/{competition['id']}", json={"status": "closed"})
    client.put(f"/registrations/{a['id']}/result", json={"performance": 11.0})
    client.put(f"/registrations/{b['id']}/result", json={"performance": 12.0})
    assert _rangs(client.get(f"/events/{event['id']}/ranking").json()) == [1, 2]

    client.put(f"/registrations/{b['id']}/result", json={"performance": 11.0})

    assert _rangs(client.get(f"/events/{event['id']}/ranking").json()) == [1, 1]


def test_inscription_annulee_exclue_du_classement_et_des_rangs(
    client, make_competition, make_event, make_athlete, make_registration
):
    """Une inscription annulée ne compte pas : plus d'ex aequo ni de saut de rang."""
    competition = make_competition(status="open")
    event = make_event(competition["id"])
    a = make_registration(event["id"], make_athlete("A")["id"])
    b = make_registration(event["id"], make_athlete("B")["id"])
    c = make_registration(event["id"], make_athlete("C")["id"])
    client.patch(f"/competitions/{competition['id']}", json={"status": "closed"})
    for inscription, perf in ((a, 11.0), (b, 11.0), (c, 12.0)):
        client.put(f"/registrations/{inscription['id']}/result", json={"performance": perf})
    client.patch(f"/registrations/{b['id']}", json={"status": "cancelled"})

    ranking = client.get(f"/events/{event['id']}/ranking").json()

    assert _rangs(ranking) == [1, 2]


def test_les_ex_aequo_gardent_des_dossards_distincts(classement):
    """Les ex aequo ont le même rang mais des dossards différents."""
    resultat = classement("time_s", [12.0, 12.0])
    assert len({e["bib"] for e in resultat}) == 2


@pytest.mark.parametrize("performance", [0, -1.5])
def test_resultat_non_positif_refuse_422(client, performance):
    """Performance nulle ou négative : 422."""
    response = client.put("/registrations/1/result", json={"performance": performance})
    assert response.status_code == 422


def test_resultat_performance_absente_422(client):
    """Corps sans performance : 422."""
    response = client.put("/registrations/1/result", json={})
    assert response.status_code == 422


def test_classement_epreuve_inconnue_404(client):
    """Épreuve inexistante : 404 avec code not_found."""
    response = client.get("/events/999/ranking")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_classement_identifiant_invalide_422(client):
    """Identifiant d'épreuve non numérique : 422."""
    assert client.get("/events/abc/ranking").status_code == 422


def test_resultat_inscription_inconnue_404(client):
    """Inscription inexistante : 404."""
    assert client.put("/registrations/999/result", json={"performance": 12.0}).status_code == 404


def test_resultat_competition_non_close_409(
    client, make_competition, make_event, make_athlete, make_registration
):
    """Compétition non close : 409 results_not_allowed."""
    competition = make_competition(status="open")
    event = make_event(competition["id"])
    inscription = make_registration(event["id"], make_athlete()["id"])

    response = client.put(f"/registrations/{inscription['id']}/result", json={"performance": 12.0})

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "results_not_allowed"
