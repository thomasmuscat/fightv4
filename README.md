# FightIQ Data Engine Fix V4

Version de correction pour le problème `found=0`.

Elle ajoute :
- HTTPS officiel UFCStats
- logs de diagnostic
- sauvegarde du HTML reçu dans `debug/`
- parser fighters plus flexible
- export d’un rapport JSON
- artifacts debug GitHub Actions

Premier test :
- upload_to_supabase: false
- max_events: 5
- max_fighters: 20
- max_fights: 50

Si les CSV sont encore à 0, télécharge l'artifact `fightiq-v4-debug` et regarde `fighters_a_debug.html`.
