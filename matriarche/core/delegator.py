"""Système de délégation des missions vers Sous-Matriarches"""
import random
import time
from typing import Dict, List, Optional
from utils.crypto_utils import CryptoManager


class MissionDelegator:
    """Délégation intelligente des missions"""
    
    def __init__(self, brain):
        self.brain = brain
        self.mission_queue = []
        self.mission_history = []
        
    def add_mission(self, mission: Dict):
        """Ajoute une mission à la queue"""
        mission['queued_at'] = time.time()
        mission['mission_id'] = CryptoManager.generate_uuid()
        self.mission_queue.append(mission)
    
    def has_pending_missions(self) -> bool:
        """Vérifie s'il y a des missions en attente"""
        return len(self.mission_queue) > 0
    
    async def delegate_pending_missions(self):
        """Délègue toutes les missions en attente"""
        while self.mission_queue:
            mission = self.mission_queue.pop(0)
            await self._delegate_mission(mission)
    
    async def _delegate_mission(self, mission: Dict):
        """Délègue une mission spécifique"""
        # Décomposition de l'objectif en sous-tâches
        subtasks = self._decompose_objective(mission)
        
        # Assignment aléatoire aux Sous-Matriarches
        assignments = self._randomized_assignment(subtasks)
        
        # Envoi aux Sous-Matriarches
        for sub_id, tasks in assignments.items():
            await self._send_to_sub_matriarche(sub_id, mission, tasks)
        
        # Archivage
        self.mission_history.append({
            'mission': mission,
            'delegated_at': time.time(),
            'assignments': assignments
        })
    
    def _decompose_objective(self, mission: Dict) -> List[Dict]:
        """Décompose un objectif en sous-tâches"""
        objective = mission.get('objective', '')
        priority = mission.get('priority', 'normal')
        
        # Décomposition heuristique simple
        subtasks = []
        
        # Analyse de l'objectif
        if 'access' in objective.lower() or 'retrieve' in objective.lower():
            # Mission de type récupération
            subtasks.extend([
                {
                    'type': 'reconnaissance',
                    'description': 'Discover target system',
                    'priority': priority
                },
                {
                    'type': 'path_finding',
                    'description': 'Find path to target',
                    'priority': priority
                },
                {
                    'type': 'exploitation',
                    'description': 'Gain access to target',
                    'priority': priority
                },
                {
                    'type': 'execution',
                    'description': 'Execute objective',
                    'priority': priority
                },
                {
                    'type': 'exfiltration',
                    'description': 'Extract data if needed',
                    'priority': priority
                }
            ])
        
        elif 'scan' in objective.lower() or 'discover' in objective.lower():
            # Mission de reconnaissance
            subtasks.extend([
                {
                    'type': 'network_scan',
                    'description': 'Scan network for systems',
                    'priority': priority
                },
                {
                    'type': 'service_enumeration',
                    'description': 'Enumerate services',
                    'priority': priority
                },
                {
                    'type': 'vulnerability_assessment',
                    'description': 'Assess vulnerabilities',
                    'priority': priority
                }
            ])
        
        else:
            # Objectif générique
            subtasks.append({
                'type': 'generic',
                'description': objective,
                'priority': priority
            })
        
        # Ajout de métadonnées
        for i, task in enumerate(subtasks):
            task['task_id'] = f"{mission['mission_id']}_task_{i}"
            task['mission_id'] = mission['mission_id']
        
        return subtasks
    
    def _randomized_assignment(self, subtasks: List[Dict]) -> Dict[str, List[Dict]]:
        """Assigne les tâches de manière aléatoire aux Sous-Matriarches"""
        if not self.brain.sub_matriarches:
            return {}
        
        assignments = {sub['id']: [] for sub in self.brain.sub_matriarches}
        
        for task in subtasks:
            # Calcul des poids basé sur la charge actuelle
            weights = []
            for sub in self.brain.sub_matriarches:
                current_load = len(assignments[sub['id']])
                # Poids inversement proportionnel à la charge
                weight = 1.0 / (current_load + 1)
                weights.append(weight)
            
            # Sélection pondérée
            chosen_sub = random.choices(
                self.brain.sub_matriarches,
                weights=weights
            )[0]
            
            assignments[chosen_sub['id']].append(task)
        
        return assignments
    
    async def _send_to_sub_matriarche(self, 
                                     sub_id: str, 
                                     mission: Dict, 
                                     tasks: List[Dict]):
        """Envoie une assignation à une Sous-Matriarche"""
        # Récupération de la clé publique de la Sous-Matriarche
        sub_info = next(
            (s for s in self.brain.sub_matriarches if s['id'] == sub_id),
            None
        )
        
        if not sub_info:
            print(f"[Delegator] Sub-Matriarche {sub_id} not found")
            return
        
        # Préparation du message
        message = {
            'type': 'mission_assignment',
            'mission_id': mission['mission_id'],
            'from': self.brain.node_id,
            'to': sub_id,
            'tasks': tasks,
            'priority': mission.get('priority', 'normal'),
            'constraints': mission.get('constraints', {}),
            'timestamp': time.time(),
            'nonce': CryptoManager.generate_nonce()
        }
        
        # Chiffrement du message
        message_json = str(message).encode()
        encrypted = self.brain.crypto.encrypt_asymmetric(
            message_json,
            sub_info['public_key']
        )
        
        # Stockage du message chiffré pour récupération par la Sub
        content_id = f"mission_{sub_id}_{mission['mission_id']}"
        self.brain.storage.store(content_id, encrypted)
        
        print(f"[Delegator] Delegated {len(tasks)} tasks to {sub_id}")
    
    def get_mission_status(self, mission_id: str) -> Optional[Dict]:
        """Récupère le statut d'une mission"""
        for record in self.mission_history:
            if record['mission']['mission_id'] == mission_id:
                return {
                    'mission_id': mission_id,
                    'objective': record['mission'].get('objective'),
                    'delegated_at': record['delegated_at'],
                    'assignments': record['assignments'],
                    'status': 'delegated'
                }
        
        # Vérification dans la queue
        for mission in self.mission_queue:
            if mission['mission_id'] == mission_id:
                return {
                    'mission_id': mission_id,
                    'status': 'queued',
                    'queued_at': mission.get('queued_at')
                }
        
        return None
