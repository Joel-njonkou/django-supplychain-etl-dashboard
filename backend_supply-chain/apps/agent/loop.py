
import json, logging, unicodedata
from django.conf import settings
from . import prompts
from .guardrails import check_numbers
from .llm_client import LLMUnavailable, chat
from .tools import TOOLS, ToolError, execute_tool
log = logging.getLogger(__name__)

MAX_CHARS = 6000      # borne la taille d'un résultat d'outil envoyé au modele


def _normalize_question(question):
    normalized = unicodedata.normalize("NFKD", question.casefold())
    return "".join(char for char in normalized if not unicodedata.combining(char))


def _percent(value):
    return f"{value * 100:.1f} %"


def _answer_common_data_question(question):
    normalized = _normalize_question(question)
    if "goulot" in normalized or "retards en exces" in normalized:
        evidence = execute_tool("analyse_goulots", {})
        if "erreur" in evidence:
            answer = "Aucune expédition ne correspond aux filtres disponibles pour cette analyse."
        else:
            global_data = evidence["global"]
            bottlenecks = evidence["classement_par_retards_en_exces"]
            variability = evidence["part_variabilite_expliquee_pct"]
            answer = (
                f"Sur {global_data['volume']} expéditions, {global_data['retards']} sont en retard "
                f"({global_data['taux_retard_pct']:.1f} %). "
            )
            if bottlenecks:
                priorities = "; ".join(
                    f"{item['region']} — {item['transporteur']} : {item['retards_en_exces']} retards "
                    f"en excès pour {item['volume']} expéditions"
                    for item in bottlenecks[:3]
                )
                answer += (
                    "En corrigeant l’effet du volume, les principaux points à examiner sont : "
                    f"{priorities}. "
                )
            else:
                answer += "Aucun point ne ressort nettement au-dessus du taux global après correction du volume. "
            answer += (
                "La variabilité des retards est associée au mode d’expédition à "
                f"{variability['transporteur']} % et à la région à {variability['region']} % ; "
                "ce sont des associations, pas des preuves de causalité."
            )
        return evidence, answer, "analyse_goulots"

    if "transporteur" in normalized and ("retard" in normalized or "plus" in normalized):
        evidence = execute_tool("bottlenecks", {"by": "transporteur", "limit": 8})
        if not evidence:
            answer = (
                "Aucun mode d’expédition n’atteint le seuil minimal de 100 expéditions "
                "pour établir un classement."
            )
        else:
            classement = sorted(evidence, key=lambda row: row["retards"], reverse=True)
            lignes = [
                f"{row['transporteur']} : {row['retards']} retards sur {row['volume']} expéditions "
                f"({_percent(row['taux_retard'])})"
                for row in classement[:5]
            ]
            answer = "Voici les modes d’expédition ayant le plus de retards :\n" + "\n".join(lignes)
        return evidence, answer, "bottlenecks"

    if "taux" in normalized and "retard" in normalized:
        evidence = execute_tool("kpi_summary", {})
        if not evidence["volume"]:
            answer = "Aucune expédition ne correspond aux filtres disponibles."
        else:
            answer = (
                f"Le taux de retard global est de {_percent(evidence['taux_retard'])} : "
                f"{evidence['retards']} expéditions en retard sur {evidence['volume']}. "
                f"Le taux de livraison à temps est de "
                f"{_percent(evidence['taux_livraison_a_temps'])}."
            )
        return evidence, answer, "kpi_summary"
    return None


def _assistant_msg(m):
    # Reconstruction minimale : certains serveurs rejettent les champs additionnels du SDK
    return {"role": "assistant", "content": m.content or "",
            "tool_calls": [{"id": c.id, "type": "function",
                            "function": {"name": c.function.name, "arguments": c.function.arguments
                                or "{}"}}
                            for c in m.tool_calls]}
    
def run_agent(history, question):
    common_answer = _answer_common_data_question(question)
    if common_answer:
        evidence, answer, tool_name = common_answer
        arguments = {"by": "transporteur", "limit": 8} if tool_name == "bottlenecks" else {}
        return {
            "source": "data",
            "answer": answer,
            "trace": [{"outil": tool_name, "arguments": arguments}],
            "evidence": [evidence],
        }

    messages = [{"role": "system", "content": prompts.SYSTEM_CHAT}]
    messages += [m for m in history[-8:] if m.get("role") in ("user", "assistant") and isinstance(m.get("content"), str)]
    messages.append({"role": "user", "content": question[:1000]})
    evidence, trace, answer = [], [], None
    try:
        for _ in range(settings.AGENT_MAX_STEPS):
            m = chat(messages, tools=TOOLS)
            if m.tool_calls:
                messages.append(_assistant_msg(m))
                for call in m.tool_calls:
                    try:
                        args = json.loads(call.function.arguments or "{}")
                        result = execute_tool(call.function.name, args)
                    except (ToolError, ValueError) as e:
                        args, result = {}, {"erreur": str(e)}
                    evidence.append(result)
                    trace.append({"outil": call.function.name, "arguments": args})
                    messages.append({"role": "tool", "tool_call_id": call.id, "content": json.dumps(result, ensure_ascii=False, default=str)[:MAX_CHARS]})
                continue

            answer = (m.content or "").strip()
            if evidence and (bad := check_numbers(answer, evidence)):
                messages += [
                    {"role": "assistant", "content": answer},
                    {"role": "user", "content": f"Ces nombres ne figurent pas dans les résultats d'outils : {bad[:5]}. "
                        "Réécris en n'utilisant que les valeurs fournies."},
                ]
                answer = (chat(messages).content or "").strip()
                if check_numbers(answer, evidence):
                    answer = None
            break
    except LLMUnavailable as e:
        log.warning("agent indisponible : %s", e)
        answer = None
    if answer:
        return {"source": "llm", "answer": answer, "trace": trace}
    return {"source": "fallback", "trace": trace, "answer": _fallback(evidence),
            "evidence": evidence[:3]}
    
def _fallback(evidence):
    if not evidence:
        return ("L'assistant n'est pas disponible pour cette question. Utilisez le bouton « Expliquer » " "ou les filtres du tableau de bord.")
    return "Je n'ai pas pu formuler une réponse fiable ; voici les données brutes retournées par les outils."