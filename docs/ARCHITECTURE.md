# Architecture du Système Matriarche

## Vue d'Ensemble

Le système est basé sur une hiérarchie organique distribuée avec 4 niveaux:

```
Matriarche (1)
    ↓
Percepteurs (filtration)
    ↓
Sous-Matriarches (3-5)
    ↓
Proto-Agents (10-50)
```

## Composants Principaux

### 1. Matriarche

**Rôle**: Cerveau central dormant

**Caractéristiques**:
- Réveils aléatoires (10min-6h)
- Collecte passive d'intelligence
- Orchestration des mutations
- Délégation des missions

**Fichiers**:
- `matriarche/core/brain.py`: Orchestrateur principal
- `matriarche/core/timer.py`: Gestion des réveils
- `matriarche/core/delegator.py`: Délégation missions
- `matriarche/core/collector.py`: Collecte intelligence
- `matriarche/core/mutator.py`: Évolution génétique

### 2. Sous-Matriarches

**Rôle**: Lieutenants semi-autonomes

**Caractéristiques**:
- Gestion d'un pool de 10-20 Proto-Agents
- Relais bidirectionnel d'informations
- Rapports périodiques à la Matriarche
- Survie temporaire sans Matriarche

**Fichiers**:
- `sous_matriarche/sub_brain.py`: Gestionnaire principal

### 3. Proto-Agents

**Rôle**: Cellules exploratrices polymorphes

**Caractéristiques**:
- Exploration autonome
- Échanges P2P avec pairs
- Polymorphisme du code
- Accumulation de connaissances
- Migration entre systèmes

**Fichiers**:
- `proto_agent/proto_core.py`: Core agent
- `proto_agent/polymorphic.py`: Moteur polymorphique

### 4. Percepteurs

**Rôle**: Système immunitaire

**Caractéristiques**:
- Filtration des communications
- Validation cryptographique
- Protection de la Matriarche
- Détection d'anomalies

**Fichiers**:
- `percepteur/perceptor_core.py`: Core percepteur

## Mécanismes Clés

### Proof of Work (PoW)

**Objectif**: Allocation CPU/GPU

**Fonctionnement**:
1. Matriarche émet un challenge aléatoire
2. 30-50% des nœuds sélectionnés
3. Mining parallèle (SHA-256)
4. Premier à résoudre gagne la récompense
5. Allocation dynamique via API Proxmox

**Récompenses**:
- +2-4 CPU cores
- Durée: 1-2 heures
- Boost priorité

**Fichiers**:
- `pow_pom/proof_of_work.py`

### Proof of Memory (PoM)

**Objectif**: Allocation stockage

**Fonctionnement**:
1. Génération d'un shard (5MB)
2. Distribution aux participants
3. Vérification par échantillonnage
4. Validation par hash
5. Allocation stockage au gagnant

**Récompenses**:
- +50-100MB stockage
- Durée: 2-4 heures
- Boost bande passante

**Fichiers**:
- `pow_pom/proof_of_memory.py`

### Communication P2P

**Mécanisme**:
- Découverte via mDNS/Zeroconf
- Beacons multicast périodiques
- Échanges asymétriques (expérience)
- Obfuscation du trafic

**Protocoles**:
- UDP multicast (port 5353)
- TCP pour transferts
- Chiffrement symétrique/asymétrique

### Polymorphisme

**Techniques**:
- Renommage de variables
- Réorganisation du code
- Insertion de code mort
- Obfuscation de strings
- Substitution d'instructions

**Générations**:
- Parent → Mutation → Enfant
- Algorithme génétique
- Taux de mutation: 15%
- Croisement entre techniques réussies

## Stockage Distribué

### Sharding

- Taille shard: 256KB
- Réplication: 5x par défaut
- Compression: LZ4/Zstandard
- Déduplication au niveau blocs

### Structure

```
/storage/
  /data/        # Shards distribués
  /index/       # Index de localisation
  /metadata/    # Métadonnées
```

### Redondance

- Data x5 shardée
- Vérification d'intégrité
- Réparation automatique
- Cleanup périodique

## Kill Switch

### Niveaux

**Niveau 1 - Pause Soft**:
- Pause temporaire (30min)
- Connexions maintenues
- Aucun nettoyage
- Reprise automatique

**Niveau 2 - Retreat Clean**:
- Retrait progressif (10min)
- Nettoyage des traces
- Suppression backdoors
- Retrait complet

**Niveau 3 - Emergency Stop**:
- Arrêt immédiat
- Fermeture connexions
- Isolation Matriarche
- Snapshot d'urgence

**Niveau 4 - Self-Destruct**:
- Effacement traces
- Suppression agents
- Wipe stockage distribué
- Reset VMs compromises
- Termination Matriarche

### Déclencheurs

- Détections élevées (>5/min)
- Systèmes compromis (>25)
- Accès VM monitoring
- Connexion externe détectée

### Dead Man's Switch

- Timeout: 30 secondes
- Heartbeat requis
- Activation niveau 3 si timeout

## Monitoring

### Métriques Collectées

**Système**:
- CPU (global + par core)
- RAM (usage + disponible)
- Disque (usage + I/O)
- Réseau (bande passante + connexions)

**Hiérarchie**:
- État Matriarche
- Sous-Matriarches actives
- Proto-Agents (statut)
- Percepteurs (alertes)

**Missions**:
- Actives / Complétées
- Durée moyenne
- Taux de succès
- Progression

### API REST

- GET `/api/status`: Status global
- GET `/api/metrics/system`: Métriques système
- GET `/api/hierarchy/summary`: Résumé hiérarchie
- POST `/api/missions`: Créer mission
- POST `/api/killswitch/activate`: Activer KS

### WebSocket

- Stream temps réel
- Port: 8000
- Endpoint: `/ws/live`
- Format: JSON

## Flux de Données

### Mission Standard

1. **Réception**: Matriarche reçoit mission (avec token)
2. **Décomposition**: Objectif → Sous-tâches
3. **Délégation**: Assignment aux Sous-Matriarches
4. **Distribution**: Subs → Proto-Agents
5. **Exécution**: Protos explorent/échangent
6. **Collecte**: Découvertes remontent via Percepteurs
7. **Analyse**: Matriarche analyse lors du réveil
8. **Mutation**: Génération nouvelles techniques
9. **Distribution**: Nouveaux payloads → Protos

### Échange P2P

1. **Beacon**: Proto broadcast sa présence
2. **Découverte**: Autre Proto écoute
3. **Décision**: Engagement probabiliste
4. **Connexion**: Établissement canal
5. **Échange**: Connaissances + Scripts
6. **Intégration**: Merge dans cache local
7. **Log**: Enregistrement rencontre

## Sécurité

### Authentification

- Token maître (configurable)
- Hash SHA-256 pour vérification
- Signatures numériques (RSA 2048)
- Clés publiques/privées par nœud

### Chiffrement

- Symétrique: Fernet (AES-128)
- Asymétrique: RSA-2048 + OAEP
- Hash: SHA-256, SHA-512, Blake2b
- Nonces: 32 bytes aléatoires

### Obfuscation

- Trafic fragmenté (512B-4KB)
- Junk data (20%)
- Délais aléatoires
- Rotation IP

## Limites et Contraintes

### Taille

- Code total: <500MB
- Data totale: <500MB (sans réplication)
- Taille Proto: <10MB
- Payload max: 1MB

### Performance

- CPU max par VM: 8 cores
- RAM max par VM: 16GB
- Stockage max par VM: 100GB
- Connexions max: 1000

### Timing

- Wake Matriarche: 10min-6h
- Rapport Sub: 30min
- Beacon Proto: 5-30min
- PoW timeout: 60s
- PoM timeout: 5min

## Évolutivité

### Scaling Horizontal

- Ajout Sous-Matriarches: Linéaire
- Ajout Proto-Agents: O(n log n)
- Ajout Percepteurs: Zones réseau

### Scaling Vertical

- CPU: Via PoW
- RAM: Direct allocation
- Stockage: Via PoM

## Maintenance

### Nettoyage

- Logs: 24h max
- Shards: 1h max
- Métriques: 1000 entrées
- Allocations expirées: Auto

### Réparation

- Intégrité shards: Automatique
- Proto mort: Respawn par Sub
- Sub morte: Migration Protos
- Matriarche morte: Subs autonomes temporairement
