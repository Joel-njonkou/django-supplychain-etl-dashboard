
import json, re, unicodedata

NOMBRE = re.compile(r"\d+(?:[.,]\d+)?")

def _norm(tok):
    t = tok.replace(",", ".")
    return t.rstrip("0").rstrip(".") if "." in t else t

def numbers_in(obj):
    return {_norm(t) for t in NOMBRE.findall(json.dumps(obj, ensure_ascii=False, default=str))}

def check_numbers(texte_ou_objet, evidence):
    # Tout nombre cité doit figurer dans les preuves (hors petits entiers d'énumération 0 à 10).
    inconnus = numbers_in(texte_ou_objet) - numbers_in(evidence) - {str(i) for i in range(11)}
    return sorted(inconnus)


def _as_text(value):
    if value is None:
        return ""
    if isinstance(value, dict):
        return "; ".join(
            f"{key.replace('_', ' ')} : {_as_text(item)}"
            for key, item in value.items()
            if item is not None
        )
    if isinstance(value, list):
        return "; ".join(text for item in value if (text := _as_text(item)))
    if isinstance(value, (str, int, float, bool)):
        return str(value)
    return ""


def normalize_bottlenecks(exp):
    if not isinstance(exp, dict):
        return exp
    normalized = dict(exp)
    for key in ("preuves", "goulots_prioritaires", "limites", "actions"):
        value = normalized.get(key)
        if isinstance(value, list):
            normalized[key] = [text for item in value if (text := _as_text(item))]

    confidence = normalized.get("confiance")
    if isinstance(confidence, str) and confidence not in ("faible", "moyenne", "élevée"):
        folded = unicodedata.normalize("NFKD", confidence.casefold())
        folded = "".join(char for char in folded if not unicodedata.combining(char))
        if any(word in folded for word in ("eleve", "high", "forte", "fort")):
            normalized["confiance"] = "élevée"
        elif any(word in folded for word in ("modere", "moyenne", "medium")):
            normalized["confiance"] = "moyenne"
        elif any(word in folded for word in ("faible", "basse", "low")):
            normalized["confiance"] = "faible"
    return normalized


def validate_bottlenecks(exp, ev):
    if not isinstance(exp, dict):
        return False, ["réponse non JSON"]
    problems = []
    required = {
        "titre", "resume", "hypothese_principale", "confiance", "preuves",
        "goulots_prioritaires", "hypothese_alternative", "limites", "actions",
    }
    manquants = required - set(exp)
    if manquants:
        problems.append(f"clés manquantes : {sorted(manquants)}")
    for key in ("titre", "resume", "hypothese_principale", "hypothese_alternative"):
        if key in exp and (not isinstance(exp[key], str) or not exp[key].strip()):
            problems.append(f"{key} doit être un texte non vide")
    for key in ("preuves", "goulots_prioritaires", "limites", "actions"):
        if key in exp and (
            not isinstance(exp[key], list)
            or any(not isinstance(item, str) for item in exp[key])
        ):
            problems.append(f"{key} doit être une liste de textes")
    if exp.get("confiance") not in ("faible", "moyenne", "élevée"):
        problems.append("confiance invalide")
    bad = check_numbers(exp, ev)
    if bad:
        problems.append(f"nombres absents des preuves : {bad[:6]}")
    return (not problems), problems

def template_bottlenecks(ev):
    g = ev["global"]
    constats = [c["texte"] for c in ev["constats"]]
    tete = ev["classement_par_retards_en_exces"][:3]
    preuves = [f"Taux de retard global : {g['taux_retard_pct']} % sur {g['volume']} expéditions."] + constats
    goulots = [f"{i['region']} · {i['transporteur']} : {i['retards_en_exces']} retards en excès "
                f"(taux {i['taux_retard_pct']} %)" for i in tete]
    structurel = any(c["id"] == "STRUCTUREL_MODE" for c in ev["constats"])
    return {
        "titre": "Goulots d'étranglement logistiques",
        "resume": preuves[0],
        "hypothese_principale": ("Le retard semble principalement lié au mode d'expédition et à la promesse de délai, "
                                "plus qu'à la région." if structurel else
                                "Aucun facteur unique ne ressort nettement."),
        "confiance": "moyenne" if g["volume"] >= 1000 else "faible",
        "preuves": preuves, "goulots_prioritaires": goulots,
        "hypothese_alternative": "Effet d'une dimension non analysée (catégorie de produit, période, client).",
        "limites": ["Association statistique, pas causalité.", "Coût estimé ; pas de date de livraison réelle."],
        "actions": ["Réexaminer les délais promis pour les modes à fort taux de retard.",
                    "Comparer avec une période antérieure avant toute décision."],
}