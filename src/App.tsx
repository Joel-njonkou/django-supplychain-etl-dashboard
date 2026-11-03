import React, { useState } from 'react';
import { DashboardLogistique } from './pages/DashboardLogistique';
import { AnalyseGlobale } from './pages/AnalyseGlobale';
import { ChatAgent } from './pages/ChatAgent'; // Import la page de chat
import { Boxes, LayoutDashboard, BarChart3, Menu } from 'lucide-react';

function App() {
  // Ajoute chat aux choix possibles de la vue
  const [currentView, setCurrentView] = useState<'logistique' | 'globale' | 'chat'>('logistique');
  const [sidebarOpen, setSidebarOpen] = useState(true);
 
  // Stockez les données de la ligne cliquée
  const [selectedContext, setSelectedContext] = useState<any>(null);

  // Fonction déclenchée lors du clic sur une ligne du tableau logistique
  const handleRowClick = (contextData: any) => {
    setSelectedContext(contextData);
    setCurrentView('chat'); // Bascule automatiquement sur la page de chat
  };

  return (
    <div className="min-h-screen w-screen bg-slate-950 text-slate-100 flex font-sans overflow-x-hidden">
    
      {/* BARRE LATÉRALE (SIDEBAR) */}
      <aside className={`bg-slate-900 border-r border-slate-800 transition-all duration-300 ${sidebarOpen ? 'w-64' : 'w-16'} flex flex-col shrink-0 min-h-screen z-10`}>
        <div className="p-4 border-b border-slate-800 flex items-center justify-between">
          {sidebarOpen && (
            <div className="flex items-center space-x-2 truncate">
              <Boxes className="w-5 h-5 text-sky-400 shrink-0" />
              <span className="font-bold text-xs text-slate-100 uppercase tracking-wider truncate">DataSupply BI</span>
            </div>
          )}
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="p-1.5 rounded hover:bg-slate-800 text-slate-400 transition-colors mx-auto"
            title="Réduire / Ouvrir le menu"
          >
            <Menu className="w-4 h-4" />
          </button>
        </div>

        <nav className="p-3 space-y-1.5 flex-1">
          <button
            onClick={() => setCurrentView('logistique')}
            className={`w-full flex items-center space-x-3 px-3 py-2.5 rounded text-xs font-semibold transition-colors ${
              currentView === 'logistique' || currentView === 'chat' // Surligne le menu logistique si on est dans le chat
                ? 'bg-sky-500/10 text-sky-400 border border-sky-500/20'
                : 'text-slate-400 hover:bg-slate-800/50 hover:text-slate-200'
            }`}
          >
            <LayoutDashboard className="w-4 h-4 shrink-0" />
            {sidebarOpen && <span className="truncate">Dashboard Logistique</span>}
          </button>

          <button
            onClick={() => setCurrentView('globale')}
            className={`w-full flex items-center space-x-3 px-3 py-2.5 rounded text-xs font-semibold transition-colors ${
              currentView === 'globale'
                ? 'bg-sky-500/10 text-sky-400 border border-sky-500/20'
                : 'text-slate-400 hover:bg-slate-800/50 hover:text-slate-200'
            }`}
          >
            <BarChart3 className="w-4 h-4 shrink-0" />
            {sidebarOpen && <span className="truncate">Analyse Globale</span>}
          </button>
        </nav>
      </aside>

      {/* ZONE PRINCIPALE DE CONTENU */}
      <div className="flex-1 flex flex-col min-h-screen min-w-0 overflow-y-auto bg-slate-950">
        <header className="bg-slate-900 border-b border-slate-800 px-6 py-3.5 flex items-center justify-between w-full">
          <span className="text-xs font-bold text-slate-300 uppercase tracking-wider">
            {currentView === 'logistique' && 'Vue Synthétique Logistique'}
            {currentView === 'globale' && 'Analyse Globale & Filtres'}
            {currentView === 'chat' && 'Assistant IA — Analyse Contextuelle'}
          </span>
          <div className="flex items-center space-x-2">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
            <span className="text-xs bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-2.5 py-1 rounded-full font-semibold">
              Django & React Connectés
            </span>
          </div>
        </header>

        <main className="flex-1 p-6 w-full">
          {/* Affiche la bonne page selon l'état actuel */}
          {currentView === 'logistique' && <DashboardLogistique onRowClick={handleRowClick} />}
          {currentView === 'globale' && <AnalyseGlobale />}
          {currentView === 'chat' && <ChatAgent contextData={selectedContext} onBack={() => setCurrentView('logistique')} />}
        </main>
      </div>

    </div>
  );
}

export default App;