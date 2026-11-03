import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { ArrowLeft, Send, Bot, User } from 'lucide-react';

interface ChatAgentProps {
  contextData: any;
  onBack: () => void;
}

export const ChatAgent: React.FC<ChatAgentProps> = ({ contextData, onBack }) => {
  const [messages, setMessages] = useState<Array<{ sender: 'user' | 'ai'; text: string }>>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(false);

  // Déclenchement automatique de l'analyse dès l'ouverture avec le contexte cliqué
  useEffect(() => {
    if (contextData) {
      const initialQuestion = `Analyse cette situation : Région ${contextData.region || 'Globale'}, ${contextData.retards || 0} retards sur ${contextData.total_expeditions || 0} expéditions (Taux de retard : ${contextData.taux_retard || 'N/A'}). Quelles sont les causes et les solutions ?`;
      triggerAiChat(initialQuestion, contextData);
    }
  }, [contextData]);

  const triggerAiChat = async (msg: string, ctx: any) => {
    setMessages(prev => [...prev, { sender: 'user', text: msg }]);
    setLoading(true);
    try {
      const response = await axios.post('http://127.0.0.1:8000/api/agent-chat/', {
        message: msg,
        context: ctx
      });
      if (response.data.status === 'success') {
        setMessages(prev => [...prev, { sender: 'ai', text: response.data.response }]);
      }
    } catch (error) {
      setMessages(prev => [...prev, { sender: 'ai', text: "Erreur de communication avec le modèle local Ollama." }]);
    } finally {
      setLoading(false);
    }
  };

  const handleSend = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputMessage.trim() || loading) return;
    const msg = inputMessage;
    setInputMessage('');
    triggerAiChat(msg, contextData);
  };

  return (
    <div className="p-6 font-sans space-y-4 text-slate-100 w-full max-w-4xl mx-auto">
      <button
        onClick={onBack}
        className="flex items-center space-x-2 text-xs text-sky-400 hover:text-sky-300 transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        <span>Retour au tableau de bord</span>
      </button>

      <div className="bg-slate-900 border border-slate-800 rounded-lg p-4 flex flex-col h-[75vh]">
        <div className="flex items-center space-x-2 pb-3 border-b border-slate-800">
          <Bot className="w-5 h-5 text-sky-400" />
          <h2 className="text-xs font-bold uppercase tracking-wider text-slate-200">
            Assistant IA Supply Chain — Analyse Contextuelle
          </h2>
        </div>

        <div className="flex-1 overflow-y-auto space-y-4 py-4 pr-2">
          {messages.map((m, idx) => (
            <div key={idx} className={`flex items-start space-x-3 ${m.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
              {m.sender === 'ai' && (
                <div className="w-7 h-7 rounded-full bg-sky-500/20 border border-sky-500/30 flex items-center justify-center text-sky-400 shrink-0">
                  <Bot className="w-4 h-4"/>
                </div>
              )}
              <div className={`max-w-[80%] rounded-lg p-3 text-xs leading-relaxed whitespace-pre-wrap ${
                m.sender === 'user'
                  ? 'bg-sky-600 text-white'
                  : 'bg-slate-950 text-slate-200 border border-slate-800'
              }`}>
                {m.text}
              </div>
              {m.sender === 'user' && (
                <div className="w-7 h-7 rounded-full bg-slate-800 flex items-center justify-center text-slate-300 shrink-0">
                  <User className="w-4 h-4"/>
                </div>
              )}
            </div>
          ))}
          {loading && (
            <div className="flex items-center space-x-2 text-slate-400 text-xs italic pl-10">
              <div className="w-2 h-2 rounded-full bg-sky-400 animate-pulse"/>
              <span>L'IA analyse les données en cours...</span>
            </div>
          )}
        </div>

        <form onSubmit={handleSend} className="pt-3 border-t border-slate-800 flex space-x-2">
          <input
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            placeholder="Posez une question complémentaire sur ces données..."
            className="flex-1 bg-slate-950 border border-slate-800 rounded px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-sky-500"
          />
          <button
            type="submit"
            disabled={loading}
            className="bg-sky-600 hover:bg-sky-500 text-white px-4 py-2 rounded text-xs font-semibold flex items-center space-x-1 transition-colors disabled:opacity-50"
          >
            <Send className="w-3.5 h-3.5"/>
          </button>
        </form>
      </div>
    </div>
  );
};