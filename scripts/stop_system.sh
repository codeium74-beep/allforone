#!/bin/bash
# Script d'arrêt du système

echo "========================================="
echo "Arrêt du Système Matriarche"
echo "========================================="

# Fonction pour arrêter un composant
stop_component() {
    local pidfile=$1
    
    if [ -f "$pidfile" ]; then
        local pid=$(cat $pidfile)
        local name=$(basename $pidfile .pid)
        
        echo "Arrêt de $name (PID: $pid)..."
        
        if kill -0 $pid 2>/dev/null; then
            kill $pid
            sleep 1
            
            # Force kill si nécessaire
            if kill -0 $pid 2>/dev/null; then
                echo "  → Force kill de $name"
                kill -9 $pid 2>/dev/null || true
            fi
        else
            echo "  → Processus déjà arrêté"
        fi
        
        rm -f $pidfile
    fi
}

# Arrêt de tous les composants
for pidfile in /tmp/*.pid; do
    if [ -f "$pidfile" ]; then
        stop_component "$pidfile"
    fi
done

echo ""
echo "========================================="
echo "Système arrêté"
echo "========================================="
