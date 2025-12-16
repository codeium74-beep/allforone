#!/bin/bash
# scripts/reset_system.sh - Réinitialisation complète

cd /home/user/webapp

echo "🔄 Réinitialisation du Système Matriarche..."
echo "============================================="
echo ""
echo "⚠️  ATTENTION: Cette opération va:"
echo "  - Arrêter tous les processus"
echo "  - Supprimer toutes les données temporaires"
echo "  - Réinitialiser les bases de données"
echo "  - Nettoyer tous les logs"
echo ""
read -p "Continuer? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Annulé."
    exit 1
fi

echo ""

# 1. Arrêter tous les processus
echo "[1/6] Arrêt de tous les processus..."
./scripts/stop_all.sh > /dev/null 2>&1
echo "  ✓ Tous les processus arrêtés"

sleep 2

# 2. Nettoyer les données temporaires
echo "[2/6] Nettoyage données temporaires..."
rm -rf /tmp/matriarche_* /tmp/proto_* /tmp/sub_* /tmp/matriarche 2>/dev/null
rm -rf data/temp/* data/cache/* 2>/dev/null
echo "  ✓ Données temporaires nettoyées"

# 3. Réinitialiser bases de données locales
echo "[3/6] Réinitialisation bases de données..."
rm -f data/knowledge_*.db 2>/dev/null
rm -f data/discoveries_*.json 2>/dev/null
rm -f data/*.sqlite 2>/dev/null
echo "  ✓ Bases de données réinitialisées"

# 4. Nettoyer logs
echo "[4/6] Nettoyage logs..."
rm -f logs/*.log 2>/dev/null
rm -f logs/*.log.* 2>/dev/null
echo "  ✓ Logs nettoyés"

# 5. Re-créer structure
echo "[5/6] Recréation structure..."
mkdir -p data/{temp,cache,cve} logs /tmp/matriarche
touch logs/.gitkeep
touch data/temp/.gitkeep
touch data/cache/.gitkeep
echo "  ✓ Structure recréée"

# 6. Vérification
echo "[6/6] Vérification..."
DIRS="data/temp data/cache data/cve logs /tmp/matriarche"
ALL_OK=true
for dir in $DIRS; do
    if [ ! -d "$dir" ]; then
        echo "  ✗ Erreur: $dir manquant"
        ALL_OK=false
    fi
done

if $ALL_OK; then
    echo "  ✓ Vérification réussie"
else
    echo "  ✗ Erreurs détectées"
    exit 1
fi

echo ""
echo "============================================="
echo "✅ Système réinitialisé avec succès!"
echo "============================================="
echo ""
echo "📊 État du système:"
echo "  - Processus actifs: 0"
echo "  - Données temporaires: nettoyées"
echo "  - Bases de données: réinitialisées"
echo "  - Logs: nettoyés"
echo ""
echo "🚀 Redémarrer le système:"
echo "  ./scripts/start_all.sh"
echo ""
