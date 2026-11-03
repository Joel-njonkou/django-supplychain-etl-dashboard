import React, { useEffect, useState } from 'react';
import { getTauxLivraison, getCoutMoyen, getPointsDeBlocage, getKPIsGlobaux } from '../services/api';
import type { TauxLivraisonData, CoutMoyenData, PointDeBlocage, KPIsGlobaux } from '../types';
import {
  TrendingUp,
  DollarSign,
  Package,
  Clock,
  Globe,
  Award,
  Boxes,
  AlertTriangle
} from 'lucide-react';

interface DashboardLogistiqueProps {
  onRowClick: (contextData: any) => void;
}

export const DashboardLogistique: React.FC<DashboardLogistiqueProps> = ({ onRowClick }) => {
  const [tauxLivraison, setTauxLivraison] = useState<TauxLivraisonData | null>(null);
  const [coutMoyen, setCoutMoyen] = useState<CoutMoyenData | null>(null);
  const [pointsBlocage, setPointsBlocage] = useState<PointDeBlocage[]>([]);
  const [kpisGlobaux, setKpisGlobaux] = useState<KPIsGlobaux | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const resTaux = await getTauxLivraison();
        const resCout = await getCoutMoyen();
        const resBlocage = await getPointsDeBlocage();
        const resKPIs = await getKPIsGlobaux();

        setTauxLivraison(resTaux.data);
        setCoutMoyen(resCout.data);
        setKpisGlobaux(resKPIs);

        if (resBlocage.data && resBlocage.data.points_de_blocage_region) {
          setPointsBlocage(resBlocage.data.points_de_blocage_region);
        } else if (Array.isArray(resBlocage.data)) {
          setPointsBlocage(resBlocage.data);
        }
      } catch (error) {
        console.error("Erreur lors de la récupération des données Django :", error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="p-4 text-slate-400 text-xs">
        Chargement de votre Dashboard Logistique...
      </div>
    );
  }

  return (
    <div className="p-6 font-sans space-y-5 text-slate-100 w-full">
    
      {/* En-tête */}
      <div className="flex items-center space-x-2 pb-2 border-b border-slate-800/80">
        <Boxes className="w-5 h-5 text-sky-400" />
        <span className="text-xs font-bold tracking-wider text-slate-200 uppercase">
          DataSupply — Vue Synthétique Logistique
        </span>
      </div>
 
      {/* Barre de KPI Synthétique */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-lg p-3 grid grid-cols-2 md:grid-cols-4 gap-3">
      
        <div className="flex flex-col justify-center px-2">
          <div className="flex items-center space-x-1.5 text-slate-400 text-[11px] mb-0.5">
            <TrendingUp className="w-3.5 h-3.5 text-emerald-400" />
            <span>Taux Livraison</span>
          </div>
          <span className="text-lg font-bold text-emerald-400">
            {tauxLivraison ? `${tauxLivraison.taux_livraison_a_temps}%` : 'N/A'}
          </span>
        </div>

        <div className="flex flex-col justify-center px-2 border-l border-slate-800/80">
          <div className="flex items-center space-x-1.5 text-slate-400 text-[11px] mb-0.5">
            <DollarSign className="w-3.5 h-3.5 text-indigo-400" />
            <span>Coût Moyen</span>
          </div>
          <span className="text-lg font-bold text-indigo-400">
            {coutMoyen ? `${coutMoyen.cout_moyen_expedition} €` : 'N/A'}
          </span>
        </div>

        <div className="flex flex-col justify-center px-2 border-l border-slate-800/80">
          <div className="flex items-center space-x-1.5 text-slate-400 text-[11px] mb-0.5">
            <Package className="w-3.5 h-3.5 text-sky-400" />
            <span>Volume Total</span>
          </div>
          <span className="text-lg font-bold text-sky-400">
            {kpisGlobaux ? kpisGlobaux.volume_total_expeditions.toLocaleString() : 'N/A'}
          </span>
        </div>

        <div className="flex flex-col justify-center px-2 border-l border-slate-800/80">
          <div className="flex items-center space-x-1.5 text-slate-400 text-[11px] mb-0.5">
            <Clock className="w-3.5 h-3.5 text-amber-400" />
            <span>Retard Moyen</span>
          </div>
          <span className="text-lg font-bold text-amber-400">
            {kpisGlobaux ? `+${kpisGlobaux.retard_moyen_jours} j` : 'N/A'}
          </span>
        </div>

      </div>

      {/* Bénéfice & Marchés Principaux */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        <div className="bg-slate-900/60 border border-slate-800 rounded-lg p-3 flex flex-col justify-center">
          <div className="flex items-center space-x-1.5 text-slate-400 text-[11px] mb-1">
            <Award className="w-3.5 h-3.5 text-emerald-400" />
            <span>Bénéfice Net & Marge</span>
          </div>
          <div className="flex items-baseline space-x-2">
            <span className="text-lg font-bold text-emerald-400">
              {kpisGlobaux ? `${Math.round(kpisGlobaux.benefice_total).toLocaleString()} €` : 'N/A'}
            </span>
            <span className="text-xs font-semibold text-emerald-500">
              {kpisGlobaux ? `(${kpisGlobaux.marge_beneficiaire_pct}%)` : ''}
            </span>
          </div>
        </div>

        <div className="md:col-span-2 bg-slate-900/60 border border-slate-800 rounded-lg p-3">
          <div className="flex items-center space-x-1.5 mb-2">
            <Globe className="w-3.5 h-3.5 text-purple-400" />
            <span className="text-[11px] font-semibold text-slate-300 uppercase tracking-wider">
              Marchés Principaux
            </span>
          </div>
          <div className="grid grid-cols-3 gap-2">
            {kpisGlobaux && kpisGlobaux.top_marches ? (
              kpisGlobaux.top_marches.map((m, idx) => (
                <div
                  key={m.market}
                  className="flex items-center justify-between bg-slate-950/40 px-2.5 py-1.5 rounded border border-slate-800/60"
                >
                  <div className="flex items-center space-x-1.5 truncate">
                    <span className={`text-[10px] font-bold px-1 py-0.2 rounded ${
                      idx === 0 ? 'bg-purple-500/20 text-purple-300 border border-purple-500/30' : 'bg-slate-800 text-slate-400'
                    }`}>
                      #{idx + 1}
                    </span>
                    <span className="text-xs font-medium text-slate-200 truncate">{m.market}</span>
                  </div>
                  <span className="text-[11px] font-semibold text-purple-400 ml-1">
                    {m.total.toLocaleString()}
                  </span>
                </div>
              ))
            ) : (
              <div className="text-slate-500 text-xs italic">Chargement...</div>
            )}
          </div>
        </div>
      </div>

      {/* Tableau des Points de Blocage */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-lg p-3">
        <div className="flex items-center space-x-1.5 mb-2.5">
          <AlertTriangle className="w-3.5 h-3.5 text-rose-400" />
          <h2 className="text-[11px] font-semibold text-slate-300 uppercase tracking-wider">
            Analyse des Points de Blocage par Région (Cliquez sur une ligne pour l'analyser avec l'IA)
          </h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs text-slate-300">
            <thead>
              <tr className="bg-slate-950/80 text-slate-400 border-b border-slate-800 text-[11px]">
                <th className="py-1.5 px-3 font-semibold">Région</th>
                <th className="py-1.5 px-3 font-semibold">Expéditions</th>
                <th className="py-1.5 px-3 font-semibold">Retards</th>
                <th className="py-1.5 px-3 font-semibold">Niveau de Risque / Ratio</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/40">
              {pointsBlocage.map((item, index) => {
                const ratio = item.total_expeditions > 0
                  ? Math.round((item.total_retards / item.total_expeditions) * 100)
                  : 0;

                return (
                  <tr
                    key={index}
                    onClick={() => onRowClick({
                      region: item.commande__order_region,
                      total_expeditions: item.total_expeditions,
                      retards: item.total_retards,
                      taux_retard: `${ratio}%`
                    })}
                    className="hover:bg-sky-950/30 cursor-pointer transition-colors"
                  >
                    <td className="py-2 px-3 font-medium text-slate-200">{item.commande__order_region}</td>
                    <td className="py-2 px-3 text-slate-400">{item.total_expeditions.toLocaleString()}</td>
                    <td className="py-2 px-3 text-rose-400 font-semibold">{item.total_retards.toLocaleString()}</td>
                    <td className="py-2 px-3">
                      <div className="flex items-center space-x-2">
                        <div className="w-24 bg-slate-800 h-1.5 rounded-full overflow-hidden">
                          <div
                            className={`h-full ${ratio > 40 ? 'bg-rose-500' : ratio > 25 ? 'bg-amber-500' : 'bg-emerald-500'}`}
                            style={{ width: `${Math.min(ratio, 100)}%` }}
                          />
                        </div>
                        <span className={`text-[11px] font-bold ${ratio > 40 ? 'text-rose-400' : ratio > 25 ? 'text-amber-400' : 'text-emerald-400'}`}>
                          {ratio}%
                        </span>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

    </div>
  );
};