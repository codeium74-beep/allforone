"""Cerveau de la Sous-Matriarche - Gestionnaire de terrain"""
import asyncio
import time
import sys
from pathlib import Path
from typing import Dict, List, Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.crypto_utils import CryptoManager
from utils.storage_utils import DistributedStorage
from utils.network_utils import P2PDiscovery, MulticastBeacon


class SubMatriarchBrain:
    """Gestionnaire de terrain entre Matriarche et Proto-Agents"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.node_id = config.get('node_id', f'sub_matriarche_{int(time.time())}')
        self.state = 'initializing'
        
        # Crypto
        self.crypto = CryptoManager()
        self.private_key, self.public_key = self.crypto.generate_keypair()
        
        # Stockage
        storage_path = config.get('storage_path', f'/tmp/sub_{self.node_id}')
        self.storage = DistributedStorage(storage_path)
        
        # Pool de Proto-Agents
        self.proto_pool_size = config.get('proto_pool_size', 15)
        self.proto_agents = []
        
        # Missions
        self.current_missions = []
        self.completed_tasks = []
        
        # Cache de connaissances locales
        self.knowledge_cache = {}
        
        # Communication
        self.p2p_discovery = P2PDiscovery("_submatri._tcp.local.")
        self.beacon = MulticastBeacon(self.node_id, 'sub_matriarche')
        
        # Timing
        self.last_report = 0
        self.report_interval = config.get('report_interval', 1800)  # 30 min
        
        self.running = False
        
    async def start(self):
        """Démarre le cycle de vie de la Sous-Matriarche"""
        self.running = True
        print(f"[{self.node_id}] Sub-Matriarche starting...")
        
        # Enregistrement du service
        self._register_service()
        
        # Enregistrement auprès de la Matriarche
        await self._register_with_matriarche()
        
        # Démarrage du pool de Protos
        await self._initialize_proto_pool()
        
        self.state = 'active'
        
        # Boucle principale
        await asyncio.gather(
            self._main_loop(),
            self._mission_check_loop(),
            self._report_loop(),
            self._proto_management_loop()
        )
    
    async def _main_loop(self):
        """Boucle principale de gestion"""
        while self.running:
            try:
                # Vérification santé générale
                await self._health_check()
                
                # Pause
                await asyncio.sleep(30)
                
            except Exception as e:
                print(f"[{self.node_id}] Error in main loop: {e}")
                await asyncio.sleep(60)
    
    async def _mission_check_loop(self):
        """Vérification périodique des nouvelles missions"""
        while self.running:
            try:
                # Recherche de nouvelles missions
                new_missions = await self._check_for_missions()
                
                for mission in new_missions:
                    await self._process_mission(mission)
                
                await asyncio.sleep(60)
                
            except Exception as e:
                print(f"[{self.node_id}] Error in mission check: {e}")
                await asyncio.sleep(120)
    
    async def _report_loop(self):
        """Envoi périodique des rapports"""
        while self.running:
            try:
                if time.time() - self.last_report > self.report_interval:
                    await self._send_report_to_matriarche()
                
                await asyncio.sleep(300)  # Check every 5 min
                
            except Exception as e:
                print(f"[{self.node_id}] Error in report loop: {e}")
                await asyncio.sleep(600)
    
    async def _proto_management_loop(self):
        """Gestion du pool de Proto-Agents"""
        while self.running:
            try:
                # Vérification santé des Protos
                await self._check_proto_health()
                
                # Équilibrage de charge
                await self._rebalance_proto_tasks()
                
                # Collecte des découvertes P2P
                await self._aggregate_proto_discoveries()
                
                await asyncio.sleep(120)
                
            except Exception as e:
                print(f"[{self.node_id}] Error in proto management: {e}")
                await asyncio.sleep(180)
    
    def _register_service(self):
        """Enregistre le service pour découverte"""
        port = self.config.get('port', 9000 + hash(self.node_id) % 1000)
        
        self.p2p_discovery.register_service(
            self.node_id,
            port,
            {
                'type': 'sub_matriarche',
                'proto_capacity': self.proto_pool_size,
                'timestamp': time.time()
            }
        )
        
        print(f"[{self.node_id}] Service registered on port {port}")
    
    async def _register_with_matriarche(self):
        """S'enregistre auprès de la Matriarche"""
        registration = {
            'type': 'sub_registration',
            'sub_id': self.node_id,
            'public_key': self.public_key,
            'timestamp': time.time()
        }
        
        # Stockage pour récupération par Matriarche
        self.storage.store(f'registration_{self.node_id}', str(registration).encode())
        
        print(f"[{self.node_id}] Registered with Matriarche")
    
    async def _initialize_proto_pool(self):
        """Initialise le pool de Proto-Agents"""
        for i in range(self.proto_pool_size):
            proto_id = f"{self.node_id}_proto_{i}"
            proto = {
                'id': proto_id,
                'status': 'idle',
                'current_task': None,
                'discoveries': [],
                'last_seen': time.time()
            }
            self.proto_agents.append(proto)
        
        print(f"[{self.node_id}] Initialized {len(self.proto_agents)} Proto-Agents")
    
    async def _check_for_missions(self) -> List[Dict]:
        """Vérifie si de nouvelles missions ont été assignées"""
        missions = []
        
        try:
            # Recherche dans le stockage
            mission_data = self.storage.retrieve(f'mission_{self.node_id}')
            if mission_data:
                mission = eval(mission_data.decode())
                missions.append(mission)
        except Exception as e:
            pass
        
        return missions
    
    async def _process_mission(self, mission: Dict):
        """Traite une nouvelle mission"""
        print(f"[{self.node_id}] Processing mission: {mission.get('mission_id')}")
        
        tasks = mission.get('tasks', [])
        self.current_missions.append(mission)
        
        # Distribution des tâches aux Protos
        for task in tasks:
            assigned_proto = self._select_proto_for_task(task)
            if assigned_proto:
                await self._assign_task_to_proto(assigned_proto, task)
    
    def _select_proto_for_task(self, task: Dict) -> Optional[Dict]:
        """Sélectionne un Proto approprié pour une tâche"""
        # Filtre les Protos disponibles
        available = [p for p in self.proto_agents if p['status'] == 'idle']
        
        if not available:
            # Sélection du moins chargé
            available = sorted(self.proto_agents, 
                             key=lambda p: len(p.get('discoveries', [])))
        
        if available:
            return available[0]
        
        return None
    
    async def _assign_task_to_proto(self, proto: Dict, task: Dict):
        """Assigne une tâche à un Proto"""
        proto['status'] = 'working'
        proto['current_task'] = task
        proto['task_started'] = time.time()
        
        print(f"[{self.node_id}] Assigned task {task['task_id']} to {proto['id']}")
    
    async def _check_proto_health(self):
        """Vérifie la santé des Protos"""
        for proto in self.proto_agents:
            # Timeout si tâche trop longue (> 1 heure)
            if proto['status'] == 'working':
                elapsed = time.time() - proto.get('task_started', time.time())
                if elapsed > 3600:
                    print(f"[{self.node_id}] Proto {proto['id']} timeout, resetting...")
                    proto['status'] = 'idle'
                    proto['current_task'] = None
    
    async def _rebalance_proto_tasks(self):
        """Équilibre la charge entre les Protos"""
        # Compte les Protos actifs
        working = [p for p in self.proto_agents if p['status'] == 'working']
        idle = [p for p in self.proto_agents if p['status'] == 'idle']
        
        # Si déséquilibre important, redistribuer
        if len(working) > len(self.proto_agents) * 0.8 and idle:
            print(f"[{self.node_id}] Load balancing: {len(working)} working, {len(idle)} idle")
    
    async def _aggregate_proto_discoveries(self):
        """Agrège les découvertes des Protos"""
        all_discoveries = []
        
        for proto in self.proto_agents:
            discoveries = proto.get('discoveries', [])
            all_discoveries.extend(discoveries)
            
            # Intégration au cache local
            for discovery in discoveries:
                discovery_id = discovery.get('id', f"disc_{time.time()}")
                self.knowledge_cache[discovery_id] = discovery
        
        if all_discoveries:
            print(f"[{self.node_id}] Aggregated {len(all_discoveries)} discoveries")
    
    async def _send_report_to_matriarche(self):
        """Envoie un rapport à la Matriarche"""
        report = self._generate_report()
        
        # Signature du rapport
        report_data = str(report).encode()
        signature = self.crypto.sign_data(report_data)
        report['signature'] = signature
        
        # Stockage pour récupération
        response_id = f"report_response_{self.node_id}"
        self.storage.store(response_id, str(report).encode())
        
        self.last_report = time.time()
        
        print(f"[{self.node_id}] Sent report to Matriarche")
    
    def _generate_report(self) -> Dict:
        """Génère un rapport de statut"""
        return {
            'sub_id': self.node_id,
            'timestamp': time.time(),
            'protos_status': {
                'total': len(self.proto_agents),
                'working': len([p for p in self.proto_agents if p['status'] == 'working']),
                'idle': len([p for p in self.proto_agents if p['status'] == 'idle'])
            },
            'discoveries': list(self.knowledge_cache.values()),
            'mission_progress': {
                'active_missions': len(self.current_missions),
                'completed_tasks': len(self.completed_tasks)
            },
            'p2p_exchanges': self._get_p2p_exchanges()
        }
    
    def _get_p2p_exchanges(self) -> List[Dict]:
        """Récupère les échanges P2P entre Protos"""
        exchanges = []
        
        for proto in self.proto_agents:
            if 'p2p_encounters' in proto:
                exchanges.extend(proto['p2p_encounters'])
        
        return exchanges
    
    async def _health_check(self):
        """Vérification de santé générale"""
        # Vérification espace stockage
        stats = self.storage.get_storage_stats()
        if stats['total_size_mb'] > 100:  # Limite 100MB
            print(f"[{self.node_id}] WARNING: Storage usage high: {stats['total_size_mb']:.2f}MB")
    
    async def shutdown(self):
        """Arrêt propre"""
        print(f"[{self.node_id}] Shutting down...")
        self.running = False
        self.p2p_discovery.close()


async def main():
    """Point d'entrée"""
    import sys
    
    sub_id = sys.argv[1] if len(sys.argv) > 1 else f'sub_{int(time.time())}'
    
    config = {
        'node_id': sub_id,
        'proto_pool_size': 15,
        'storage_path': f'/tmp/sub_{sub_id}',
        'report_interval': 1800
    }
    
    brain = SubMatriarchBrain(config)
    
    try:
        await brain.start()
    except KeyboardInterrupt:
        await brain.shutdown()


if __name__ == '__main__':
    asyncio.run(main())
