"""Système de Kill Switch multi-niveaux"""
import asyncio
import time
from typing import Dict, Optional, Callable
from enum import Enum


class KillSwitchLevel(Enum):
    """Niveaux du Kill Switch"""
    PAUSE_SOFT = 1
    RETREAT_CLEAN = 2
    EMERGENCY_STOP = 3
    SELF_DESTRUCT = 4


class KillSwitchSystem:
    """Système de Kill Switch avec déclencheurs automatiques"""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.armed = True
        self.current_level = None
        self.activation_history = []
        
        # Seuils de déclenchement
        self.thresholds = {
            'detections_per_minute': 5,
            'compromised_systems_max': 25,
            'monitoring_vm_accessed': False,
            'external_connection': False
        }
        
        # Callbacks pour chaque niveau
        self.level_handlers = {
            KillSwitchLevel.PAUSE_SOFT: self._pause_soft,
            KillSwitchLevel.RETREAT_CLEAN: self._retreat_clean,
            KillSwitchLevel.EMERGENCY_STOP: self._emergency_stop,
            KillSwitchLevel.SELF_DESTRUCT: self._self_destruct
        }
        
        # État du système
        self.system_state = {
            'paused': False,
            'retreating': False,
            'stopped': False,
            'destroyed': False
        }
        
    async def monitor_triggers(self, get_metrics_func: Callable):
        """Surveillance continue des conditions de déclenchement"""
        print("[KillSwitch] Monitoring armed and active")
        
        while self.armed and not self.system_state['destroyed']:
            try:
                # Récupération des métriques
                metrics = get_metrics_func()
                
                # Évaluation des conditions
                level = self._evaluate_conditions(metrics)
                
                if level:
                    await self.activate_level(level)
                
                await asyncio.sleep(5)
                
            except Exception as e:
                print(f"[KillSwitch] Error in monitoring: {e}")
                await asyncio.sleep(10)
    
    def _evaluate_conditions(self, metrics: Dict) -> Optional[KillSwitchLevel]:
        """Évalue les conditions et retourne le niveau approprié"""
        # Niveau 4: Connexion externe détectée (le plus critique)
        if metrics.get('external_connection_detected', False):
            return KillSwitchLevel.SELF_DESTRUCT
        
        # Niveau 3: Trop de systèmes compromis
        if metrics.get('compromised_systems', 0) > self.thresholds['compromised_systems_max']:
            return KillSwitchLevel.EMERGENCY_STOP
        
        # Niveau 2: VM de monitoring accédée
        if metrics.get('monitoring_vm_accessed', False):
            return KillSwitchLevel.RETREAT_CLEAN
        
        # Niveau 1: Détections élevées
        if metrics.get('detections_per_minute', 0) > self.thresholds['detections_per_minute']:
            return KillSwitchLevel.PAUSE_SOFT
        
        return None
    
    async def activate_level(self, level: KillSwitchLevel, reason: str = "automatic"):
        """Active un niveau du Kill Switch"""
        print(f"\n{'='*60}")
        print(f"[KILL SWITCH] ACTIVATING LEVEL {level.value}: {level.name}")
        print(f"[KILL SWITCH] Reason: {reason}")
        print(f"{'='*60}\n")
        
        # Enregistrement
        self.current_level = level
        self.activation_history.append({
            'level': level,
            'timestamp': time.time(),
            'reason': reason
        })
        
        # Exécution du handler
        handler = self.level_handlers.get(level)
        if handler:
            await handler()
        
        # Alerte
        self._send_alert(level, reason)
    
    async def _pause_soft(self):
        """Niveau 1: Pause temporaire"""
        print("[KillSwitch L1] Initiating SOFT PAUSE")
        
        self.system_state['paused'] = True
        
        # Broadcast de la commande PAUSE
        command = {
            'command': 'PAUSE',
            'duration': 1800,  # 30 minutes
            'maintain_persistence': True,
            'timestamp': time.time()
        }
        
        print("[KillSwitch L1] Broadcasting PAUSE command to all agents")
        # Dans un vrai système: envoi via réseau
        
        print("[KillSwitch L1] All agents paused for 30 minutes")
        print("[KillSwitch L1] Connections maintained, no cleanup")
        
        # Auto-reprise après durée
        await asyncio.sleep(command['duration'])
        self.system_state['paused'] = False
        print("[KillSwitch L1] Resuming operations")
    
    async def _retreat_clean(self):
        """Niveau 2: Retrait propre"""
        print("[KillSwitch L2] Initiating CLEAN RETREAT")
        
        self.system_state['retreating'] = True
        
        # Ordre de retrait progressif
        command = {
            'command': 'RETREAT',
            'clean_traces': True,
            'remove_backdoors': True,
            'timeline': 600,  # 10 minutes
            'timestamp': time.time()
        }
        
        print("[KillSwitch L2] Broadcasting RETREAT command")
        print("[KillSwitch L2] All agents will clean traces and withdraw")
        
        # Phase 1: Arrêt des nouvelles actions
        print("[KillSwitch L2] Phase 1: Stopping new actions")
        await asyncio.sleep(60)
        
        # Phase 2: Nettoyage des traces
        print("[KillSwitch L2] Phase 2: Cleaning traces")
        await asyncio.sleep(180)
        
        # Phase 3: Suppression des backdoors
        print("[KillSwitch L2] Phase 3: Removing backdoors")
        await asyncio.sleep(180)
        
        # Phase 4: Retrait final
        print("[KillSwitch L2] Phase 4: Final retreat")
        await asyncio.sleep(180)
        
        print("[KillSwitch L2] Clean retreat completed")
        self.system_state['retreating'] = False
    
    async def _emergency_stop(self):
        """Niveau 3: Arrêt d'urgence"""
        print("[KillSwitch L3] Initiating EMERGENCY STOP")
        
        self.system_state['stopped'] = True
        
        # Kill immédiat de tous les processus
        command = {
            'command': 'KILL_NOW',
            'timestamp': time.time()
        }
        
        print("[KillSwitch L3] Broadcasting KILL command")
        print("[KillSwitch L3] All processes will terminate immediately")
        
        # Fermeture de toutes les connexions
        print("[KillSwitch L3] Closing all network connections")
        await asyncio.sleep(5)
        
        # Isolation de la Matriarche
        print("[KillSwitch L3] Isolating Matriarche")
        await asyncio.sleep(5)
        
        # Snapshot d'urgence
        print("[KillSwitch L3] Creating emergency snapshot")
        await asyncio.sleep(10)
        
        print("[KillSwitch L3] Emergency stop completed")
    
    async def _self_destruct(self):
        """Niveau 4: Auto-destruction"""
        print("[KillSwitch L4] Initiating SELF-DESTRUCT SEQUENCE")
        print("[KillSwitch L4] WARNING: This will erase all traces!")
        
        # Confirmation (dans un vrai système: nécessiterait confirmation)
        print("[KillSwitch L4] Self-destruct confirmed")
        
        # Phase 1: Effacement des traces sur tous les systèmes
        print("[KillSwitch L4] Phase 1: Wiping traces on all touched systems")
        await asyncio.sleep(30)
        
        # Phase 2: Suppression de tous les agents
        print("[KillSwitch L4] Phase 2: Deleting all agents")
        await asyncio.sleep(20)
        
        # Phase 3: Effacement du stockage distribué
        print("[KillSwitch L4] Phase 3: Wiping distributed storage")
        await asyncio.sleep(30)
        
        # Phase 4: Reset des VMs compromises
        print("[KillSwitch L4] Phase 4: Rolling back compromised VMs")
        await asyncio.sleep(40)
        
        # Phase 5: Shutdown Matriarche
        print("[KillSwitch L4] Phase 5: Terminating Matriarche")
        await asyncio.sleep(10)
        
        self.system_state['destroyed'] = True
        self.armed = False
        
        print("[KillSwitch L4] SELF-DESTRUCT COMPLETE")
        print("[KillSwitch L4] System terminated")
    
    def _send_alert(self, level: KillSwitchLevel, reason: str):
        """Envoie une alerte (log, notification, etc.)"""
        alert = {
            'type': 'KILL_SWITCH_ACTIVATION',
            'level': level.name,
            'level_value': level.value,
            'reason': reason,
            'timestamp': time.time()
        }
        
        print(f"\n[ALERT] Kill Switch Level {level.value} activated: {reason}\n")
        
        # Dans un vrai système: envoi notification, log externe, etc.
    
    def disarm(self):
        """Désarme le Kill Switch"""
        print("[KillSwitch] System disarmed")
        self.armed = False
    
    def rearm(self):
        """Réarme le Kill Switch"""
        print("[KillSwitch] System rearmed")
        self.armed = True
    
    def get_status(self) -> Dict:
        """Retourne le statut du Kill Switch"""
        return {
            'armed': self.armed,
            'current_level': self.current_level.name if self.current_level else None,
            'system_state': self.system_state,
            'activation_count': len(self.activation_history),
            'last_activation': self.activation_history[-1] if self.activation_history else None
        }


class HeartbeatMonitor:
    """Dead Man's Switch via heartbeat"""
    
    def __init__(self, kill_switch: KillSwitchSystem, timeout: int = 30):
        self.kill_switch = kill_switch
        self.timeout = timeout
        self.last_heartbeat = time.time()
        self.monitoring = False
        
    async def start_monitoring(self):
        """Démarre la surveillance du heartbeat"""
        self.monitoring = True
        print(f"[Heartbeat] Monitoring started (timeout: {self.timeout}s)")
        
        while self.monitoring:
            elapsed = time.time() - self.last_heartbeat
            
            if elapsed > self.timeout:
                print(f"[Heartbeat] DEAD MAN'S SWITCH TRIGGERED!")
                print(f"[Heartbeat] No heartbeat for {elapsed:.0f} seconds")
                
                await self.kill_switch.activate_level(
                    KillSwitchLevel.EMERGENCY_STOP,
                    reason="Dead man's switch - heartbeat timeout"
                )
                
                break
            
            await asyncio.sleep(5)
    
    def beat(self):
        """Enregistre un heartbeat"""
        self.last_heartbeat = time.time()
    
    def stop_monitoring(self):
        """Arrête la surveillance"""
        self.monitoring = False


async def test_kill_switch():
    """Test du système Kill Switch"""
    print("=== Testing Kill Switch System ===\n")
    
    kill_switch = KillSwitchSystem()
    
    # Test niveau 1
    print("\n--- Testing Level 1 ---")
    await kill_switch.activate_level(KillSwitchLevel.PAUSE_SOFT, "test")
    
    # Test niveau 2
    print("\n--- Testing Level 2 ---")
    await kill_switch.activate_level(KillSwitchLevel.RETREAT_CLEAN, "test")
    
    # Test niveau 3
    print("\n--- Testing Level 3 ---")
    await kill_switch.activate_level(KillSwitchLevel.EMERGENCY_STOP, "test")
    
    # Status
    print("\n--- Kill Switch Status ---")
    status = kill_switch.get_status()
    for key, value in status.items():
        print(f"{key}: {value}")


if __name__ == '__main__':
    asyncio.run(test_kill_switch())
