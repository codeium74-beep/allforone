# Guide d'Utilisation

## Scénarios d'Usage

### Scénario 1: Reconnaissance Réseau

#### Objectif
Scanner un réseau pour identifier les systèmes vulnérables.

#### Configuration Mission

```python
mission = {
    'mission_id': 'recon_001',
    'objective': 'Scan network 192.168.1.0/24 and identify vulnerable systems',
    'priority': 'normal',
    'constraints': {
        'stealth': 'high',
        'duration_max': 7200  # 2 heures
    },
    'auth_token': 'warrior'
}
```

#### Processus

1. **Envoi de la mission**:
```bash
curl -X POST http://localhost:8000/api/missions \
  -H "Content-Type: application/json" \
  -d @mission_recon.json
```

2. **Surveillance de la progression**:
```bash
# Via API
curl http://localhost:8000/api/missions | jq '.active'

# Via logs
tail -f /tmp/matriarche.log
```

3. **Résultats attendus**:
   - Liste des systèmes découverts
   - Services identifiés
   - Vulnérabilités potentielles

### Scénario 2: Exfiltration de Fichier

#### Objectif
Accéder à un fichier spécifique sur un système cible.

#### Configuration Mission

```python
mission = {
    'mission_id': 'exfil_001',
    'objective': 'Access file /opt/secret.txt on server-prod-01',
    'priority': 'high',
    'constraints': {
        'stealth': 'maximum',
        'no_traces': True
    },
    'auth_token': 'warrior'
}
```

#### Stratégie Automatique

Le système planifiera:
1. Reconnaissance du serveur cible
2. Identification des chemins d'accès
3. Exploitation des vulnérabilités
4. Récupération du fichier
5. Nettoyage des traces

### Scénario 3: Persistence Multi-Système

#### Objectif
Établir une présence persistante sur plusieurs systèmes.

#### Configuration Mission

```python
mission = {
    'mission_id': 'persist_001',
    'objective': 'Establish persistence on critical infrastructure systems',
    'priority': 'low',  # Lent et discret
    'constraints': {
        'stealth': 'maximum',
        'slow_deployment': True,
        'redundancy': 3
    },
    'auth_token': 'warrior'
}
```

## Commandes Avancées

### Contrôle de la Matriarche

#### Forcer un réveil
```python
# Via code
from matriarche.core.brain import MatriarchBrain

brain.timer.force_wake()
```

#### Entrer en sommeil profond
```python
brain.timer.enter_deep_sleep(duration=3600)  # 1 heure
```

### Gestion des Sous-Matriarches

#### Lister les Subs actives
```bash
curl http://localhost:8000/api/hierarchy/subs | jq '.subs'
```

#### Ajouter une nouvelle Sub
```bash
python3 sous_matriarche/sub_brain.py sub_004
```

### Gestion des Proto-Agents

#### Monitorer un Proto spécifique
```bash
curl http://localhost:8000/api/hierarchy/protos | jq '.protos.proto_001'
```

#### Injecter une mutation
```python
from proto_agent.proto_core import ProtoAgent

proto = ProtoAgent({'node_id': 'proto_001'})
mutation = {
    'payload': b'...',  # Code muté
    'generation': 5
}
proto.receive_mutation(mutation)
```

### Contrôle du Kill Switch

#### Activer manuellement un niveau
```bash
# Niveau 1: Pause
curl -X POST http://localhost:8000/api/killswitch/activate \
  -H "Content-Type: application/json" \
  -d '{"level": 1, "reason": "manual intervention"}'

# Niveau 2: Retrait
curl -X POST http://localhost:8000/api/killswitch/activate \
  -H "Content-Type: application/json" \
  -d '{"level": 2, "reason": "detected activity"}'

# Niveau 3: Emergency Stop
curl -X POST http://localhost:8000/api/killswitch/activate \
  -H "Content-Type: application/json" \
  -d '{"level": 3, "reason": "compromised"}'
```

#### Vérifier le statut
```bash
curl http://localhost:8000/api/killswitch/status
```

## Monitoring en Temps Réel

### Dashboard Web (à implémenter)

```html
<!DOCTYPE html>
<html>
<head>
    <title>Matriarche Monitor</title>
</head>
<body>
    <div id="status"></div>
    <script>
        const ws = new WebSocket('ws://localhost:8000/ws/live');
        
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            document.getElementById('status').innerHTML = 
                `CPU: ${data.data.cpu.total_percent.toFixed(1)}%`;
        };
    </script>
</body>
</html>
```

### Monitoring via Python

```python
import asyncio
import websockets
import json

async def monitor():
    uri = "ws://localhost:8000/ws/live"
    
    async with websockets.connect(uri) as websocket:
        while True:
            try:
                data = await websocket.recv()
                metrics = json.loads(data)
                
                print(f"[{metrics['timestamp']}]")
                print(f"  CPU: {metrics['data']['cpu']['total_percent']:.1f}%")
                print(f"  RAM: {metrics['data']['memory']['percent']:.1f}%")
                print()
                
            except Exception as e:
                print(f"Error: {e}")
                break

asyncio.run(monitor())
```

## Analyse des Résultats

### Extraction des Découvertes

```bash
# Systèmes découverts
curl http://localhost:8000/api/hierarchy/summary | \
  jq '.sub_matriarches.total_protos'

# Missions complétées
curl http://localhost:8000/api/missions | \
  jq '.completed[] | {id: .mission_id, duration: .duration, success: .result.success}'
```

### Génération de Rapports

```python
import requests
import json

# Récupération du statut global
status = requests.get('http://localhost:8000/api/status').json()

# Génération rapport
report = {
    'timestamp': status['timestamp'],
    'matriarche_state': status['hierarchy']['matriarche']['status'],
    'active_agents': status['hierarchy']['proto_agents']['count'],
    'missions_completed': status['missions']['completed_count'],
    'success_rate': status['missions']['success_rate']
}

print(json.dumps(report, indent=2))
```

## Dépannage Avancé

### La Matriarche ne se réveille pas

**Symptômes**: Aucune activité après démarrage

**Solutions**:
1. Vérifier le timer:
```python
print(brain.timer.get_sleep_status())
```

2. Forcer un réveil:
```python
brain.timer.force_wake()
```

3. Vérifier les logs:
```bash
grep "Waking up" /tmp/matriarche.log
```

### Protos ne communiquent pas en P2P

**Symptômes**: Pas d'échanges dans les logs

**Solutions**:
1. Vérifier découverte réseau:
```bash
avahi-browse -a
```

2. Tester beacon:
```python
from utils.network_utils import MulticastBeacon
beacon = MulticastBeacon('test', 'test')
discovered = beacon.listen_for_beacons(10)
print(discovered)
```

### Kill Switch ne s'active pas

**Symptômes**: Pas de réponse aux déclencheurs

**Solutions**:
1. Vérifier armement:
```bash
curl http://localhost:8000/api/killswitch/status | jq '.armed'
```

2. Réarmer:
```bash
curl -X POST http://localhost:8000/api/killswitch/rearm
```

3. Activer manuellement:
```bash
curl -X POST http://localhost:8000/api/killswitch/activate \
  -d '{"level": 1, "reason": "test"}'
```

## Bonnes Pratiques

### Sécurité

1. **Changer le token par défaut**:
```python
# Dans la config
config = {
    'master_key': 'your_secure_token_here'
}
```

2. **Limiter l'accès réseau**:
```bash
# Firewall rules
iptables -A INPUT -p tcp --dport 8000 -s 192.168.1.0/24 -j ACCEPT
iptables -A INPUT -p tcp --dport 8000 -j DROP
```

3. **Surveiller les logs**:
```bash
# Rotation des logs
logrotate -f /etc/logrotate.d/matriarche
```

### Performance

1. **Ajuster les intervalles**:
```yaml
# config/default_config.yaml
matriarche:
  min_sleep: 300    # Plus fréquent
  max_sleep: 1800   # Moins long
```

2. **Augmenter le pool de Protos**:
```yaml
sub_matriarche:
  proto_pool_size: 25  # Au lieu de 15
```

3. **Activer PoW/PoM plus souvent**:
```python
# Dans le code
if random.random() > 0.5:  # 50% au lieu de 30%
    challenge = pow_engine.issue_challenge()
```

### Stealth

1. **Augmenter les délais aléatoires**:
```python
# Dans proto_core.py
await asyncio.sleep(random.uniform(120, 600))  # 2-10 min
```

2. **Réduire la fréquence des beacons**:
```python
beacon_interval = random.randint(1800, 3600)  # 30-60 min
```

3. **Activer obfuscation maximale**:
```python
junk_ratio = 0.4  # 40% de junk data
```

## Conclusion

Ce système est un outil puissant qui nécessite une utilisation responsable. Assurez-vous de:

- Toujours avoir le contrôle via le Kill Switch
- Surveiller les métriques en temps réel
- Limiter la portée des missions
- Nettoyer les traces après usage
- Respecter les cadres légaux et éthiques
