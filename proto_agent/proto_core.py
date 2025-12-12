"""Core du Proto-Agent - Agent exploratoire autonome"""
import asyncio
import random
import time
import sys
from pathlib import Path
from typing import Dict, List, Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.crypto_utils import CryptoManager
from utils.network_utils import MulticastBeacon
from proto_agent.polymorphic import PolymorphicEngine


class ProtoAgent:
    """Agent exploratoire léger et polymorphe"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.node_id = config.get('node_id', f'proto_{int(time.time())}')
        self.sub_matriarche_id = config.get('sub_matriarche_id')
        
        # Crypto basique
        self.crypto = CryptoManager()
        
        # Polymorphisme
        self.polymorph = PolymorphicEngine()
        
        # Connaissances accumulées
        self.knowledge = {}
        self.scripts = []
        self.current_location = config.get('initial_location', 'unknown')
        self.travel_history = [self.current_location]
        self.generation = 0
        
        # P2P
        self.beacon = MulticastBeacon(self.node_id, 'proto_agent')
        self.encounter_log = []
        self.beacon_interval = random.randint(300, 1800)  # 5-30 min
        
        # État
        self.status = 'idle'
        self.current_task = None
        self.discoveries = []
        
        self.running = False
    
    async def start(self):
        """Démarre le cycle de vie du Proto"""
        self.running = True
        print(f"[{self.node_id}] Proto-Agent starting at {self.current_location}")
        
        # Boucles parallèles
        await asyncio.gather(
            self._exploration_loop(),
            self._p2p_encounter_loop(),
            self._beacon_loop(),
            self._task_execution_loop()
        )
    
    async def _exploration_loop(self):
        """Boucle d'exploration autonome"""
        while self.running:
            try:
                if self.status == 'idle':
                    await self._explore()
                
                # Pause aléatoire entre explorations
                await asyncio.sleep(random.uniform(60, 300))
                
            except Exception as e:
                print(f"[{self.node_id}] Error in exploration: {e}")
                await asyncio.sleep(120)
    
    async def _p2p_encounter_loop(self):
        """Boucle d'écoute pour rencontres P2P"""
        while self.running:
            try:
                # Écoute des beacons d'autres Protos
                discovered = self.beacon.listen_for_beacons(timeout=10.0)
                
                for peer_beacon in discovered:
                    if self._should_engage(peer_beacon):
                        await self._encounter_peer(peer_beacon)
                
                await asyncio.sleep(random.uniform(30, 120))
                
            except Exception as e:
                print(f"[{self.node_id}] Error in P2P: {e}")
                await asyncio.sleep(180)
    
    async def _beacon_loop(self):
        """Émission périodique de beacons"""
        while self.running:
            try:
                # Broadcast présence
                beacon_data = self._create_beacon()
                # Note: beacon.broadcast_presence() serait bloquant, on simule
                
                await asyncio.sleep(self.beacon_interval * random.uniform(0.7, 1.3))
                
            except Exception as e:
                print(f"[{self.node_id}] Error in beacon: {e}")
                await asyncio.sleep(300)
    
    async def _task_execution_loop(self):
        """Exécution des tâches assignées"""
        while self.running:
            try:
                if self.status == 'working' and self.current_task:
                    await self._execute_task(self.current_task)
                
                await asyncio.sleep(30)
                
            except Exception as e:
                print(f"[{self.node_id}] Error in task execution: {e}")
                self.status = 'idle'
                await asyncio.sleep(60)
    
    async def _explore(self):
        """Exploration autonome de l'environnement"""
        print(f"[{self.node_id}] Exploring from {self.current_location}")
        
        # Scan environnement local
        nearby_systems = await self._discover_nearby()
        
        if nearby_systems:
            # Sélection cible
            target = self._select_target(nearby_systems)
            
            # Tentative d'accès
            if await self._attempt_access(target):
                # Migration réussie
                await self._migrate_to(target)
                await self._gather_local_intel(target)
    
    async def _discover_nearby(self) -> List[Dict]:
        """Découvre les systèmes à proximité"""
        # Simulation de découverte
        nearby = []
        
        # Dans un vrai système: scan réseau, énumération, etc.
        # Ici: simulation simple
        for i in range(random.randint(1, 5)):
            system = {
                'id': f'system_{random.randint(1000, 9999)}',
                'ip': f'192.168.{random.randint(1, 255)}.{random.randint(1, 255)}',
                'reachable': random.random() > 0.3,
                'services': random.randint(1, 10)
            }
            nearby.append(system)
        
        return nearby
    
    def _select_target(self, nearby_systems: List[Dict]) -> Optional[Dict]:
        """Sélectionne une cible pour exploration"""
        # Filtre systèmes accessibles
        reachable = [s for s in nearby_systems if s.get('reachable')]
        
        if not reachable:
            return None
        
        # Sélection pondérée (plus de services = plus intéressant)
        weights = [s.get('services', 1) for s in reachable]
        target = random.choices(reachable, weights=weights)[0]
        
        return target
    
    async def _attempt_access(self, target: Dict) -> bool:
        """Tente d'accéder à un système"""
        print(f"[{self.node_id}] Attempting access to {target['id']}")
        
        # Simulation d'exploitation
        # Dans un vrai système: test vulns, brute force, etc.
        success_rate = 0.3  # 30% base
        
        # Augmente avec l'expérience
        success_rate += min(len(self.travel_history) * 0.05, 0.4)
        
        success = random.random() < success_rate
        
        if success:
            print(f"[{self.node_id}] Successfully accessed {target['id']}")
            
            # Enregistrement découverte
            self.discoveries.append({
                'type': 'successful_access',
                'target': target['id'],
                'timestamp': time.time(),
                'method': 'simulated'
            })
        else:
            print(f"[{self.node_id}] Failed to access {target['id']}")
        
        return success
    
    async def _migrate_to(self, target: Dict):
        """Migre vers un nouveau système"""
        print(f"[{self.node_id}] Migrating to {target['id']}")
        
        old_location = self.current_location
        self.current_location = target['id']
        self.travel_history.append(target['id'])
        
        # Enregistrement du chemin
        self.knowledge[f"path_{old_location}_{target['id']}"] = {
            'from': old_location,
            'to': target['id'],
            'timestamp': time.time(),
            'method': 'simulated'
        }
    
    async def _gather_local_intel(self, target: Dict):
        """Collecte des informations sur le système local"""
        print(f"[{self.node_id}] Gathering intel on {target['id']}")
        
        # Simulation collecte
        intel = {
            'type': 'system',
            'id': target['id'],
            'ip': target.get('ip'),
            'discovered_at': time.time(),
            'discoverer': self.node_id
        }
        
        self.knowledge[target['id']] = intel
        self.discoveries.append(intel)
    
    def _should_engage(self, peer_beacon: Dict) -> bool:
        """Décide s'il faut s'engager avec un pair"""
        peer_id = peer_beacon.get('node_id')
        
        # Évite de re-rencontrer trop vite
        recent = [e for e in self.encounter_log 
                 if time.time() - e['timestamp'] < 3600]  # 1h
        
        if peer_id in [e['peer_id'] for e in recent]:
            return False
        
        # Plus le pair a voyagé, plus attractif
        travel_count = peer_beacon.get('travel_count', 0)
        engagement_prob = 0.3 + min(travel_count * 0.05, 0.5)
        
        return random.random() < engagement_prob
    
    async def _encounter_peer(self, peer_beacon: Dict):
        """Rencontre avec un pair Proto"""
        peer_id = peer_beacon.get('node_id')
        print(f"[{self.node_id}] Encountering peer {peer_id}")
        
        # Échange de connaissances
        await self._exchange_knowledge(peer_beacon)
        
        # Échange de scripts
        await self._exchange_scripts(peer_beacon)
        
        # Log de la rencontre
        self.encounter_log.append({
            'peer_id': peer_id,
            'timestamp': time.time(),
            'location': peer_beacon.get('location')
        })
    
    async def _exchange_knowledge(self, peer_beacon: Dict):
        """Échange de connaissances avec un pair"""
        # Simulation d'échange
        print(f"[{self.node_id}] Exchanging knowledge with peer")
        
        # Dans un vrai système: communication réseau réelle
        # Ici: simulation d'échange
        
        # Calcul valeur respective
        my_value = len(self.travel_history) * len(self.knowledge)
        peer_value = peer_beacon.get('travel_count', 0) * 10  # Estimation
        
        # Échange asymétrique
        if my_value < peer_value:
            # Recevoir plus
            print(f"[{self.node_id}] Receiving more knowledge (less experienced)")
        else:
            # Donner plus
            print(f"[{self.node_id}] Sharing more knowledge (more experienced)")
    
    async def _exchange_scripts(self, peer_beacon: Dict):
        """Échange de scripts/payloads avec un pair"""
        print(f"[{self.node_id}] Exchanging scripts with peer")
        
        # Simulation
        # Dans un vrai système: partage de code réel
    
    def _create_beacon(self) -> Dict:
        """Crée un beacon pour broadcast"""
        return {
            'node_id': self.node_id,
            'node_type': 'proto_agent',
            'location': self.current_location,
            'travel_count': len(self.travel_history),
            'timestamp': time.time()
        }
    
    def assign_task(self, task: Dict):
        """Assigne une tâche au Proto"""
        print(f"[{self.node_id}] Task assigned: {task.get('type')}")
        self.current_task = task
        self.status = 'working'
    
    async def _execute_task(self, task: Dict):
        """Exécute une tâche assignée"""
        task_type = task.get('type')
        
        print(f"[{self.node_id}] Executing task: {task_type}")
        
        # Simulation d'exécution selon le type
        if task_type == 'reconnaissance':
            await self._task_reconnaissance(task)
        elif task_type == 'path_finding':
            await self._task_path_finding(task)
        elif task_type == 'exploitation':
            await self._task_exploitation(task)
        else:
            await self._task_generic(task)
        
        # Tâche terminée
        self.status = 'idle'
        self.current_task = None
    
    async def _task_reconnaissance(self, task: Dict):
        """Tâche de reconnaissance"""
        print(f"[{self.node_id}] Performing reconnaissance")
        
        # Découverte de systèmes
        systems = await self._discover_nearby()
        
        for system in systems:
            self.discoveries.append({
                'type': 'system',
                'data': system,
                'task_id': task.get('task_id'),
                'timestamp': time.time()
            })
        
        await asyncio.sleep(random.uniform(5, 15))
    
    async def _task_path_finding(self, task: Dict):
        """Recherche de chemins"""
        print(f"[{self.node_id}] Finding paths")
        
        # Analyse des chemins possibles
        await asyncio.sleep(random.uniform(10, 30))
    
    async def _task_exploitation(self, task: Dict):
        """Exploitation de vulnérabilités"""
        print(f"[{self.node_id}] Attempting exploitation")
        
        # Tentative d'exploitation
        success = random.random() < 0.4
        
        if success:
            self.discoveries.append({
                'type': 'successful_exploit',
                'task_id': task.get('task_id'),
                'timestamp': time.time()
            })
        
        await asyncio.sleep(random.uniform(15, 45))
    
    async def _task_generic(self, task: Dict):
        """Tâche générique"""
        print(f"[{self.node_id}] Executing generic task")
        await asyncio.sleep(random.uniform(10, 30))
    
    def receive_mutation(self, mutation: Dict):
        """Reçoit une mutation de la hiérarchie"""
        print(f"[{self.node_id}] Received mutation")
        
        self.scripts.append(mutation)
        self.generation += 1
        
        # Application de la mutation
        if random.random() < 0.1:  # 10% chance de polymorphisme
            self.polymorph.mutate_self()
    
    async def shutdown(self):
        """Arrêt propre"""
        print(f"[{self.node_id}] Shutting down")
        self.running = False


async def main():
    """Point d'entrée"""
    import sys
    
    proto_id = sys.argv[1] if len(sys.argv) > 1 else f'proto_{int(time.time())}'
    
    config = {
        'node_id': proto_id,
        'sub_matriarche_id': 'sub_001',
        'initial_location': 'start_zone'
    }
    
    proto = ProtoAgent(config)
    
    try:
        await proto.start()
    except KeyboardInterrupt:
        await proto.shutdown()


if __name__ == '__main__':
    asyncio.run(main())
