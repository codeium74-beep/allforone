"""Système de planification stratégique"""
import time
from typing import Dict, List, Optional
import random


class StrategyPlanner:
    """Planification stratégique haut niveau"""
    
    def __init__(self, brain):
        self.brain = brain
        self.current_strategy = None
        self.strategy_history = []
        
    def plan_strategy(self, objective: str, intel: List[Dict]) -> Dict:
        """Planifie une stratégie basée sur l'objectif et l'intelligence"""
        print(f"[Strategy] Planning for: {objective}")
        
        # Analyse de l'objectif
        objective_type = self._classify_objective(objective)
        
        # Analyse du terrain
        terrain_analysis = self._analyze_terrain(intel)
        
        # Sélection de la stratégie
        strategy = self._select_strategy(objective_type, terrain_analysis)
        
        # Génération du plan d'action
        action_plan = self._generate_action_plan(strategy, intel)
        
        self.current_strategy = {
            'objective': objective,
            'type': objective_type,
            'strategy': strategy,
            'action_plan': action_plan,
            'created_at': time.time()
        }
        
        self.strategy_history.append(self.current_strategy)
        
        return self.current_strategy
    
    def _classify_objective(self, objective: str) -> str:
        """Classifie le type d'objectif"""
        objective_lower = objective.lower()
        
        if any(word in objective_lower for word in ['scan', 'discover', 'reconnaissance']):
            return 'reconnaissance'
        elif any(word in objective_lower for word in ['access', 'penetrate', 'breach']):
            return 'penetration'
        elif any(word in objective_lower for word in ['exfiltrate', 'extract', 'steal']):
            return 'exfiltration'
        elif any(word in objective_lower for word in ['persist', 'maintain', 'backdoor']):
            return 'persistence'
        elif any(word in objective_lower for word in ['escalate', 'privilege', 'admin']):
            return 'escalation'
        else:
            return 'generic'
    
    def _analyze_terrain(self, intel: List[Dict]) -> Dict:
        """Analyse le terrain à partir de l'intelligence"""
        systems_count = sum(len(report.get('discovered_systems', [])) for report in intel)
        paths_count = sum(len(report.get('paths', [])) for report in intel)
        vulns_count = sum(len(report.get('vulnerabilities', [])) for report in intel)
        
        return {
            'systems_discovered': systems_count,
            'paths_available': paths_count,
            'vulnerabilities_found': vulns_count,
            'terrain_complexity': self._calculate_complexity(systems_count, paths_count)
        }
    
    def _calculate_complexity(self, systems: int, paths: int) -> str:
        """Calcule la complexité du terrain"""
        if systems < 5 and paths < 3:
            return 'simple'
        elif systems < 20 and paths < 15:
            return 'moderate'
        else:
            return 'complex'
    
    def _select_strategy(self, objective_type: str, terrain: Dict) -> str:
        """Sélectionne la stratégie appropriée"""
        complexity = terrain['terrain_complexity']
        
        strategies = {
            'reconnaissance': {
                'simple': 'direct_scan',
                'moderate': 'layered_scan',
                'complex': 'distributed_recon'
            },
            'penetration': {
                'simple': 'direct_attack',
                'moderate': 'multi_vector',
                'complex': 'slow_infiltration'
            },
            'exfiltration': {
                'simple': 'direct_transfer',
                'moderate': 'staged_exfil',
                'complex': 'covert_channel'
            },
            'persistence': {
                'simple': 'single_backdoor',
                'moderate': 'multiple_methods',
                'complex': 'distributed_persistence'
            },
            'escalation': {
                'simple': 'exploit_path',
                'moderate': 'credential_theft',
                'complex': 'lateral_movement'
            }
        }
        
        return strategies.get(objective_type, {}).get(complexity, 'adaptive')
    
    def _generate_action_plan(self, strategy: str, intel: List[Dict]) -> List[Dict]:
        """Génère un plan d'action détaillé"""
        action_plans = {
            'direct_scan': [
                {'phase': 1, 'action': 'identify_targets', 'parallel': False},
                {'phase': 2, 'action': 'enumerate_services', 'parallel': True},
                {'phase': 3, 'action': 'fingerprint_systems', 'parallel': True}
            ],
            'layered_scan': [
                {'phase': 1, 'action': 'network_discovery', 'parallel': False},
                {'phase': 2, 'action': 'service_enumeration', 'parallel': True},
                {'phase': 3, 'action': 'vulnerability_scan', 'parallel': True},
                {'phase': 4, 'action': 'deep_analysis', 'parallel': False}
            ],
            'distributed_recon': [
                {'phase': 1, 'action': 'deploy_scouts', 'parallel': True},
                {'phase': 2, 'action': 'passive_collection', 'parallel': True},
                {'phase': 3, 'action': 'correlate_intelligence', 'parallel': False},
                {'phase': 4, 'action': 'targeted_probing', 'parallel': True}
            ],
            'slow_infiltration': [
                {'phase': 1, 'action': 'establish_foothold', 'parallel': False},
                {'phase': 2, 'action': 'patient_observation', 'parallel': False},
                {'phase': 3, 'action': 'trust_building', 'parallel': False},
                {'phase': 4, 'action': 'gradual_expansion', 'parallel': True},
                {'phase': 5, 'action': 'objective_execution', 'parallel': False}
            ]
        }
        
        return action_plans.get(strategy, [
            {'phase': 1, 'action': 'assess_situation', 'parallel': False},
            {'phase': 2, 'action': 'execute_objective', 'parallel': True}
        ])
    
    def adapt_strategy(self, feedback: Dict):
        """Adapte la stratégie basée sur le feedback"""
        if not self.current_strategy:
            return
        
        success_rate = feedback.get('success_rate', 0.5)
        
        if success_rate < 0.3:
            print("[Strategy] Low success rate, adapting strategy...")
            # Passage à une stratégie plus furtive
            self._escalate_stealth()
        elif success_rate > 0.8:
            print("[Strategy] High success rate, optimizing speed...")
            # Accélération si tout va bien
            self._optimize_speed()
    
    def _escalate_stealth(self):
        """Augmente la furtivité de la stratégie"""
        if self.current_strategy:
            self.current_strategy['stealth_level'] = 'high'
            self.current_strategy['delay_multiplier'] = 2.0
    
    def _optimize_speed(self):
        """Optimise pour la vitesse"""
        if self.current_strategy:
            self.current_strategy['parallelization'] = 'maximum'
            self.current_strategy['delay_multiplier'] = 0.5


class ObjectiveParser:
    """Parser d'objectifs en langage naturel"""
    
    @staticmethod
    def parse_objective(objective: str) -> Dict:
        """Parse un objectif en composants structurés"""
        components = {
            'raw': objective,
            'action': ObjectiveParser._extract_action(objective),
            'target': ObjectiveParser._extract_target(objective),
            'constraints': ObjectiveParser._extract_constraints(objective),
            'priority': ObjectiveParser._extract_priority(objective)
        }
        
        return components
    
    @staticmethod
    def _extract_action(objective: str) -> str:
        """Extrait l'action principale"""
        action_verbs = {
            'access': ['access', 'enter', 'get into'],
            'scan': ['scan', 'discover', 'find', 'identify'],
            'exfiltrate': ['exfiltrate', 'extract', 'steal', 'retrieve'],
            'modify': ['modify', 'change', 'alter', 'update'],
            'destroy': ['destroy', 'delete', 'remove', 'wipe']
        }
        
        objective_lower = objective.lower()
        
        for action, verbs in action_verbs.items():
            if any(verb in objective_lower for verb in verbs):
                return action
        
        return 'execute'
    
    @staticmethod
    def _extract_target(objective: str) -> str:
        """Extrait la cible"""
        # Recherche de patterns comme "file X", "system Y", "server Z"
        import re
        
        patterns = [
            r'file\s+([^\s]+)',
            r'system\s+([^\s]+)',
            r'server\s+([^\s]+)',
            r'on\s+([^\s]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, objective, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return 'unknown'
    
    @staticmethod
    def _extract_constraints(objective: str) -> Dict:
        """Extrait les contraintes"""
        constraints = {}
        
        if 'without detection' in objective.lower():
            constraints['stealth'] = 'required'
        
        if 'quickly' in objective.lower() or 'asap' in objective.lower():
            constraints['speed'] = 'high'
        
        if 'quietly' in objective.lower():
            constraints['noise'] = 'minimal'
        
        return constraints
    
    @staticmethod
    def _extract_priority(objective: str) -> str:
        """Extrait le niveau de priorité"""
        objective_lower = objective.lower()
        
        if any(word in objective_lower for word in ['urgent', 'critical', 'asap']):
            return 'high'
        elif any(word in objective_lower for word in ['low priority', 'when possible']):
            return 'low'
        else:
            return 'normal'
