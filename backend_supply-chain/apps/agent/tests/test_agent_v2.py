
from types import SimpleNamespace as NS
import pytest
from apps.agent import loop, tools
from apps.agent.guardrails import check_numbers, normalize_bottlenecks, validate_bottlenecks

def test_outil_inconnu_refuse():
    with pytest.raises(tools.ToolError):
        tools.execute_tool("run_sql", {"query": "DROP TABLE x"})

def test_parametre_non_autorise_refuse():
    with pytest.raises(tools.ToolError):
        tools.execute_tool("kpi_summary", {"sql": "select 1"})


def test_schemas_outils_acceptent_les_valeurs_nulles_facultatives():
    schemas = {
        tool["function"]["name"]: tool["function"]["parameters"]["properties"]
        for tool in tools.TOOLS
    }

    assert "null" in schemas["kpi_summary"]["date_min"]["type"]
    assert "null" in schemas["kpi_summary"]["date_max"]["type"]
    assert None in schemas["kpi_summary"]["transporteur"]["enum"]
    assert "null" in schemas["timeseries"]["granularity"]["type"]
    assert "null" in schemas["bottlenecks"]["limit"]["type"]


def test_parametres_nuls_utilisent_les_valeurs_par_defaut(monkeypatch):
    calls = {}
    queryset = object()
    monkeypatch.setattr(tools.kpis, "base_queryset", lambda filters: queryset)

    def timeseries(received_queryset, granularity):
        calls["timeseries"] = (received_queryset, granularity)
        return []

    def bottlenecks(received_queryset, by, min_volume, limit):
        calls["bottlenecks"] = (received_queryset, by, min_volume, limit)
        return []

    monkeypatch.setattr(tools.kpis, "timeseries", timeseries)
    monkeypatch.setattr(tools.kpis, "bottlenecks", bottlenecks)

    tools.execute_tool("timeseries", {"granularity": None})
    tools.execute_tool("bottlenecks", {"by": None, "limit": None})

    assert calls["timeseries"] == (queryset, "week")
    assert calls["bottlenecks"] == (queryset, "region_transporteur", 100, 8)

def test_date_invalide_refusee():
    with pytest.raises(tools.ToolError):
        tools.execute_tool("kpi_summary", {"date_min": "hier"})

def test_nombre_invente_detecte():
    ev = {"global": {"taux_retard_pct": 57.3, "volume": 62897}}
    assert check_numbers("Le taux est de 57.3 % sur 62897 expéditions", ev) == []
    assert check_numbers("Le taux est de 63.9 %", ev) == ["63.9"]

def test_reponse_llm_incomplete_rejetee():
    
    ok, problems = validate_bottlenecks({"titre": "x"}, {"global": {}})
    assert not ok and any("clés manquantes" in p for p in problems)


def test_reponse_llm_rejettee_si_les_champs_affiches_sont_invalides():
    response = {
        "titre": "Analyse",
        "resume": "Résumé",
        "hypothese_principale": "Hypothèse",
        "confiance": "moyenne",
        "preuves": "ceci devrait être une liste",
        "goulots_prioritaires": [],
        "hypothese_alternative": "Alternative",
        "limites": [],
        "actions": [],
    }

    valid, problems = validate_bottlenecks(response, {})

    assert not valid
    assert "preuves doit être une liste de textes" in problems


def test_normalise_la_reponse_openrouter_observee():
    explanation = {
        "titre": "Analyse",
        "resume": "Les données mettent en évidence un écart.",
        "hypothese_principale": "Le mode d’expédition peut contribuer aux retards.",
        "confiance": "Élevée, en raison du volume significatif.",
        "preuves": [
            {
                "region": "Europe",
                "transporteur": "First Class",
                "retards": 24,
                "volume": 80,
            }
        ],
        "goulots_prioritaires": ["Europe · First Class"],
        "hypothese_alternative": "La composition des commandes peut aussi jouer.",
        "limites": ["Une association ne prouve pas une causalité."],
        "actions": ["Comparer les délais annoncés."],
    }
    evidence = {
        "global": {"volume": 80, "retards": 24},
        "regions": ["Europe"],
        "transporteurs": ["First Class"],
    }

    normalized = normalize_bottlenecks(explanation)
    valid, problems = validate_bottlenecks(normalized, evidence)

    assert normalized["confiance"] == "élevée"
    assert normalized["preuves"] == [
        "region : Europe; transporteur : First Class; retards : 24; volume : 80"
    ]
    assert valid, problems


@pytest.mark.django_db
def test_boucle_avec_faux_llm(monkeypatch):
    # 1er tour : le modèle demande un outil ; 2e tour : il répond avec un nombre issu de l'outil
    monkeypatch.setattr(loop, "execute_tool", lambda n, a: {"taux_retard": 0.573, "volume": 100})
    call = NS(id="c1", function=NS(name="kpi_summary", arguments="{}"))
    scripted = iter([NS(content="", tool_calls=[call]), NS(content="Le volume est de 100.",
        tool_calls=None)])
    monkeypatch.setattr(loop, "chat", lambda *a, **k: next(scripted))
    out = loop.run_agent([], "Quel est le volume ?")
    assert out["source"] == "llm" and out["trace"][0]["outil"] == "kpi_summary"

@pytest.mark.django_db
def test_boucle_bascule_en_secours_si_nombre_invente(monkeypatch):
    monkeypatch.setattr(loop, "execute_tool", lambda n, a: {"volume": 100})
    call = NS(id="c1", function=NS(name="kpi_summary", arguments="{}"))
    scripted = iter([NS(content="", tool_calls=[call]), NS(content="Le volume est 777.",
        tool_calls=None),
                    NS(content="Toujours 777.", tool_calls=None)])
    monkeypatch.setattr(loop, "chat", lambda *a, **k: next(scripted))
    assert loop.run_agent([], "Volume ?")["source"] == "fallback"


@pytest.mark.parametrize(
    ("question", "tool_name", "result", "expected"),
    [
        (
            "Quel est le taux de retard global ?",
            "kpi_summary",
            {
                "volume": 250,
                "retards": 50,
                "taux_retard": 0.2,
                "taux_livraison_a_temps": 0.8,
            },
            "20.0 %",
        ),
        (
            "Quels transporteurs ont le plus de retards ?",
            "bottlenecks",
            [
                {
                    "transporteur": "First Class",
                    "retards": 30,
                    "volume": 100,
                    "taux_retard": 0.3,
                }
            ],
            "First Class",
        ),
        (
            "Où sont les goulots indépendamment du volume ?",
            "analyse_goulots",
            {
                "global": {"volume": 250, "retards": 50, "taux_retard_pct": 20.0},
                "classement_par_retards_en_exces": [
                    {
                        "region": "Europe",
                        "transporteur": "First Class",
                        "retards_en_exces": 12,
                        "volume": 100,
                    }
                ],
                "part_variabilite_expliquee_pct": {"transporteur": 8.0, "region": 2.0},
            },
            "Europe — First Class",
        ),
    ],
)
def test_questions_suggestions_sont_repondues_sans_llm(
    monkeypatch, question, tool_name, result, expected
):
    def execute_tool(name, args):
        assert name == tool_name
        return result

    monkeypatch.setattr(loop, "execute_tool", execute_tool)
    monkeypatch.setattr(loop, "chat", lambda *args, **kwargs: pytest.fail("Le LLM ne doit pas être appelé"))

    response = loop.run_agent([], question)

    assert response["source"] == "data"
    assert expected in response["answer"]
    assert response["trace"][0]["outil"] == tool_name
    if tool_name == "bottlenecks":
        assert response["trace"][0]["arguments"] == {"by": "transporteur", "limit": 8}