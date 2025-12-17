# 🧠 Guide Complet du Tactical Brain

## Vue d'ensemble

Le **TacticalBrain** est le cerveau stratégique du système Matriarche. Il utilise un LLM (TinyLlama-1.1B) quantifié en 4-bit pour générer des plans tactiques intelligents basés sur les données de reconnaissance.

---

## Architecture

### Composants

```
┌─────────────────────────────────────────┐
│         TacticalBrain (LLM)             │
│  ┌──────────────────────────────────┐   │
│  │  TinyLlama-1.1B-Chat (4-bit)    │   │
│  │  Mémoire: ~800MB                │   │
│  └──────────────────────────────────┘   │
│              ▼                           │
│  ┌──────────────────────────────────┐   │
│  │    Analyse Intel Reports         │   │
│  └──────────────────────────────────┘   │
│              ▼                           │
│  ┌──────────────────────────────────┐   │
│  │  Génération Plan Tactique        │   │
│  │  (Target, Action, Reasoning)     │   │
│  └──────────────────────────────────┘   │
└─────────────────────────────────────────┘
         ▼
┌─────────────────────────────────────────┐
│         FeedbackLoop                    │
│  ┌──────────────────────────────────┐   │
│  │  Historique Succès/Échecs        │   │
│  │  Patterns de Failure             │   │
│  │  Recommandations                 │   │
│  └──────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

---

## Utilisation

### Initialisation

```python
from matriarche.intelligence.tactical_brain import TacticalBrain

# Configuration
config = {
    'use_4bit_quantization': True,  # Quantification 4-bit pour économie RAM
    'max_memory_gb': 0.8,            # Limite mémoire
    'auto_load': False               # Chargement manuel (recommandé)
}

# Création
brain = TacticalBrain(config)

# Chargement du modèle
if brain._load_model():
    print("✓ Modèle chargé avec succès")
```

### Génération de Plans Tactiques

```python
# Données de reconnaissance (exemple)
intel_reports = [
    {
        'knowledge': {
            'systems': {
                '192.168.1.100': {
                    'ports': [22, 80, 443],
                    'os': ['Linux'],
                    'hostname': 'webserver01'
                }
            },
            'credentials': []
        },
        'discoveries': [
            {
                'type': 'system',
                'vulnerabilities': [
                    {
                        'cve_id': 'CVE-2023-1234',
                        'cvss_score': 9.8,
                        'description': 'Critical RCE vulnerability in Apache'
                    }
                ]
            }
        ]
    }
]

# Génération du plan
plan = brain.analyze_and_plan(intel_reports, feedback_context="")

# Résultat
print(f"Target: {plan['target']}")
print(f"Action: {plan['action']}")
print(f"Reasoning: {plan['reasoning']}")
print(f"Priority: {plan['priority']}")
print(f"Estimated Success: {plan['estimated_success']}")
```

### Résultat Exemple

```json
{
  "target": "192.168.1.100",
  "action": "exploit",
  "reasoning": "Target has critical RCE vulnerability (CVE-2023-1234) with CVSS 9.8. Apache service detected on port 80/443. High probability of successful exploitation.",
  "priority": "high",
  "estimated_success": 0.85,
  "generated_at": 1703001234.56,
  "model_version": "TinyLlama-1.1B-Chat-v1.0",
  "context": {
    "reports_analyzed": 1,
    "total_systems": 1,
    "total_vulnerabilities": 1
  }
}
```

---

## FeedbackLoop

### Enregistrement de Résultats

```python
from matriarche.intelligence.feedback_loop import FeedbackLoop

feedback = FeedbackLoop(storage_path='/tmp/matriarche_feedback')

# Enregistrement d'un succès
feedback.record_operation(
    plan={'action': 'exploit', 'target': '192.168.1.100'},
    success=True,
    result={'output': 'Shell obtained', 'session_id': 123}
)

# Enregistrement d'un échec
feedback.record_operation(
    plan={'action': 'exploit', 'target': '192.168.1.101'},
    success=False,
    result={'error': 'Target patched against exploit'}
)
```

### Contexte de Feedback

```python
# Génération de contexte pour le LLM
context = feedback.get_feedback_context(max_failures=5)

# Utilisation dans génération de plan
plan = brain.analyze_and_plan(intel_reports, feedback_context=context)
```

### Recommandations

```python
# Évaluation d'un plan proposé
recommendation = feedback.get_recommendation(proposed_plan)

if not recommendation['recommended']:
    print(f"⚠️  Plan non recommandé: {recommendation['reason']}")
    
    if recommendation.get('alternative_suggested'):
        alt = recommendation['alternative']
        print(f"Alternative suggérée: {alt['action']} - {alt['reason']}")
```

---

## Intégration avec MatriarchBrain

### Cycle de Réveil

Le TacticalBrain est automatiquement appelé lors des cycles de réveil de la Matriarche:

```python
# Dans MatriarchBrain._wake_cycle()

# Phase 2b: Génération de plan tactique avec LLM
if self.tactical_brain and len(intel) > 0:
    print(f"[{self.node_id}] Generating tactical plan with LLM...")
    tactical_plan = self._generate_tactical_plan(intel)
    
    if tactical_plan:
        self._process_tactical_plan(tactical_plan)
```

### Rapport de Résultat

```python
# Après exécution d'une mission
matriarche.report_mission_result(
    mission_id='mission_123',
    success=True,
    result={'output': 'Objective achieved'}
)
```

---

## Optimisations Mémoire

### Quantification 4-bit

Le modèle utilise la quantification NF4 (NormalFloat4) pour réduire l'empreinte mémoire:

```python
from transformers import BitsAndBytesConfig

bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_use_double_quant=True,
    bnb_4bit_compute_dtype=torch.float16
)
```

**Gains:**
- Modèle original: ~4.4 GB
- Modèle quantifié: ~800 MB
- Perte de qualité: <5%

### Lazy Loading

Le modèle n'est chargé qu'à la demande:

```python
config = {
    'auto_load': False  # Pas de chargement automatique
}

brain = TacticalBrain(config)

# Chargement manuel quand nécessaire
if needed:
    brain._load_model()

# Déchargement après utilisation
brain.unload_model()
```

### Économie Mémoire

```python
# Pas de gradients (mode inférence uniquement)
with torch.no_grad():
    outputs = model.generate(...)

# Nettoyage cache CUDA
if torch.cuda.is_available():
    torch.cuda.empty_cache()
```

---

## Paramètres de Génération

### Configuration

```python
# Dans _generate()
outputs = model.generate(
    **inputs,
    max_new_tokens=500,           # Longueur max de réponse
    do_sample=True,               # Échantillonnage stochastique
    temperature=0.7,              # Contrôle créativité (0.1-1.0)
    top_p=0.9,                    # Nucleus sampling
    top_k=50,                     # Top-K sampling
    pad_token_id=tokenizer.eos_token_id
)
```

### Tuning

- **temperature**: 
  - 0.1-0.3: Réponses déterministes
  - 0.5-0.7: Équilibré (recommandé)
  - 0.8-1.0: Créatif/imprévisible

- **top_p**: Probabilité cumulative
  - 0.9: Recommandé
  - 1.0: Aucun filtrage

- **top_k**: Nombre de tokens considérés
  - 50: Recommandé
  - 0: Désactivé

---

## Prompt Engineering

### Structure du Prompt

```
<|system|>
You are a tactical cybersecurity analyst.
</|system|>

<|user|>
RECONNAISSANCE DATA:
- Systems discovered: X
- Vulnerabilities found: Y
- Credentials obtained: Z

DETAILED FINDINGS:
[...]

PREVIOUS FAILURES TO AVOID:
[...]

TASK:
Generate a tactical plan with:
1. TARGET
2. ACTION
3. REASONING
4. PRIORITY

Format: JSON
</|user|>

<|assistant|>
[Réponse du modèle]
```

### Optimisations

1. **Concision**: Prompt limité à 1500 tokens
2. **Structure**: Format JSON explicite
3. **Contexte**: Échecs récents inclus
4. **Priorités**: Top 3 systèmes/vulns seulement

---

## Statistiques & Monitoring

### Récupération des Stats

```python
stats = brain.get_statistics()

print(f"Model loaded: {stats['model_loaded']}")
print(f"Generations: {stats['generation_count']}")
print(f"Memory used: {stats['memory_used_gb']:.2f} GB")
print(f"Device: {stats['device']}")
```

### Historique

```python
# Historique des générations (limité aux 20 dernières)
for entry in brain.generation_history[-5:]:
    print(f"Timestamp: {entry['timestamp']}")
    print(f"Reports: {entry['reports_count']}")
    print(f"Plan: {entry['plan']['action']} on {entry['plan']['target']}")
```

---

## Dépannage

### Problèmes Communs

1. **OutOfMemoryError**
   - Réduire `max_new_tokens`
   - Vérifier `low_cpu_mem_usage=True`
   - Augmenter la RAM disponible

2. **Slow Generation**
   - Normal pour CPU (30-60s par plan)
   - Utiliser GPU si disponible
   - Réduire la longueur du prompt

3. **Poor Quality Plans**
   - Ajuster `temperature` (0.5-0.7)
   - Améliorer le prompt
   - Fournir plus de contexte

### Debug Mode

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Active les logs détaillés
brain = TacticalBrain(config)
plan = brain.analyze_and_plan(intel, feedback_context)
```

---

## Exemples Avancés

### Fine-tuning (LoRA)

```python
from peft import PeftModel

# Chargement du modèle de base
base_model = AutoModelForCausalLM.from_pretrained(...)

# Chargement de l'adaptateur LoRA
model = PeftModel.from_pretrained(base_model, "./lora_adapters")

# Utilisation dans TacticalBrain
brain.model = model
```

### Plans Multi-Étapes

```python
# Plan initial
plan = brain.analyze_and_plan(intel_initial)

# Exécution phase 1
result_phase1 = execute_plan(plan)

# Génération phase 2 basée sur résultats
intel_phase2 = collect_new_intel()
plan_phase2 = brain.analyze_and_plan(intel_phase2, 
                                     feedback_context=result_phase1)
```

---

## Performance

### Benchmarks (CPU Intel i7)

- **Chargement modèle**: 5-10s
- **Génération plan**: 30-60s
- **Mémoire utilisée**: ~800MB
- **Précision**: 85-90% vs humain

### Optimisations Futures

1. Quantification INT8 (plus rapide)
2. Distillation du modèle
3. Caching des plans similaires
4. Fine-tuning spécialisé

---

## Références

- [TinyLlama GitHub](https://github.com/jzhang38/TinyLlama)
- [Transformers Documentation](https://huggingface.co/docs/transformers)
- [BitsAndBytes](https://github.com/TimDettmers/bitsandbytes)
- [PEFT (LoRA)](https://github.com/huggingface/peft)

---

**Auteur**: AllForOne Matriarche System  
**Version**: 2.0.0  
**Date**: 2025-12-17
