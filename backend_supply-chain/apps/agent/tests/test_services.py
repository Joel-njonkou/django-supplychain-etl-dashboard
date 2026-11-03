import json
from types import SimpleNamespace

import pytest
from django.conf import settings

from apps.agent import services
from django.core.cache import cache


EVIDENCE = {
    "global": {"volume": 100, "retards": 20, "taux_retard_pct": 20.0},
    "classement_par_retards_en_exces": [],
    "constats": [],
    "part_variabilite_expliquee_pct": {"transporteur": 8.0, "region": 2.0},
}

VALID_EXPLANATION = {
    "titre": "Analyse des retards",
    "resume": "Une part des expéditions est en retard.",
    "hypothese_principale": "Les délais annoncés sont à examiner.",
    "confiance": "moyenne",
    "preuves": ["Les données montrent des retards."],
    "goulots_prioritaires": [],
    "hypothese_alternative": "La composition des commandes peut jouer.",
    "limites": ["Une association ne prouve pas une causalité."],
    "actions": ["Comparer les délais par mode."],
}

OPENROUTER_EXPLANATION = {
    **VALID_EXPLANATION,
    "confiance": "Élevée, en raison du volume significatif de données.",
    "preuves": [{"region": "Europe", "retards": 20, "volume": 100}],
}


@pytest.mark.django_db
def test_explain_accepte_une_reponse_llm_valide(monkeypatch):
    monkeypatch.setattr(services, "_cache_key", lambda params: "test-explain-valid")
    monkeypatch.setattr(services, "analyse_bottlenecks", lambda params: EVIDENCE)
    calls = []

    def fake_chat(*args, **kwargs):
        calls.append(kwargs)
        return SimpleNamespace(content=json.dumps(VALID_EXPLANATION))

    monkeypatch.setattr(services, "chat", fake_chat)

    result = services.explain_bottlenecks({}, force=True)

    assert result["source"] == "llm"
    assert result["explanation"] == VALID_EXPLANATION
    assert calls[0]["timeout"] == settings.LLM_EXPLAIN_TIMEOUT_S
    assert calls[0]["max_tokens"] == settings.LLM_EXPLAIN_MAX_TOKENS


@pytest.mark.django_db
def test_explain_normalise_le_format_openrouter_observe(monkeypatch):
    monkeypatch.setattr(services, "_cache_key", lambda params: "test-explain-openrouter-shape")
    monkeypatch.setattr(services, "analyse_bottlenecks", lambda params: EVIDENCE)
    monkeypatch.setattr(
        services,
        "chat",
        lambda *args, **kwargs: SimpleNamespace(
            content=json.dumps(OPENROUTER_EXPLANATION, ensure_ascii=False)
        ),
    )

    result = services.explain_bottlenecks({}, force=True)

    assert result["source"] == "llm"
    assert result["explanation"]["confiance"] == "élevée"
    assert result["explanation"]["preuves"] == ["region : Europe; retards : 20; volume : 100"]


@pytest.mark.django_db
def test_explain_reessaie_une_reponse_llm_invalide(monkeypatch):
    monkeypatch.setattr(services, "_cache_key", lambda params: "test-explain-retry")
    monkeypatch.setattr(services, "analyse_bottlenecks", lambda params: EVIDENCE)
    responses = iter([
        SimpleNamespace(content='{"titre":"Réponse incomplète"}'),
        SimpleNamespace(content=json.dumps(VALID_EXPLANATION)),
    ])
    calls = []

    def fake_chat(messages, **kwargs):
        calls.append(messages)
        return next(responses)

    monkeypatch.setattr(services, "chat", fake_chat)

    result = services.explain_bottlenecks({}, force=True)

    assert len(calls) == 2
    assert result["source"] == "llm"
    assert result["explanation"] == VALID_EXPLANATION


@pytest.mark.django_db
def test_explain_signale_le_mode_secours_si_le_llm_reste_invalide(monkeypatch):
    monkeypatch.setattr(services, "_cache_key", lambda params: "test-explain-fallback")
    monkeypatch.setattr(services, "analyse_bottlenecks", lambda params: EVIDENCE)
    cache_key = "test-explain-fallback"
    cache.delete(cache_key)
    monkeypatch.setattr(
        services,
        "chat",
        lambda *args, **kwargs: SimpleNamespace(content='{"titre":"Réponse incomplète"}'),
    )

    result = services.explain_bottlenecks({}, force=True)

    assert result["source"] == "template"
    assert result["explanation"]
    assert cache.get(cache_key) is None


@pytest.mark.django_db
def test_explain_reessaie_un_secours_precedemment_mis_en_cache(monkeypatch):
    monkeypatch.setattr(services, "analyse_bottlenecks", lambda params: EVIDENCE)
    cache_key = services._cache_key({})
    assert cache_key.startswith("agent:bn:v2:")
    old_cache_key = cache_key.replace("agent:bn:v2:", "agent:bn:", 1)
    cache.set(
        old_cache_key,
        {"source": "template", "explanation": {"titre": "Ancienne réponse"}, "evidence": EVIDENCE},
        3600,
    )
    monkeypatch.setattr(
        services,
        "chat",
        lambda *args, **kwargs: SimpleNamespace(content=json.dumps(VALID_EXPLANATION)),
    )

    result = services.explain_bottlenecks({}, force=False)

    assert result["source"] == "llm"
    assert result["explanation"] == VALID_EXPLANATION
