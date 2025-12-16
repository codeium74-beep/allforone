# 🚀 DÉMARRAGE RAPIDE - Système Matriarche

## ⚡ Installation & Lancement (5 minutes)

### 1. Installation des dépendances
```bash
cd /home/user/webapp
pip3 install -r requirements.txt
```

### 2. Démarrage du système
```bash
chmod +x scripts/*.sh
./scripts/start_all.sh
```

✅ Le système démarre automatiquement:
- 1 Matriarche
- 3 Sous-Matriarches
- 10 Proto-Agents
- API Monitoring sur http://localhost:8000

### 3. Vérification
```bash
# Status système
curl http://localhost:8000/api/status

# Agents actifs
curl http://localhost:8000/api/agents

# Découvertes
curl http://localhost:8000/api/discoveries
```

---

## 🛑 Arrêt & Réinitialisation

### Arrêt propre
```bash
./scripts/stop_all.sh
```

### Réinitialisation complète
```bash
./scripts/reset_system.sh
```

---

## 🎯 Fonctionnalités Opérationnelles

### ✅ Phase 1 - Scanning (100%)
- **Nmap Scanner**: Scan réseau complet
- **Fingerprinting**: Identification services HTTP/SSL
- **CVE Database**: Détection vulnérabilités automatique

### ✅ Phase 2 - Exploitation (100%)
- **Metasploit**: Exploitation automatique via MSF RPC
- **Bruteforce**: SSH, SMB, HTTP multi-protocoles
- **Exploit Selector**: Sélection intelligente d'exploits

### Proto-Agents autonomes
- Scanning automatique de réseaux
- Exploitation automatique de vulnérabilités
- Bruteforce automatique si exploitation échoue
- Stockage découvertes et credentials

---

## 📊 Monitoring en Temps Réel

### API Endpoints
```bash
# Status général
GET http://localhost:8000/api/status

# Métriques
GET http://localhost:8000/api/metrics

# Agents
GET http://localhost:8000/api/agents

# Découvertes
GET http://localhost:8000/api/discoveries

# Kill Switch
POST http://localhost:8000/api/killswitch/{level}
```

### WebSocket
```python
import websockets
async with websockets.connect("ws://localhost:8000/ws/metrics") as ws:
    data = await ws.recv()
    print(data)
```

---

## 🔧 Configuration

### Fichier principal: `config/system.yaml`

```yaml
system:
  environment: "production"

reconnaissance:
  nmap_timing: "T4"
  scan_timeout: 300

exploitation:
  msf_host: "127.0.0.1"
  msf_port: 55553
  msf_password: "msf"
  bruteforce_delay: 0.5
```

---

## 🧪 Tests

### Lancer tous les tests
```bash
pytest tests/ -v
```

### Tests individuels
```bash
pytest tests/test_nmap_scanner.py -v
pytest tests/test_fingerprint.py -v
pytest tests/test_cve_database.py -v
```

---

## 🔐 Kill Switch

### Niveaux disponibles

**Niveau 1 - Pause**: Arrêt temporaire réversible
```bash
curl -X POST http://localhost:8000/api/killswitch/1
```

**Niveau 2 - Retrait**: Retrait des systèmes avec nettoyage léger
```bash
curl -X POST http://localhost:8000/api/killswitch/2
```

**Niveau 3 - Effacement**: Suppression données + nettoyage complet
```bash
curl -X POST http://localhost:8000/api/killswitch/3
```

**Niveau 4 - Autodestruction**: Effacement sécurisé IRRÉVERSIBLE
```bash
curl -X POST http://localhost:8000/api/killswitch/4
```

---

## 📦 Pré-requis Système

### Obligatoire
- Python 3.11+
- Nmap (`sudo apt-get install nmap`)
- Dépendances Python (`pip3 install -r requirements.txt`)

### Optionnel (pour fonctionnalités avancées)
- Metasploit Framework (pour exploitation MSF)
  ```bash
  curl https://raw.githubusercontent.com/rapid7/metasploit-omnibus/master/config/templates/metasploit-framework-wrappers/msfupdate.erb > msfinstall
  chmod +x msfinstall
  ./msfinstall
  
  # Démarrer msfrpcd
  msfrpcd -P msf -S -a 127.0.0.1
  ```

---

## 🐛 Dépannage

### Problème: Système ne démarre pas
```bash
# Vérifier processus existants
ps aux | grep -E "(matriarche|proto_agent|sous_matriarche)"

# Tuer processus zombies
pkill -f "matriarche"
pkill -f "proto_agent"
pkill -f "sous_matriarche"

# Réinitialiser et redémarrer
./scripts/reset_system.sh
./scripts/start_all.sh
```

### Problème: API ne répond pas
```bash
# Vérifier logs
tail -f logs/monitoring.log

# Redémarrer API uniquement
pkill -f "uvicorn"
cd monitoring/api
uvicorn main:app --host 0.0.0.0 --port 8000 &
```

### Problème: Agents n'explorent pas
```bash
# Vérifier logs agents
tail -f logs/proto_*.log

# Vérifier CVE database
ls -lh data/cve/cve_database.json

# Télécharger CVE si manquant
python3 utils/cve_database.py download 2023
```

---

## 📈 Monitoring Logs

### Logs système
```bash
# Matriarche
tail -f logs/matriarche.log

# Proto-Agents
tail -f logs/proto_*.log

# Monitoring
tail -f logs/monitoring.log

# Tous les logs
tail -f logs/*.log
```

---

## 🎯 Utilisation Typique

### Scénario 1: Scan et exploitation automatique
```bash
# 1. Démarrer système
./scripts/start_all.sh

# 2. Attendre découvertes (1-5 minutes)
watch -n 5 'curl -s http://localhost:8000/api/discoveries | jq'

# 3. Vérifier credentials trouvés
curl http://localhost:8000/api/credentials

# 4. Arrêter proprement
./scripts/stop_all.sh
```

### Scénario 2: Mission spécifique
```python
import requests

# Assigner mission à Matriarche
mission = {
    "objective": "Access file /etc/passwd on system 192.168.1.100",
    "priority": "high",
    "constraints": {
        "stealth": "high",
        "max_time": 3600
    }
}

response = requests.post(
    "http://localhost:8000/api/missions",
    json=mission
)

print(response.json())
```

---

## 📞 Support

### Logs à vérifier en priorité
1. `logs/matriarche.log` - Activité Matriarche
2. `logs/proto_*.log` - Activité Proto-Agents
3. `/tmp/matriarche/*.pid` - PIDs des processus

### Commandes de diagnostic
```bash
# Status processus
ps aux | grep -E "(matriarche|proto)"

# Status API
curl http://localhost:8000/api/status

# Logs en temps réel
tail -f logs/*.log
```

---

**Version**: 1.0.0  
**Date**: 2025-12-16  
**Status**: ✅ Phases 1-2 opérationnelles (Scanning + Exploitation)

---

## 🎉 Félicitations !

Vous avez maintenant un système de reconnaissance et d'exploitation autonome fonctionnel avec:
- ✅ Scanning réseau Nmap
- ✅ Fingerprinting HTTP/SSL
- ✅ Détection CVE automatique
- ✅ Exploitation Metasploit
- ✅ Bruteforce multi-protocoles
- ✅ Agents autonomes intelligents
- ✅ Monitoring temps réel
- ✅ Kill Switch multi-niveaux

Pour aller plus loin, consultez `IMPLEMENTATION_STATUS.md` pour voir les phases suivantes.
