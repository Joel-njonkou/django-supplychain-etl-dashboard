
def quality_report(orders, rejects, stats) -> str:
    actives = orders[orders["statut_livraison"] != "annulee"]
    
    lines = [
        f"Lignes lues : {stats.get('rows_in', 0)}",
        f"Lignes rejetées : {stats.get('rows_rejected', 0)}",
        f"Doublons supprimés : {stats.get('duplicates_dropped', 0)}",
        f"Commandes produites : {stats.get('orders_out', 0)}",
        f"Lignes de commande   : {stats.get('order_lines_out', 0)}",
        f"Commandes incohérentes : {stats.get('commandes_incoherentes', 0)}",
        f"Incohérences retard    : {stats.get('incoherences_retard', 0)}",
        f"Taux d'annulation      : {1 - len(actives) / len(orders) if len(orders) > 0 else 0:.1%}",
        f"Taux de retard global  : {actives['en_retard'].mean():.1%}" if len(actives) > 0 else "Taux de retard global  : 0.0%",
        f"Période                : {orders['date_commande'].min():%Y-%m-%d} -> {orders['date_commande'].max():%Y-%m-%d}" if not orders.empty else "Période : N/A",
    ]
    
    if len(rejects):
        lines.append("Motifs de rejet        : " + ", ".join(f"{k}={v}" for k, v in
            rejects["motif"].value_counts().items()))
            
    return "\n".join(lines)