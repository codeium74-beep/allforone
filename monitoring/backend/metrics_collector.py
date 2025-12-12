"""Collecteur de métriques système en temps réel"""
import psutil
import time
import asyncio
from typing import Dict, List
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class MetricsCollector:
    """Collecte des métriques système"""
    
    def __init__(self):
        self.metrics_history = []
        self.max_history_size = 1000
        
    def collect_system_metrics(self) -> Dict:
        """Collecte les métriques système globales"""
        cpu_percent = psutil.cpu_percent(interval=0.1, percpu=True)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            'timestamp': time.time(),
            'cpu': {
                'total_percent': sum(cpu_percent) / len(cpu_percent),
                'per_core': cpu_percent,
                'count': psutil.cpu_count()
            },
            'memory': {
                'total_mb': memory.total / 1024 / 1024,
                'used_mb': memory.used / 1024 / 1024,
                'available_mb': memory.available / 1024 / 1024,
                'percent': memory.percent
            },
            'disk': {
                'total_gb': disk.total / 1024 / 1024 / 1024,
                'used_gb': disk.used / 1024 / 1024 / 1024,
                'free_gb': disk.free / 1024 / 1024 / 1024,
                'percent': disk.percent
            }
        }
    
    def collect_network_metrics(self) -> Dict:
        """Collecte les métriques réseau"""
        net_io = psutil.net_io_counters()
        connections = psutil.net_connections(kind='inet')
        
        return {
            'timestamp': time.time(),
            'bytes_sent': net_io.bytes_sent,
            'bytes_recv': net_io.bytes_recv,
            'packets_sent': net_io.packets_sent,
            'packets_recv': net_io.packets_recv,
            'active_connections': len(connections),
            'established_connections': len([c for c in connections if c.status == 'ESTABLISHED'])
        }
    
    def store_metrics(self, metrics: Dict):
        """Stocke les métriques dans l'historique"""
        self.metrics_history.append(metrics)
        
        # Limite la taille de l'historique
        if len(self.metrics_history) > self.max_history_size:
            self.metrics_history = self.metrics_history[-self.max_history_size:]
    
    def get_recent_metrics(self, count: int = 100) -> List[Dict]:
        """Retourne les N dernières métriques"""
        return self.metrics_history[-count:]
    
    def get_average_metrics(self, duration_seconds: int = 60) -> Dict:
        """Calcule les moyennes sur une durée"""
        cutoff_time = time.time() - duration_seconds
        recent = [m for m in self.metrics_history if m['timestamp'] > cutoff_time]
        
        if not recent:
            return {}
        
        avg_cpu = sum(m['cpu']['total_percent'] for m in recent) / len(recent)
        avg_memory = sum(m['memory']['percent'] for m in recent) / len(recent)
        avg_disk = sum(m['disk']['percent'] for m in recent) / len(recent)
        
        return {
            'duration_seconds': duration_seconds,
            'sample_count': len(recent),
            'avg_cpu_percent': avg_cpu,
            'avg_memory_percent': avg_memory,
            'avg_disk_percent': avg_disk
        }


class HierarchyMetricsCollector:
    """Collecte des métriques spécifiques à la hiérarchie"""
    
    def __init__(self):
        self.matriarche_metrics = {}
        self.sub_matriarche_metrics = {}
        self.proto_metrics = {}
        self.perceptor_metrics = {}
        
    def update_matriarche_metrics(self, metrics: Dict):
        """Met à jour les métriques de la Matriarche"""
        self.matriarche_metrics = {
            **metrics,
            'timestamp': time.time()
        }
    
    def update_sub_metrics(self, sub_id: str, metrics: Dict):
        """Met à jour les métriques d'une Sous-Matriarche"""
        self.sub_matriarche_metrics[sub_id] = {
            **metrics,
            'timestamp': time.time()
        }
    
    def update_proto_metrics(self, proto_id: str, metrics: Dict):
        """Met à jour les métriques d'un Proto"""
        self.proto_metrics[proto_id] = {
            **metrics,
            'timestamp': time.time()
        }
    
    def update_perceptor_metrics(self, perceptor_id: str, metrics: Dict):
        """Met à jour les métriques d'un Percepteur"""
        self.perceptor_metrics[perceptor_id] = {
            **metrics,
            'timestamp': time.time()
        }
    
    def get_hierarchy_summary(self) -> Dict:
        """Génère un résumé de la hiérarchie"""
        return {
            'timestamp': time.time(),
            'matriarche': {
                'active': bool(self.matriarche_metrics),
                'status': self.matriarche_metrics.get('state', 'unknown'),
                'wake_count': self.matriarche_metrics.get('wake_count', 0)
            },
            'sub_matriarches': {
                'count': len(self.sub_matriarche_metrics),
                'active': len([s for s in self.sub_matriarche_metrics.values() 
                             if s.get('state') == 'active']),
                'total_protos': sum(s.get('proto_count', 0) 
                                   for s in self.sub_matriarche_metrics.values())
            },
            'proto_agents': {
                'count': len(self.proto_metrics),
                'exploring': len([p for p in self.proto_metrics.values() 
                                if p.get('status') == 'exploring']),
                'working': len([p for p in self.proto_metrics.values() 
                              if p.get('status') == 'working'])
            },
            'perceptors': {
                'count': len(self.perceptor_metrics),
                'suspicious_activities': sum(p.get('suspicious_count', 0) 
                                            for p in self.perceptor_metrics.values())
            }
        }


class MissionMetricsCollector:
    """Collecte des métriques de missions"""
    
    def __init__(self):
        self.active_missions = {}
        self.completed_missions = []
        self.mission_history = []
        
    def register_mission(self, mission_id: str, mission_data: Dict):
        """Enregistre une nouvelle mission"""
        self.active_missions[mission_id] = {
            **mission_data,
            'start_time': time.time(),
            'status': 'active'
        }
    
    def update_mission_progress(self, mission_id: str, progress: Dict):
        """Met à jour la progression d'une mission"""
        if mission_id in self.active_missions:
            self.active_missions[mission_id].update(progress)
            self.active_missions[mission_id]['last_update'] = time.time()
    
    def complete_mission(self, mission_id: str, result: Dict):
        """Marque une mission comme complétée"""
        if mission_id in self.active_missions:
            mission = self.active_missions.pop(mission_id)
            mission['status'] = 'completed'
            mission['completion_time'] = time.time()
            mission['duration'] = mission['completion_time'] - mission['start_time']
            mission['result'] = result
            
            self.completed_missions.append(mission)
            self.mission_history.append(mission)
    
    def get_mission_stats(self) -> Dict:
        """Statistiques des missions"""
        if not self.completed_missions:
            avg_duration = 0
        else:
            avg_duration = sum(m['duration'] for m in self.completed_missions) / len(self.completed_missions)
        
        return {
            'active_count': len(self.active_missions),
            'completed_count': len(self.completed_missions),
            'total_count': len(self.mission_history),
            'avg_duration_seconds': avg_duration,
            'success_rate': self._calculate_success_rate()
        }
    
    def _calculate_success_rate(self) -> float:
        """Calcule le taux de succès"""
        if not self.completed_missions:
            return 0.0
        
        successful = len([m for m in self.completed_missions 
                         if m.get('result', {}).get('success', False)])
        
        return successful / len(self.completed_missions)


async def metrics_collection_loop(system_collector: MetricsCollector, 
                                  hierarchy_collector: HierarchyMetricsCollector):
    """Boucle de collecte continue"""
    while True:
        try:
            # Collecte des métriques système
            sys_metrics = system_collector.collect_system_metrics()
            system_collector.store_metrics(sys_metrics)
            
            # Collecte des métriques réseau
            net_metrics = system_collector.collect_network_metrics()
            
            # Pause
            await asyncio.sleep(5)
            
        except Exception as e:
            print(f"[MetricsCollector] Error: {e}")
            await asyncio.sleep(10)
