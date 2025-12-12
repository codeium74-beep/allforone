#!/bin/bash
# Script de déploiement du système Matriarche

set -e

echo "========================================="
echo "Déploiement du Système Matriarche"
echo "========================================="

# Vérification Python
echo "Vérification de Python..."
python3 --version

# Installation des dépendances
echo "Installation des dépendances..."
pip3 install -r requirements.txt

# Création des répertoires de stockage
echo "Création des répertoires..."
mkdir -p /tmp/matriarche_storage
mkdir -p /tmp/matriarche_knowledge
mkdir -p /tmp/sub_storage
mkdir -p /tmp/proto_storage

# Vérification des permissions
echo "Vérification des permissions..."
chmod +x scripts/*.sh 2>/dev/null || true

echo "========================================="
echo "Déploiement terminé!"
echo "========================================="
echo ""
echo "Pour démarrer le système:"
echo "  python3 matriarche/core/brain.py"
echo ""
echo "Pour le monitoring:"
echo "  python3 monitoring/backend/api_server.py"
echo ""
