"""Système de timer aléatoire pour réveils de la Matriarche"""
import random
import time
from datetime import datetime
from typing import Optional


class MatriarchTimer:
    """Gestion des cycles de réveil/sommeil aléatoires"""
    
    def __init__(self, 
                 min_sleep: int = 600,      # 10 minutes
                 max_sleep: int = 21600,    # 6 heures
                 wake_variance: float = 0.3):  # ±30%
        self.min_sleep = min_sleep
        self.max_sleep = max_sleep
        self.wake_variance = wake_variance
        self.last_wake = time.time()
        self.next_wake_scheduled = None
        
        # Pondération selon heure de la journée
        self.hour_weights = {
            range(0, 6): 2.0,      # Nuit : plus probable
            range(6, 9): 0.5,      # Matin : moins probable
            range(9, 17): 0.3,     # Journée : rare
            range(17, 23): 0.8,    # Soirée : moyen
        }
    
    def next_wake_time(self) -> float:
        """Calcule le prochain temps de réveil aléatoire"""
        # Intervalle de base aléatoire
        base_interval = random.uniform(self.min_sleep, self.max_sleep)
        
        # Variance supplémentaire
        variance = base_interval * random.uniform(
            -self.wake_variance, 
            self.wake_variance
        )
        
        return base_interval + variance
    
    def should_wake(self) -> bool:
        """Détermine si la Matriarche devrait se réveiller"""
        current_hour = datetime.now().hour
        
        # Poids selon l'heure
        weight = self._get_hour_weight(current_hour)
        
        # Temps écoulé depuis dernier réveil
        elapsed = time.time() - self.last_wake
        
        # Calcul du seuil ajusté
        if self.next_wake_scheduled is None:
            self.next_wake_scheduled = self.next_wake_time()
        
        threshold = self.next_wake_scheduled / weight
        
        # Décision probabiliste même si temps écoulé
        if elapsed > threshold:
            # 70% de chance de se réveiller si temps écoulé
            should_wake = random.random() > 0.3
            if should_wake:
                self.last_wake = time.time()
                self.next_wake_scheduled = None  # Recalcul au prochain cycle
            return should_wake
        
        return False
    
    def force_wake(self):
        """Force un réveil immédiat (ex: mission urgente)"""
        self.last_wake = time.time()
        self.next_wake_scheduled = None
    
    def enter_deep_sleep(self, duration: Optional[int] = None):
        """Entre en sommeil profond pour une durée spécifiée"""
        if duration is None:
            duration = random.randint(3600, 14400)  # 1-4 heures
        
        self.next_wake_scheduled = duration
        self.last_wake = time.time()
    
    def get_sleep_status(self) -> dict:
        """Retourne le statut actuel du timer"""
        elapsed = time.time() - self.last_wake
        
        if self.next_wake_scheduled:
            remaining = max(0, self.next_wake_scheduled - elapsed)
        else:
            remaining = self.next_wake_time()
        
        return {
            'last_wake': self.last_wake,
            'last_wake_datetime': datetime.fromtimestamp(self.last_wake).isoformat(),
            'elapsed_seconds': elapsed,
            'next_wake_estimated_seconds': remaining,
            'current_hour': datetime.now().hour,
            'hour_weight': self._get_hour_weight(datetime.now().hour)
        }
    
    def _get_hour_weight(self, hour: int) -> float:
        """Obtient le poids pour une heure donnée"""
        for hour_range, weight in self.hour_weights.items():
            if hour in hour_range:
                return weight
        return 1.0


class DistributedTimer:
    """Timer distribué pour synchronisation sans horloge centrale"""
    
    def __init__(self, node_id: str):
        self.node_id = node_id
        self.local_time = time.time()
        self.time_offsets = {}  # Offsets avec autres nœuds
        
    def sync_with_peer(self, peer_id: str, peer_timestamp: float):
        """Synchronise l'horloge avec un pair"""
        # Calcul offset simple (amélioration possible avec NTP-like)
        current_time = time.time()
        offset = peer_timestamp - current_time
        
        self.time_offsets[peer_id] = offset
    
    def get_consensus_time(self) -> float:
        """Obtient le temps consensuel basé sur les pairs"""
        if not self.time_offsets:
            return time.time()
        
        # Médiane des offsets pour robustesse
        offsets = sorted(self.time_offsets.values())
        median_offset = offsets[len(offsets) // 2]
        
        return time.time() + median_offset
    
    def schedule_distributed_action(self, 
                                    action_time: float, 
                                    tolerance: float = 5.0) -> bool:
        """Vérifie si c'est le moment d'exécuter une action distribuée"""
        consensus_time = self.get_consensus_time()
        
        # Tolérance pour exécution distribuée
        return abs(consensus_time - action_time) <= tolerance
