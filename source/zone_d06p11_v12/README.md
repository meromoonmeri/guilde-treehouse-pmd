# Zone D06P11 V12 — falaise V10 intacte, seul le second chemin ouvert
- **Falaise** : pixel pour pixel celle de la V10. Seule la zone du second chemin a changé (cases rangées 40-51, colonnes 20-47) : l'ancien goulet de 5 cases entre deux rebords est devenu une rampe ouverte. Vérifié par `fusion_v10.py` : 17 414 pixels modifiés, **tous dans cette zone**.
- La modification globale des rebords faite par erreur en V11 est annulée.
- **Sol** : herbe/chemin d05p11a posés exactement sur les cases de sable V10 (mêmes bords, sans arrondi) + les cases ouvertes. Rochers d13p11a et fleurs d05p11a en calques séparés, aucun décor sur le second chemin.
- Astres, mer, berge : comme V11 (soleil blanc le jour, soleil couchant généré au crépuscule).
- Collisions : V10 hors zone, recalculées dans la zone (1310 cases). Non testé en jeu.
Construction : `falaise_canon.py` → `fusion_v10.py` → `sol_canon.py` → `build.py`. Comparatif : `renders/zone_d06p11_v12/apercu/v10_vs_v12.png`.
