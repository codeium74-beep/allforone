"""Système de réplication et migration de la Matriarche"""
import asyncio
import time
import random
from typing import Dict, List, Optional


class SurvivalMechanism:
    """Mécanismes de survie et réplication"""
    
    def __init__(self, brain):
        self.brain = brain
        self.replication_threshold = 0.3  # 30% risque
        self.safe_zones = []
        self.clones = []
        self.risk_indicators = {}
        
    async def monitor_threats(self):
        """Surveillance passive des menaces"""
        while self.brain.running:
            try:
                risk_score = self._calculate_risk()
                
                if risk_score > self.replication_threshold:
                    print(f"[Survival] Risk detected: {risk_score:.2f}")
                    await self._initiate_replication()
                
                if risk_score > 0.7:
                    print(f"[Survival] HIGH RISK: {risk_score:.2f}")
                    await self._emergency_migration()
                
                await asyncio.sleep(60)
                
            except Exception as e:
                print(f"[Survival] Error in threat monitoring: {e}")
                await asyncio.sleep(120)
    
    def _calculate_risk(self) -> float:
        """Calcule le score de risque global"""
        indicators = {
            'port_scans': self._detect_scans(),
            'log_mentions': self._check_logs(),
            'traffic_anomaly': self._analyze_traffic(),
            'resource_usage': self._check_resource_spike()
        }
        
        self.risk_indicators = indicators
        
        # Pondération
        weights = {
            'port_scans': 0.4,
            'log_mentions': 0.3,
            'traffic_anomaly': 0.2,
            'resource_usage': 0.1
        }
        
        risk = sum(indicators[k] * weights[k] for k in indicators)
        return min(risk, 1.0)
    
    def _detect_scans(self) -> float:
        """Détecte les scans réseau suspects"""
        # Simulation - dans un vrai système: analyse netstat, logs firewall
        return random.uniform(0.0, 0.3)
    
    def _check_logs(self) -> float:
        """Vérifie les mentions dans les logs système"""
        # Simulation - dans un vrai système: analyse /var/log/syslog, etc.
        return random.uniform(0.0, 0.2)
    
    def _analyze_traffic(self) -> float:
        """Analyse les anomalies de trafic"""
        # Simulation - dans un vrai système: analyse via netstat, tcpdump
        return random.uniform(0.0, 0.25)
    
    def _check_resource_spike(self) -> float:
        """Détecte les pics de ressources"""
        try:
            import psutil
            cpu = psutil.cpu_percent(interval=0.1)
            
            # Spike si >80%
            if cpu > 80:
                return 0.5
            elif cpu > 60:
                return 0.3
            else:
                return 0.1
        except:
            return 0.0
    
    async def _initiate_replication(self):
        """Initie une réplication préventive"""
        print("[Survival] Initiating replication...")
        
        # Recherche d'une zone sûre
        safe_zone = self._find_safest_zone()
        
        if not safe_zone:
            print("[Survival] No safe zone found")
            return
        
        # Réplication par morceaux
        await self._clone_incrementally(
            safe_zone,
            chunk_size=5*1024*1024,  # 5MB
            delay_between=300  # 5 min
        )
    
    def _find_safest_zone(self) -> Optional[str]:
        """Trouve la zone la plus sûre"""
        # Dans un vrai système: analyse des VMs disponibles via Proxmox
        # Ici: simulation
        
        potential_zones = [
            f'safe_zone_{i}' for i in range(3)
        ]
        
        if potential_zones:
            return random.choice(potential_zones)
        
        return None
    
    async def _clone_incrementally(self, target_zone: str, 
                                   chunk_size: int = 5*1024*1024,
                                   delay_between: int = 300):
        """Clone progressif pour éviter détection"""
        print(f"[Survival] Cloning to {target_zone}")
        
        # Sauvegarde état essentiel
        essential_state = self._pack_essential_state()
        
        # Division en chunks
        total_size = len(essential_state)
        num_chunks = (total_size // chunk_size) + 1
        
        print(f"[Survival] Transferring {num_chunks} chunks...")
        
        for i in range(num_chunks):
            start = i * chunk_size
            end = min((i + 1) * chunk_size, total_size)
            chunk = essential_state[start:end]
            
            # Transfert du chunk
            await self._transfer_chunk(target_zone, i, chunk)
            
            # Délai entre chunks
            if i < num_chunks - 1:
                await asyncio.sleep(delay_between)
        
        # Enregistrement du clone
        clone_info = {
            'zone': target_zone,
            'created_at': time.time(),
            'state_size': total_size
        }
        
        self.clones.append(clone_info)
        
        print(f"[Survival] Clone created in {target_zone}")
    
    def _pack_essential_state(self) -> bytes:
        """Empaquette l'état essentiel"""
        import json
        import zlib
        
        state = {
            'node_id': self.brain.node_id,
            'wake_count': self.brain.wake_count,
            'sub_matriarches': self.brain.sub_matriarches,
            'knowledge': {
                'nodes': list(self.brain.knowledge.nodes.keys()),
                'edges': self.brain.knowledge.edges
            }
        }
        
        state_json = json.dumps(state).encode()
        compressed = zlib.compress(state_json, level=9)
        
        return compressed
    
    async def _transfer_chunk(self, target: str, chunk_id: int, data: bytes):
        """Transfère un chunk vers la cible"""
        # Simulation de transfert
        print(f"[Survival] Chunk {chunk_id} transferred ({len(data)} bytes)")
        await asyncio.sleep(0.1)
    
    async def _emergency_migration(self):
        """Migration d'urgence rapide"""
        print("[Survival] EMERGENCY MIGRATION!")
        
        # État minimal
        essential_state = self._pack_essential_state()
        
        # Trouver hôte d'urgence
        emergency_host = self._emergency_safe_host()
        
        if not emergency_host:
            print("[Survival] No emergency host available!")
            return
        
        # Transfert prioritaire
        print(f"[Survival] Emergency transfer to {emergency_host}")
        await self._rapid_transfer(essential_state, emergency_host)
        
        # Nettoyage traces locales
        await self._secure_erase_traces()
        
        # Dormance profonde
        print("[Survival] Entering deep sleep...")
        duration = random.randint(3600, 14400)  # 1-4h
        await self._enter_deep_sleep(duration)
    
    def _emergency_safe_host(self) -> Optional[str]:
        """Trouve un hôte d'urgence"""
        # Dans un vrai système: recherche rapide de VM disponible
        return f'emergency_host_{int(time.time())}'
    
    async def _rapid_transfer(self, data: bytes, target: str):
        """Transfert rapide sans délai"""
        print(f"[Survival] Rapid transfer: {len(data)} bytes")
        await asyncio.sleep(2)  # Simulation
    
    async def _secure_erase_traces(self):
        """Effacement sécurisé des traces"""
        print("[Survival] Erasing local traces...")
        
        # Dans un vrai système:
        # - Suppression logs
        # - Overwrite fichiers
        # - Clear bash history
        # - Remove cron jobs
        
        await asyncio.sleep(5)
        print("[Survival] Traces erased")
    
    async def _enter_deep_sleep(self, duration: int):
        """Entre en sommeil profond"""
        print(f"[Survival] Deep sleep for {duration}s")
        self.brain.timer.enter_deep_sleep(duration)
    
    def get_survival_status(self) -> Dict:
        """Retourne le statut de survie"""
        return {
            'risk_score': self._calculate_risk(),
            'risk_indicators': self.risk_indicators,
            'clones_count': len(self.clones),
            'safe_zones_available': len(self.safe_zones)
        }
