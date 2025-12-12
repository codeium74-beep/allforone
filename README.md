# Système Matriarche Distribué

Architecture distribuée et furtive avec hiérarchie organique.

## Architecture

```
Matriarche (1) → Sous-Matriarches (3-5) → Proto-Agents (10-50)
                      ↑
                 Percepteurs (filtration)
```

## Structure

- `matriarche/` - Cerveau central dormant
- `sous_matriarche/` - Lieutenants semi-autonomes
- `proto_agent/` - Cellules exploratrices polymorphes
- `percepteur/` - Système immunitaire de filtration
- `pow_pom/` - Mécanismes Proof of Work/Memory
- `monitoring/` - Dashboard et métriques temps réel
- `utils/` - Utilitaires partagés
- `scripts/` - Scripts de déploiement
- `tests/` - Tests système
- `docs/` - Documentation
- `config/` - Configurations

## Caractéristiques

- **Taille**: <500MB code + <500MB data
- **Stealth**: Trafic obfusqué, actions aléatoires
- **Redondance**: Data x5 shardée
- **P2P**: Échanges directs entre Protos
- **PoW/PoM**: Allocation dynamique ressources

## Déploiement

Voir `docs/DEPLOYMENT.md` pour instructions complètes.

## Sécurité

Système à usage interne uniquement. Kill switch multi-niveaux intégré.
