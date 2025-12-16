#!/bin/bash
# scripts/stop_all.sh - Arrêt propre du système

cd /home/user/webapp

echo "🛑 Arrêt du Système Matriarche..."
echo "=================================="

STOPPED=0

# 1. Arrêter Monitoring
echo "[1/4] Arrêt Monitoring API..."
if [ -f /tmp/matriarche/monitoring.pid ]; then
    PID=$(cat /tmp/matriarche/monitoring.pid)
    kill $PID 2>/dev/null && echo "  ✓ Monitoring arrêté (PID: $PID)" || echo "  ⚠ Monitoring déjà arrêté"
    rm /tmp/matriarche/monitoring.pid
    ((STOPPED++))
else
    echo "  ⚠ Monitoring n'était pas démarré"
fi

# 2. Arrêter Proto-Agents
echo "[2/4] Arrêt Proto-Agents..."
if [ -f /tmp/matriarche/proto_agent.pids ]; then
    COUNT=0
    while read PID; do
        kill $PID 2>/dev/null && ((COUNT++))
    done < /tmp/matriarche/proto_agent.pids
    echo "  ✓ $COUNT Proto-Agents arrêtés"
    rm /tmp/matriarche/proto_agent.pids
    ((STOPPED+=$COUNT))
else
    echo "  ⚠ Aucun Proto-Agent démarré"
fi

# 3. Arrêter Sous-Matriarches
echo "[3/4] Arrêt Sous-Matriarches..."
if [ -f /tmp/matriarche/sous_matriarche.pids ]; then
    COUNT=0
    while read PID; do
        kill $PID 2>/dev/null && ((COUNT++))
    done < /tmp/matriarche/sous_matriarche.pids
    echo "  ✓ $COUNT Sous-Matriarches arrêtées"
    rm /tmp/matriarche/sous_matriarche.pids
    ((STOPPED+=$COUNT))
else
    echo "  ⚠ Aucune Sous-Matriarche démarrée"
fi

# 4. Arrêter Matriarche
echo "[4/4] Arrêt Matriarche..."
if [ -f /tmp/matriarche/matriarche.pid ]; then
    PID=$(cat /tmp/matriarche/matriarche.pid)
    kill $PID 2>/dev/null && echo "  ✓ Matriarche arrêtée (PID: $PID)" || echo "  ⚠ Matriarche déjà arrêtée"
    rm /tmp/matriarche/matriarche.pid
    ((STOPPED++))
else
    echo "  ⚠ Matriarche n'était pas démarrée"
fi

# Nettoyage processus zombies
sleep 1
pkill -f "matriarche/core/brain.py" 2>/dev/null
pkill -f "sous_matriarche/sub_core.py" 2>/dev/null
pkill -f "proto_agent/proto_core.py" 2>/dev/null

echo ""
echo "=================================="
echo "✅ Système arrêté proprement!"
echo "=================================="
echo ""
echo "📊 Processus arrêtés: $STOPPED"
echo ""
echo "🚀 Redémarrer:"
echo "  ./scripts/start_all.sh"
echo ""
