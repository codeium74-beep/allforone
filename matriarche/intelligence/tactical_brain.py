"""
Tactical Brain - Cerveau tactique avec LLM pour analyse et planification
Utilise TinyLlama quantifié 4-bit pour minimiser l'empreinte mémoire (<1Go)
"""
import json
import time
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
import torch
import psutil

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TacticalBrain:
    """
    Cerveau tactique utilisant un LLM pour:
    - Analyser les données de reconnaissance
    - Générer des plans d'action tactiques
    - Apprendre des échecs et succès
    - Adapter les stratégies en temps réel
    """
    
    def __init__(self, config: Dict):
        self.config = config
        self.model = None
        self.tokenizer = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model_loaded = False
        self.generation_count = 0
        
        # Configuration mémoire
        self.max_memory = config.get('max_memory_gb', 0.8)  # 800MB max
        self.use_4bit = config.get('use_4bit_quantization', True)
        
        # Historique des générations
        self.generation_history = []
        self.max_history = 20
        
        # Initialisation différée (lazy loading)
        self.auto_load = config.get('auto_load', False)
        if self.auto_load:
            self._load_model()
    
    def _load_model(self):
        """Charge le modèle TinyLlama avec quantification 4-bit"""
        if self.model_loaded:
            print("[TacticalBrain] Model already loaded")
            return True
        
        try:
            print("[TacticalBrain] Loading TinyLlama-1.1B-Chat-v1.0 with 4-bit quantization...")
            
            # Vérification mémoire disponible
            available_memory = psutil.virtual_memory().available / (1024**3)
            print(f"[TacticalBrain] Available memory: {available_memory:.2f} GB")
            
            if available_memory < 0.5:
                print(f"[TacticalBrain] WARNING: Low memory ({available_memory:.2f}GB). Model loading may fail.")
                return False
            
            from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
            
            # Configuration 4-bit pour minimiser la RAM
            if self.use_4bit:
                bnb_config = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_quant_type="nf4",  # NormalFloat4
                    bnb_4bit_use_double_quant=True,  # Double quantization
                    bnb_4bit_compute_dtype=torch.float16
                )
            else:
                bnb_config = None
            
            # Chargement du tokenizer
            print("[TacticalBrain] Loading tokenizer...")
            self.tokenizer = AutoTokenizer.from_pretrained(
                "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
                trust_remote_code=True
            )
            
            # Chargement du modèle avec optimisations mémoire
            print("[TacticalBrain] Loading model...")
            self.model = AutoModelForCausalLM.from_pretrained(
                "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
                quantization_config=bnb_config if self.use_4bit else None,
                device_map="auto",
                trust_remote_code=True,
                low_cpu_mem_usage=True,  # CRITIQUE pour éviter OOM
                torch_dtype=torch.float16 if not self.use_4bit else None
            )
            
            self.model_loaded = True
            
            # Vérification mémoire post-chargement
            used_memory = (psutil.virtual_memory().total - psutil.virtual_memory().available) / (1024**3)
            print(f"[TacticalBrain] Model loaded successfully. Memory used: {used_memory:.2f} GB")
            
            return True
            
        except Exception as e:
            print(f"[TacticalBrain] Failed to load model: {e}")
            self.model_loaded = False
            return False
    
    def analyze_and_plan(self, intel_reports: List[Dict], feedback_context: str = "") -> Dict:
        """
        Analyse les rapports d'intelligence et génère un plan tactique
        
        Args:
            intel_reports: Liste de rapports des Proto-Agents
            feedback_context: Contexte des échecs récents (optionnel)
        
        Returns:
            Dict contenant: analyse, plan tactique, actions recommandées
        """
        if not self.model_loaded:
            print("[TacticalBrain] Model not loaded, attempting to load...")
            if not self._load_model():
                # Fallback vers analyse basique sans LLM
                return self._fallback_analysis(intel_reports)
        
        try:
            # Construction du prompt
            prompt = self._build_tactical_prompt(intel_reports, feedback_context)
            
            # Génération avec le LLM
            response = self._generate(prompt, max_tokens=500)
            
            # Parsing de la réponse
            plan = self._parse_llm_response(response, intel_reports)
            
            # Historique
            self._save_to_history(intel_reports, plan)
            
            return plan
            
        except Exception as e:
            print(f"[TacticalBrain] Analysis failed: {e}")
            return self._fallback_analysis(intel_reports)
    
    def _build_tactical_prompt(self, intel_reports: List[Dict], feedback_context: str) -> str:
        """Construit un prompt optimisé pour la génération de plans tactiques"""
        
        # Extraction des découvertes clés
        systems_found = []
        vulnerabilities = []
        credentials = []
        
        for report in intel_reports:
            # Systèmes découverts
            if 'knowledge' in report:
                systems_found.extend(report['knowledge'].get('systems', {}).keys())
                credentials.extend(report['knowledge'].get('credentials', []))
            
            # Vulnérabilités
            if 'discoveries' in report:
                for discovery in report['discoveries']:
                    if discovery.get('type') == 'system' and 'vulnerabilities' in discovery:
                        vulnerabilities.extend(discovery['vulnerabilities'])
        
        # Construction du prompt structuré
        prompt = f"""<|system|>
You are a tactical cybersecurity analyst. Analyze reconnaissance data and generate actionable attack plans.
</|system|>

<|user|>
RECONNAISSANCE DATA:
- Systems discovered: {len(set(systems_found))} unique hosts
- Vulnerabilities found: {len(vulnerabilities)} total
- Credentials obtained: {len(credentials)}

DETAILED FINDINGS:
"""
        
        # Ajout de détails sur les systèmes les plus intéressants
        if systems_found:
            prompt += f"\nTop discovered systems:\n"
            for ip in list(set(systems_found))[:3]:  # Top 3
                prompt += f"- {ip}\n"
        
        # Ajout des vulnérabilités critiques
        high_severity_vulns = [v for v in vulnerabilities if v.get('cvss_score', 0) >= 7.0]
        if high_severity_vulns:
            prompt += f"\nHigh-severity vulnerabilities ({len(high_severity_vulns)}):\n"
            for vuln in high_severity_vulns[:3]:  # Top 3
                prompt += f"- {vuln.get('cve_id', 'Unknown')}: {vuln.get('description', '')[:100]}\n"
        
        # Ajout du contexte de feedback si disponible
        if feedback_context:
            prompt += f"\nPREVIOUS FAILURES TO AVOID:\n{feedback_context}\n"
        
        prompt += """
TASK:
Generate a tactical plan with:
1. TARGET: Most valuable target (IP/system)
2. ACTION: Specific action to take (exploit, bruteforce, lateral_move)
3. REASONING: Why this target and action
4. PRIORITY: high/medium/low

Format your response as JSON:
{
  "target": "IP or system identifier",
  "action": "specific_action_type",
  "reasoning": "tactical justification",
  "priority": "high/medium/low",
  "estimated_success": 0.7
}
</|user|>

<|assistant|>
"""
        
        return prompt
    
    def _generate(self, prompt: str, max_tokens: int = 500) -> str:
        """Génère une réponse avec le LLM"""
        try:
            # Tokenization
            inputs = self.tokenizer(prompt, return_tensors="pt", truncation=True, max_length=1500)
            
            if self.device == "cuda":
                inputs = inputs.to("cuda")
            
            # Génération avec paramètres optimisés
            with torch.no_grad():  # Pas de gradients = économie mémoire
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=max_tokens,
                    do_sample=True,
                    temperature=0.7,
                    top_p=0.9,
                    top_k=50,
                    pad_token_id=self.tokenizer.eos_token_id
                )
            
            # Décodage
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Extraction de la partie assistant
            if "<|assistant|>" in response:
                response = response.split("<|assistant|>")[-1].strip()
            
            self.generation_count += 1
            
            return response
            
        except Exception as e:
            print(f"[TacticalBrain] Generation error: {e}")
            return "{}"
    
    def _parse_llm_response(self, response: str, intel_reports: List[Dict]) -> Dict:
        """Parse la réponse du LLM en structure de plan"""
        try:
            # Extraction JSON de la réponse
            # Le LLM peut générer du texte avant/après le JSON
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                plan = json.loads(json_str)
            else:
                # Fallback si pas de JSON valide
                plan = {
                    "target": "unknown",
                    "action": "reconnaissance",
                    "reasoning": "No valid plan generated",
                    "priority": "medium",
                    "estimated_success": 0.5
                }
            
            # Validation et enrichissement du plan
            plan = self._validate_and_enrich_plan(plan, intel_reports)
            
            return plan
            
        except json.JSONDecodeError as e:
            print(f"[TacticalBrain] JSON parsing error: {e}")
            return self._fallback_analysis(intel_reports)
        except Exception as e:
            print(f"[TacticalBrain] Response parsing error: {e}")
            return self._fallback_analysis(intel_reports)
    
    def _validate_and_enrich_plan(self, plan: Dict, intel_reports: List[Dict]) -> Dict:
        """Valide et enrichit le plan généré"""
        # Champs requis
        required_fields = ['target', 'action', 'reasoning', 'priority']
        for field in required_fields:
            if field not in plan:
                plan[field] = 'unknown' if field in ['target', 'action'] else 'Not specified'
        
        # Normalisation de la priorité
        if plan['priority'] not in ['high', 'medium', 'low']:
            plan['priority'] = 'medium'
        
        # Ajout de métadonnées
        plan['generated_at'] = time.time()
        plan['generation_count'] = self.generation_count
        plan['model_version'] = 'TinyLlama-1.1B-Chat-v1.0'
        
        # Enrichissement avec données contextuelles
        plan['context'] = {
            'reports_analyzed': len(intel_reports),
            'total_systems': self._count_systems_in_reports(intel_reports),
            'total_vulnerabilities': self._count_vulns_in_reports(intel_reports)
        }
        
        return plan
    
    def _count_systems_in_reports(self, reports: List[Dict]) -> int:
        """Compte le nombre de systèmes uniques dans les rapports"""
        systems = set()
        for report in reports:
            if 'knowledge' in report:
                systems.update(report['knowledge'].get('systems', {}).keys())
        return len(systems)
    
    def _count_vulns_in_reports(self, reports: List[Dict]) -> int:
        """Compte le nombre de vulnérabilités dans les rapports"""
        count = 0
        for report in reports:
            if 'discoveries' in report:
                for discovery in report['discoveries']:
                    count += len(discovery.get('vulnerabilities', []))
        return count
    
    def _fallback_analysis(self, intel_reports: List[Dict]) -> Dict:
        """Analyse basique sans LLM (fallback si le modèle n'est pas chargé)"""
        print("[TacticalBrain] Using fallback analysis (no LLM)")
        
        # Comptage basique
        systems = set()
        high_value_targets = []
        
        for report in intel_reports:
            if 'knowledge' in report:
                systems.update(report['knowledge'].get('systems', {}).keys())
                
                # Recherche de cibles à haute valeur
                for ip, system_info in report['knowledge'].get('systems', {}).items():
                    if system_info.get('vulnerabilities'):
                        high_value_targets.append(ip)
        
        # Sélection de cible
        target = high_value_targets[0] if high_value_targets else (list(systems)[0] if systems else "unknown")
        
        plan = {
            "target": target,
            "action": "reconnaissance" if not high_value_targets else "exploit",
            "reasoning": f"Fallback analysis: {len(systems)} systems discovered, {len(high_value_targets)} with vulnerabilities",
            "priority": "high" if high_value_targets else "medium",
            "estimated_success": 0.6 if high_value_targets else 0.3,
            "generated_at": time.time(),
            "model_version": "fallback",
            "context": {
                "reports_analyzed": len(intel_reports),
                "total_systems": len(systems),
                "fallback_mode": True
            }
        }
        
        return plan
    
    def _save_to_history(self, intel_reports: List[Dict], plan: Dict):
        """Sauvegarde dans l'historique (mémoire limitée)"""
        self.generation_history.append({
            'timestamp': time.time(),
            'reports_count': len(intel_reports),
            'plan': plan
        })
        
        # Limite la taille de l'historique
        if len(self.generation_history) > self.max_history:
            self.generation_history.pop(0)
    
    def get_statistics(self) -> Dict:
        """Retourne des statistiques sur l'utilisation du cerveau tactique"""
        return {
            'model_loaded': self.model_loaded,
            'generation_count': self.generation_count,
            'history_size': len(self.generation_history),
            'device': self.device,
            'quantization_4bit': self.use_4bit,
            'memory_used_gb': (psutil.virtual_memory().total - psutil.virtual_memory().available) / (1024**3)
        }
    
    def unload_model(self):
        """Décharge le modèle de la mémoire pour libérer des ressources"""
        if self.model_loaded:
            print("[TacticalBrain] Unloading model...")
            del self.model
            del self.tokenizer
            
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            self.model = None
            self.tokenizer = None
            self.model_loaded = False
            
            print("[TacticalBrain] Model unloaded successfully")
    
    def __del__(self):
        """Nettoyage à la destruction de l'objet"""
        if self.model_loaded:
            self.unload_model()


if __name__ == '__main__':
    # Test du TacticalBrain
    print("=== TacticalBrain Test ===")
    
    config = {
        'use_4bit_quantization': True,
        'max_memory_gb': 0.8,
        'auto_load': False  # Chargement manuel pour test
    }
    
    brain = TacticalBrain(config)
    
    # Test de chargement
    print("\n1. Testing model loading...")
    if brain._load_model():
        print("✓ Model loaded successfully")
    else:
        print("✗ Model loading failed")
    
    # Test d'analyse
    print("\n2. Testing tactical analysis...")
    
    mock_intel = [
        {
            'knowledge': {
                'systems': {
                    '192.168.1.100': {
                        'ports': [22, 80, 443],
                        'os': ['Linux']
                    }
                },
                'credentials': []
            },
            'discoveries': [
                {
                    'type': 'system',
                    'vulnerabilities': [
                        {'cve_id': 'CVE-2023-1234', 'cvss_score': 9.8, 'description': 'Critical RCE vulnerability'}
                    ]
                }
            ]
        }
    ]
    
    plan = brain.analyze_and_plan(mock_intel)
    print(f"Generated plan: {json.dumps(plan, indent=2)}")
    
    # Statistiques
    print("\n3. Statistics:")
    stats = brain.get_statistics()
    print(json.dumps(stats, indent=2))
    
    # Nettoyage
    print("\n4. Unloading model...")
    brain.unload_model()
    print("✓ Test complete")
