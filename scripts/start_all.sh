#!/bin/bash
# scripts/start_all.sh - Démarrage complet du système

cd /home/user/webapp

echo "🚀 Démarrage du Système Matriarche..."
echo "=================================="

# Créer dossiers nécessaires
mkdir -p data/{temp,cache,cve} logs /tmp/matriarche

# 1. Vérifier les dépendances
echo "[1/6] Vérification des dépendances..."
pip3 install -q -r requirements.txt 2>&1 | grep -i error || echo "  ✓ Dépendances OK"

# 2. Télécharger CVE database si nécessaire
echo "[2/6] Initialisation base CVE..."
if [ ! -f "data/cve/cve_database.json" ]; then
    echo "  Téléchargement CVE database 2023 (peut prendre quelques minutes)..."
    python3 utils/cve_database.py download 2023 > /dev/null 2>&1 &
    echo "  ✓ Téléchargement en arrière-plan"
else
    echo "  ✓ CVE database existante"
fi

# 3. Démarrer Matriarche (background)
echo "[3/6] Démarrage Matriarche..."
python3 matriarche/core/brain.py --daemon &
MATRIARCHE_PID=$!
echo $MATRIARCHE_PID > /tmp/matriarche/matriarche.pid
echo "  ✓ Matriarche démarrée (PID: $MATRIARCHE_PID)"

sleep 2

# 4. Démarrer Sous-Matriarches
echo "[4/6] Démarrage Sous-Matriarches..."
for i in {1..3}; do
    python3 sous_matriarche/sub_core.py --id "sub_$i" --daemon &
    PID=$!
    echo $PID >> /tmp/matriarche/sous_matriarche.pids
    echo "  ✓ Sous-Matriarche $i (PID: $PID)"
    sleep 1
done

# 5. Démarrer Proto-Agents
echo "[5/6] Démarrage Proto-Agents..."
for i in {1..10}; do
    python3 proto_agent/proto_core.py --id "proto_$(printf %03d $i)" --daemon &
    PID=$!
    echo $PID >> /tmp/matriarche/proto_agent.pids
    if [ $((i % 3)) -eq 0 ]; then
        echo "  ✓ Proto-Agents 1-$i démarrés..."
    fi
    sleep 0.5
done

echo "  ✓ 10 Proto-Agents démarrés"

# 6. Démarrer Monitoring API
echo "[6/6] Démarrage Monitoring API..."
cd monitoring/api
uvicorn main:app --host 0.0.0.0 --port 8000 > /tmp/matriarche/monitoring.log 2>&1 &
MONITORING_PID=$!
cd /home/user/webapp
echo $MONITORING_PID > /tmp/matriarche/monitoring.pid
echo "  ✓ Monitoring API (PID: $MONITORING_PID)"

sleep 2

echo ""
echo "=================================="
echo "✅ Système démarré avec succès!"
echo "=================================="
echo ""
echo "📊 Status:"
echo "  - Matriarche PID: $MATRIARCHE_PID"
echo "  - Sous-Matriarches: 3 instances"
echo "  - Proto-Agents: 10 instances"
echo "  - Monitoring API: http://localhost:8000"
echo ""
echo "📈 Vérifier status:"
echo "  curl http://localhost:8000/api/status"
echo ""
echo "🔴 Arrêter système:"
echo "  ./scripts/stop_all.sh"
echo ""
echo "🔄 Réinitialiser:"
echo "  ./scripts/reset_system.sh"
echo ""
