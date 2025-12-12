#!/bin/bash
# Script de démarrage complet du système

set -e

echo "========================================="
echo "Démarrage du Système Matriarche"
echo "========================================="

# Vérification que le système est déployé
if [ ! -d "/tmp/matriarche_storage" ]; then
    echo "Système non déployé. Exécutez d'abord ./scripts/deploy.sh"
    exit 1
fi

# Fonction pour démarrer un composant en arrière-plan
start_component() {
    local name=$1
    local command=$2
    
    echo "Démarrage de $name..."
    $command > /tmp/${name}.log 2>&1 &
    echo $! > /tmp/${name}.pid
    echo "  → PID: $(cat /tmp/${name}.pid)"
}

# Démarrage de la Matriarche
start_component "matriarche" "python3 matriarche/core/brain.py"

# Attente de l'initialisation
sleep 2

# Démarrage des Sous-Matriarches
for i in {1..3}; do
    start_component "sub_matriarche_$i" "python3 sous_matriarche/sub_brain.py sub_00$i"
    sleep 1
done

# Démarrage des Percepteurs
for i in {1..2}; do
    start_component "perceptor_$i" "python3 percepteur/perceptor_core.py"
    sleep 1
done

# Démarrage de l'API de monitoring
start_component "monitoring_api" "python3 monitoring/backend/api_server.py"

echo ""
echo "========================================="
echo "Système démarré!"
echo "========================================="
echo ""
echo "Composants actifs:"
ls -1 /tmp/*.pid 2>/dev/null | while read pidfile; do
    name=$(basename $pidfile .pid)
    pid=$(cat $pidfile)
    echo "  - $name (PID: $pid)"
done

echo ""
echo "Monitoring API: http://localhost:8000"
echo "Logs disponibles dans /tmp/*.log"
echo ""
echo "Pour arrêter le système: ./scripts/stop_system.sh"
echo ""
