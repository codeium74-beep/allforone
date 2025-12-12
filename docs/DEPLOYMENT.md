# Guide de Déploiement

## Prérequis

- Python 3.11+
- 8GB RAM minimum
- 20GB espace disque
- Linux (Ubuntu 20.04+ recommandé)

## Installation

### 1. Clonage du dépôt

```bash
git clone <repository-url>
cd webapp
```

### 2. Installation des dépendances

```bash
pip3 install -r requirements.txt
```

### 3. Déploiement initial

```bash
chmod +x scripts/*.sh
./scripts/deploy.sh
```

## Démarrage du Système

### Démarrage complet

```bash
./scripts/start_system.sh
```

Cela démarre:
- 1 Matriarche
- 3 Sous-Matriarches
- 2 Percepteurs
- API de monitoring

### Démarrage manuel des composants

#### Matriarche

```bash
python3 matriarche/core/brain.py
```

#### Sous-Matriarche

```bash
python3 sous_matriarche/sub_brain.py sub_001
```

#### Proto-Agent

```bash
python3 proto_agent/proto_core.py proto_001
```

#### Percepteur

```bash
python3 percepteur/perceptor_core.py
```

#### API Monitoring

```bash
python3 monitoring/backend/api_server.py
```

## Accès au Monitoring

Une fois démarré, accédez à:
- API: http://localhost:8000
- Documentation API: http://localhost:8000/docs
- WebSocket: ws://localhost:8000/ws/live

## Envoi d'une Mission

### Via API

```bash
curl -X POST http://localhost:8000/api/missions \
  -H "Content-Type: application/json" \
  -d '{
    "mission_id": "mission_001",
    "objective": "Scan network and identify vulnerable systems",
    "priority": "high",
    "auth_token": "warrior"
  }'
```

### Via Python

```python
import requests

mission = {
    'mission_id': 'mission_001',
    'objective': 'Access file /opt/secret.txt on server-prod-01',
    'priority': 'normal',
    'auth_token': 'warrior'
}

response = requests.post('http://localhost:8000/api/missions', json=mission)
print(response.json())
```

## Arrêt du Système

### Arrêt propre

```bash
./scripts/stop_system.sh
```

### Kill Switch manuel

```bash
# Niveau 1: Pause
curl -X POST http://localhost:8000/api/killswitch/activate \
  -H "Content-Type: application/json" \
  -d '{"level": 1, "reason": "manual pause"}'

# Niveau 2: Retrait
curl -X POST http://localhost:8000/api/killswitch/activate \
  -H "Content-Type: application/json" \
  -d '{"level": 2, "reason": "manual retreat"}'

# Niveau 3: Arrêt d'urgence
curl -X POST http://localhost:8000/api/killswitch/activate \
  -H "Content-Type: application/json" \
  -d '{"level": 3, "reason": "emergency"}'
```

## Configuration

### Matriarche

Éditez `matriarche/core/brain.py` pour ajuster:
- `min_sleep`: Temps minimum entre réveils
- `max_sleep`: Temps maximum entre réveils
- `replication_factor`: Facteur de réplication des données

### Sous-Matriarches

Éditez `sous_matriarche/sub_brain.py` pour ajuster:
- `proto_pool_size`: Nombre de Proto-Agents par Sub
- `report_interval`: Intervalle de rapport à la Matriarche

### Proto-Agents

Comportement autonome, pas de configuration nécessaire.

## Tests

### Test PoW

```bash
python3 pow_pom/proof_of_work.py
```

### Test PoM

```bash
python3 pow_pom/proof_of_memory.py
```

### Test Kill Switch

```bash
python3 monitoring/backend/kill_switch.py
```

## Monitoring en Temps Réel

### Via WebSocket (Python)

```python
import asyncio
import websockets
import json

async def monitor():
    uri = "ws://localhost:8000/ws/live"
    async with websockets.connect(uri) as websocket:
        while True:
            data = await websocket.recv()
            metrics = json.loads(data)
            print(f"CPU: {metrics['data']['cpu']['total_percent']:.1f}%")

asyncio.run(monitor())
```

### Via API REST

```bash
# Status global
curl http://localhost:8000/api/status

# Métriques système
curl http://localhost:8000/api/metrics/system

# Hiérarchie
curl http://localhost:8000/api/hierarchy/summary

# Missions
curl http://localhost:8000/api/missions
```

## Logs

Les logs sont disponibles dans:
- `/tmp/matriarche.log`
- `/tmp/sub_matriarche_*.log`
- `/tmp/proto_*.log`
- `/tmp/perceptor_*.log`
- `/tmp/monitoring_api.log`

## Dépannage

### La Matriarche ne démarre pas

Vérifiez:
- Python 3.11+ installé
- Dépendances installées
- Répertoires créés (`/tmp/matriarche_storage`)

### Aucune mission n'est exécutée

Vérifiez:
- Le token d'authentification (`warrior`)
- Les Sous-Matriarches sont démarrées
- Les Proto-Agents sont initialisés

### API de monitoring inaccessible

Vérifiez:
- Port 8000 disponible
- Processus `monitoring_api` en cours d'exécution
- Logs dans `/tmp/monitoring_api.log`

## Sécurité

⚠️ **IMPORTANT**: Ce système est destiné à un usage contrôlé uniquement.

- Changez le token d'authentification par défaut
- Limitez l'accès réseau
- Activez le Kill Switch en cas de problème
- Surveillez les logs régulièrement
