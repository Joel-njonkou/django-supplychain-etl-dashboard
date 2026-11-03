
import hashlib, json, logging
from django.conf import settings
from django.core.cache import cache
from apps.logistics.models import EtlRun
from . import prompts
from .analysis import analyse_bottlenecks
from .guardrails import normalize_bottlenecks, template_bottlenecks, validate_bottlenecks
from .llm_client import LLMUnavailable, chat, parse_json

log = logging.getLogger(__name__)

def _cache_key(params):
    last = EtlRun.objects.filter(status="success").values_list("id", flat=True).first() or 0
    raw = json.dumps({"p": dict(params), "etl": last}, sort_keys=True, default=str)
    return "agent:bn:v2:" + hashlib.sha1(raw.encode()).hexdigest()


def explain_bottlenecks(params, force=False):
    key = _cache_key(params)
    cached = cache.get(key)
    if not force and cached:
        return cached
    ev = analyse_bottlenecks(params)
    if ev is None:
        return {"source": "none", "explanation": None, "evidence": None}
    source, problems, exp = "llm", [], None
    messages = [
        {"role": "system", "content": prompts.SYSTEM_EXPLAIN},
        {
            "role": "user",
            "content": "evidence :\n" + json.dumps(ev, ensure_ascii=False),
        },
    ]
    try:
        msg = chat(
            messages,
            json_mode=True,
            timeout=settings.LLM_EXPLAIN_TIMEOUT_S,
            max_tokens=settings.LLM_EXPLAIN_MAX_TOKENS,
        )
        exp = normalize_bottlenecks(parse_json(msg.content))
        ok, problems = validate_bottlenecks(exp, ev)
        if not ok:
            log.warning("OpenRouter explanation failed validation: %s", problems)
            messages.extend([
                {"role": "assistant", "content": msg.content or ""},
                {
                    "role": "user",
                    "content": (
                        "Ta réponse précédente n'a pas passé les vérifications suivantes : "
                        f"{'; '.join(problems)}. Réécris-la en JSON valide avec toutes les clés "
                        "demandées dans le format système. Utilise uniquement les nombres exacts "
                        "du JSON evidence déjà fourni et n'ajoute aucun commentaire hors JSON."
                    ),
                },
            ])
            msg = chat(
                messages,
                json_mode=True,
                timeout=settings.LLM_EXPLAIN_TIMEOUT_S,
                max_tokens=settings.LLM_EXPLAIN_MAX_TOKENS,
            )
            exp = normalize_bottlenecks(parse_json(msg.content))
            ok, problems = validate_bottlenecks(exp, ev)
    except LLMUnavailable as e:
        log.warning(
            "OpenRouter explanation unavailable: %s (HTTP %s)",
            type(e.__cause__).__name__ if e.__cause__ else type(e).__name__,
            e.status_code or "sans réponse HTTP",
        )
        ok, problems = False, ["appel fournisseur IA indisponible"]
    if not ok:
        log.warning("Using automatic explanation after LLM failure: %s", problems)
        exp, source = template_bottlenecks(ev), "template"
    out = {
        "source": source,
        "explanation": exp,
        "evidence": ev,
    }
    if source == "llm":
        cache.set(key, out, 3600)
    return out