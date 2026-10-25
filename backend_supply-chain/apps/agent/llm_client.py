
import json, logging, re
from django.conf import settings
from openai import OpenAI
log = logging.getLogger(__name__)

class LLMUnavailable(Exception):
    def __init__(self, message, status_code=None):
        super().__init__(message)
        self.status_code = status_code


_client = None
def _get():
    
    global _client
    if _client is None:
        _client = OpenAI(base_url=settings.LLM_BASE_URL, api_key=settings.LLM_API_KEY or "none",
                        timeout=settings.LLM_TIMEOUT_S, max_retries=1)
    return _client

def chat(messages, tools=None, json_mode=False):
    # Retourne le message de l'assistant (content et/ou tool_calls). Lève LLMUnavailable en cas d'échec.
    if not settings.LLM_ENABLED:
        raise LLMUnavailable("LLM non configuré")
    kw = dict(model=settings.LLM_MODEL, messages=messages, temperature=0.1, max_tokens=1000)
    if tools:
        kw.update(tools=tools, tool_choice="auto")
    elif json_mode:
        kw["response_format"] = {"type": "json_object"}
    try:
        try:
            return _get().chat.completions.create(**kw).choices[0].message
        except Exception:
            if "response_format" in kw:                       # certains serveurs locaux ne le supportent pas
                kw.pop("response_format")
                return _get().chat.completions.create(**kw).choices[0].message
            raise
    except Exception as exc:
        log.warning("Appel LLM échoué : %s", type(exc).__name__)
        raise LLMUnavailable(str(exc)) from exc
        
def parse_json(text):
    # Extrait un objet JSON d'une réponse éventuellement entourée de texte ou de balises ```
    if not text:
        return None
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M).strip()
    try:
        return json.loads(text)
    except ValueError:
        m = re.search(r"\{.*\}", text, flags=re.S)
        try:
            return json.loads(m.group(0)) if m else None
        except ValueError:
            return None