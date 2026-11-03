import { useEffect, useRef, useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { chat, type ChatMessage, type ChatSource } from "@/api/agent";
import { agentErrorMessage } from "@/api/errors";
import { Spinner } from "@/components/Spinner";

interface Message extends ChatMessage {
  source?: "llm" | "fallback" | "data";
  tools?: string[];
  sources?: ChatSource[];
  failed?: boolean;
  retryQuestion?: string;
}

const suggestions = [
  "Quel est le taux de retard global ?",
  "Quels transporteurs ont le plus de retards ?",
  "Où sont les goulots indépendamment du volume ?",
];

export function ChatPanel() {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [question, setQuestion] = useState("");
  const endRef = useRef<HTMLDivElement>(null);
  const send = useMutation({
    mutationFn: ({ text, history }: { text: string; history: ChatMessage[] }) => chat(text, history),
    onSuccess: (response) => setMessages((current) => [
      ...current,
      { role: "assistant", content: response.answer, source: response.source, tools: response.trace.map(({ outil }) => outil), sources: response.sources },
    ]),
    onError: (error, variables) => setMessages((current) => [
      ...current,
      { role: "assistant", content: agentErrorMessage(error), failed: true, retryQuestion: variables.text },
    ]),
  });

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, send.isPending, open]);

  function sendQuestion(rawQuestion: string, history: ChatMessage[]) {
    const text = rawQuestion.trim();
    if (!text || send.isPending) return;
    setMessages((current) => [...current, { role: "user", content: text }]);
    setQuestion("");
    send.mutate({ text, history });
  }

  function ask(rawQuestion: string) {
    const history = messages
      .filter((message) => !message.failed)
      .slice(-8)
      .map(({ role, content }) => ({ role, content }));
    sendQuestion(rawQuestion, history);
  }

  function retry(message: Message, index: number) {
    if (!message.retryQuestion) return;
    const history = messages.slice(0, index)
      .filter((entry) => !entry.failed)
      .slice(-8)
      .map(({ role, content }) => ({ role, content }));
    const last = history.at(-1);
    if (last?.role === "user" && last.content === message.retryQuestion) history.pop();
    sendQuestion(message.retryQuestion, history);
  }

  function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    ask(question);
  }

  return (
    <div className="assistant-widget">
      <section id="assistant-chat" className={`chat-window${open ? " chat-window-open" : ""}`} aria-label="Assistant de données" aria-hidden={!open}>
        <header className="chat-header">
          <div className="chat-brand">
            <span className="chat-avatar">✦</span>
            <span><strong>Assistant logistique</strong><small><i /> Analyse des données activée</small></span>
          </div>
          <div className="chat-header-actions">
            {messages.length > 0 && <button className="chat-icon-button" title="Effacer la conversation" aria-label="Effacer la conversation" disabled={send.isPending} onClick={() => setMessages([])}>↺</button>}
            <button className="chat-icon-button" title="Fermer l’assistant" aria-label="Fermer l’assistant" onClick={() => setOpen(false)}>×</button>
          </div>
        </header>
        <div className="chat-messages" aria-live="polite">
          {messages.length === 0 && (
            <div className="chat-welcome">
              <div className="chat-welcome-icon">✦</div>
              <h2>Comment puis-je vous aider ?</h2>
              <p>Je peux analyser les indicateurs et rechercher les points de blocage dans vos données.</p>
              <div className="chat-suggestions">{suggestions.map((suggestion) => <button key={suggestion} disabled={send.isPending} onClick={() => ask(suggestion)}>{suggestion}<span>↗</span></button>)}</div>
            </div>
          )}
          {messages.map((message, index) => (
            <article className={`chat-message chat-message-${message.role}${message.failed ? " chat-message-error" : ""}`} key={`${message.role}-${index}`}>
              {message.role === "assistant" && <span className="chat-message-avatar">✦</span>}
              <div className="chat-message-body">
                <div className="chat-bubble">{message.content}</div>
                {message.tools && message.tools.length > 0 && <small className="chat-meta">Sources consultées : {[...new Set(message.tools)].join(", ")}{message.source === "data" ? " · calcul direct" : message.source === "fallback" ? " · réponse de secours" : ""}</small>}
                {message.sources && message.sources.length > 0 && <small className="chat-meta">Documents : {[...new Set(message.sources.map(({ title, section }) => section ? `${title} · ${section}` : title))].join(" ; ")}</small>}
                {message.failed && <button className="chat-retry" disabled={send.isPending} onClick={() => retry(message, index)}>Réessayer cette question</button>}
              </div>
            </article>
          ))}
          {send.isPending && <div className="chat-message chat-message-assistant"><span className="chat-message-avatar">✦</span><div className="chat-bubble chat-thinking"><Spinner label="L’assistant analyse les données…" size="small" /></div></div>}
          <div ref={endRef} />
        </div>
        <form className="chat-composer" onSubmit={submit}>
          <textarea
            aria-label="Votre question"
            maxLength={1000}
            placeholder="Posez une question sur vos données…"
            rows={2}
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault();
                ask(question);
              }
            }}
          />
          <div className="chat-composer-footer"><span>{question.length}/1000 · Entrée pour envoyer</span><button className="chat-send-button" type="submit" aria-label="Envoyer la question" disabled={!question.trim() || send.isPending}>{send.isPending ? <Spinner size="small" /> : <span aria-hidden="true">↑</span>}</button></div>
        </form>
      </section>
      <button className={`assistant-launcher${open ? " assistant-launcher-open" : ""}`} aria-expanded={open} aria-controls="assistant-chat" onClick={() => setOpen((value) => !value)}>
        <span aria-hidden="true">{open ? "×" : "✦"}</span><span className="assistant-launcher-label">{open ? "Fermer" : "Assistant IA"}</span>
      </button>
    </div>
  );
}
