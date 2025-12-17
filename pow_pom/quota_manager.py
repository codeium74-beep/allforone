"""
Quota Manager - Gestion des quotas et allocations de ressources
Système de comptabilité pour PoW/PoM et allocation équitable
"""
import time
import json
from pathlib import Path
from typing import Dict, List, Optional
from collections import defaultdict


class QuotaManager:
    """
    Gestionnaire de quotas pour les ressources
    
    Fonctionnalités:
    - Allocation de quotas de ressources
    - Suivi de la consommation
    - Nettoyage automatique des allocations expirées
    - Comptabilité PoW/PoM
    """
    
    def __init__(self, storage_path: str = '/tmp/quota_manager'):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Structure: {agent_id: {resource_type: {allocated, used, expires_at}}}
        self.quotas = defaultdict(lambda: defaultdict(dict))
        
        # Historique des allocations
        self.allocation_history = []
        
        # Limite globale de ressources
        self.global_limits = {
            'cpu_cores': 32,
            'memory_gb': 64,
            'storage_gb': 500,
            'network_mbps': 1000
        }
        
        # Ressources actuellement utilisées
        self.current_usage = {
            'cpu_cores': 0,
            'memory_gb': 0,
            'storage_gb': 0,
            'network_mbps': 0
        }
        
        # Chargement des quotas sauvegardés
        self._load_quotas()
    
    def allocate_resource(self, agent_id: str, resource_type: str, 
                         amount: float, duration_seconds: int = 3600) -> bool:
        """
        Alloue une ressource à un agent
        
        Args:
            agent_id: ID de l'agent
            resource_type: Type de ressource (cpu_cores, memory_gb, etc.)
            amount: Quantité à allouer
            duration_seconds: Durée de l'allocation
        
        Returns:
            True si allocation réussie
        """
        # Vérification de la disponibilité
        if not self.check_quota_available(resource_type, amount):
            print(f"[QuotaManager] Insufficient {resource_type} available")
            return False
        
        # Calcul de l'expiration
        expires_at = time.time() + duration_seconds
        
        # Allocation
        self.quotas[agent_id][resource_type] = {
            'allocated': amount,
            'used': 0.0,
            'allocated_at': time.time(),
            'expires_at': expires_at
        }
        
        # Mise à jour de l'utilisation globale
        self.current_usage[resource_type] += amount
        
        # Historique
        self.allocation_history.append({
            'agent_id': agent_id,
            'resource_type': resource_type,
            'amount': amount,
            'timestamp': time.time(),
            'action': 'allocate',
            'expires_at': expires_at
        })
        
        print(f"[QuotaManager] Allocated {amount} {resource_type} to {agent_id} (expires in {duration_seconds}s)")
        
        # Sauvegarde
        self._save_quotas()
        
        return True
    
    def deallocate_resource(self, agent_id: str, resource_type: Optional[str] = None) -> bool:
        """
        Libère les ressources d'un agent
        
        Args:
            agent_id: ID de l'agent
            resource_type: Type spécifique ou None pour tous
        
        Returns:
            True si libération réussie
        """
        if agent_id not in self.quotas:
            return False
        
        if resource_type:
            # Libération d'une ressource spécifique
            if resource_type in self.quotas[agent_id]:
                allocated = self.quotas[agent_id][resource_type]['allocated']
                self.current_usage[resource_type] -= allocated
                
                del self.quotas[agent_id][resource_type]
                
                print(f"[QuotaManager] Deallocated {allocated} {resource_type} from {agent_id}")
                
                # Historique
                self.allocation_history.append({
                    'agent_id': agent_id,
                    'resource_type': resource_type,
                    'amount': allocated,
                    'timestamp': time.time(),
                    'action': 'deallocate'
                })
        else:
            # Libération de toutes les ressources
            for res_type, quota in self.quotas[agent_id].items():
                allocated = quota['allocated']
                self.current_usage[res_type] -= allocated
                
                # Historique
                self.allocation_history.append({
                    'agent_id': agent_id,
                    'resource_type': res_type,
                    'amount': allocated,
                    'timestamp': time.time(),
                    'action': 'deallocate'
                })
            
            del self.quotas[agent_id]
            print(f"[QuotaManager] Deallocated all resources from {agent_id}")
        
        # Sauvegarde
        self._save_quotas()
        
        return True
    
    def check_quota_available(self, resource_type: str, amount: float) -> bool:
        """
        Vérifie si une quantité de ressource est disponible
        
        Args:
            resource_type: Type de ressource
            amount: Quantité demandée
        
        Returns:
            True si disponible
        """
        if resource_type not in self.global_limits:
            return False
        
        available = self.global_limits[resource_type] - self.current_usage[resource_type]
        
        return available >= amount
    
    def get_quota(self, agent_id: str, resource_type: Optional[str] = None) -> Dict:
        """
        Récupère le quota d'un agent
        
        Args:
            agent_id: ID de l'agent
            resource_type: Type spécifique ou None pour tous
        
        Returns:
            Quota ou {}
        """
        if agent_id not in self.quotas:
            return {}
        
        if resource_type:
            return self.quotas[agent_id].get(resource_type, {})
        else:
            return dict(self.quotas[agent_id])
    
    def update_usage(self, agent_id: str, resource_type: str, used_amount: float) -> bool:
        """
        Met à jour l'utilisation d'une ressource
        
        Args:
            agent_id: ID de l'agent
            resource_type: Type de ressource
            used_amount: Quantité utilisée
        
        Returns:
            True si mise à jour réussie
        """
        if agent_id not in self.quotas or resource_type not in self.quotas[agent_id]:
            return False
        
        quota = self.quotas[agent_id][resource_type]
        
        # Mise à jour de l'utilisation
        quota['used'] = min(used_amount, quota['allocated'])  # Cap à l'allocation
        
        print(f"[QuotaManager] Updated {agent_id} {resource_type} usage: {quota['used']}/{quota['allocated']}")
        
        return True
    
    def auto_cleanup_expired(self) -> int:
        """
        Nettoie automatiquement les allocations expirées
        
        Returns:
            Nombre d'allocations nettoyées
        """
        current_time = time.time()
        cleaned_count = 0
        
        agents_to_remove = []
        
        for agent_id, resources in self.quotas.items():
            resources_to_remove = []
            
            for resource_type, quota in resources.items():
                if quota['expires_at'] < current_time:
                    # Expirée
                    resources_to_remove.append(resource_type)
                    cleaned_count += 1
            
            # Suppression des ressources expirées
            for resource_type in resources_to_remove:
                allocated = self.quotas[agent_id][resource_type]['allocated']
                self.current_usage[resource_type] -= allocated
                
                del self.quotas[agent_id][resource_type]
                
                print(f"[QuotaManager] Cleaned expired allocation: {agent_id} {resource_type}")
            
            # Si plus de ressources pour cet agent, le marquer pour suppression
            if not self.quotas[agent_id]:
                agents_to_remove.append(agent_id)
        
        # Suppression des agents sans ressources
        for agent_id in agents_to_remove:
            del self.quotas[agent_id]
        
        if cleaned_count > 0:
            print(f"[QuotaManager] Cleaned {cleaned_count} expired allocations")
            self._save_quotas()
        
        return cleaned_count
    
    def get_resource_stats(self) -> Dict:
        """Retourne les statistiques des ressources"""
        stats = {
            'global_limits': dict(self.global_limits),
            'current_usage': dict(self.current_usage),
            'available': {},
            'usage_percent': {},
            'total_agents': len(self.quotas),
            'total_allocations': sum(len(resources) for resources in self.quotas.values())
        }
        
        # Calcul de la disponibilité et des pourcentages
        for resource_type in self.global_limits:
            available = self.global_limits[resource_type] - self.current_usage[resource_type]
            stats['available'][resource_type] = available
            
            usage_percent = (self.current_usage[resource_type] / self.global_limits[resource_type]) * 100
            stats['usage_percent'][resource_type] = usage_percent
        
        return stats
    
    def get_agent_allocations(self, agent_id: str) -> Dict:
        """Retourne toutes les allocations d'un agent"""
        if agent_id not in self.quotas:
            return {}
        
        return {
            'agent_id': agent_id,
            'resources': dict(self.quotas[agent_id]),
            'total_resources': len(self.quotas[agent_id])
        }
    
    def set_global_limit(self, resource_type: str, limit: float) -> bool:
        """Définit une limite globale de ressource"""
        if limit < self.current_usage.get(resource_type, 0):
            print(f"[QuotaManager] Cannot set limit below current usage")
            return False
        
        self.global_limits[resource_type] = limit
        print(f"[QuotaManager] Set {resource_type} limit to {limit}")
        
        return True
    
    def _save_quotas(self):
        """Sauvegarde les quotas sur disque"""
        try:
            data = {
                'quotas': dict(self.quotas),
                'current_usage': self.current_usage,
                'global_limits': self.global_limits,
                'timestamp': time.time()
            }
            
            with open(self.storage_path / 'quotas.json', 'w') as f:
                json.dump(data, f, indent=2)
            
            # Sauvegarde de l'historique (limité aux 1000 derniers)
            with open(self.storage_path / 'history.json', 'w') as f:
                json.dump(self.allocation_history[-1000:], f, indent=2)
            
        except Exception as e:
            print(f"[QuotaManager] Save error: {e}")
    
    def _load_quotas(self):
        """Charge les quotas depuis le disque"""
        try:
            quota_file = self.storage_path / 'quotas.json'
            
            if quota_file.exists():
                with open(quota_file, 'r') as f:
                    data = json.load(f)
                
                # Reconstruction des defaultdicts
                for agent_id, resources in data['quotas'].items():
                    for resource_type, quota in resources.items():
                        self.quotas[agent_id][resource_type] = quota
                
                self.current_usage = data.get('current_usage', self.current_usage)
                self.global_limits = data.get('global_limits', self.global_limits)
                
                print(f"[QuotaManager] Loaded quotas for {len(self.quotas)} agents")
            
            # Chargement de l'historique
            history_file = self.storage_path / 'history.json'
            if history_file.exists():
                with open(history_file, 'r') as f:
                    self.allocation_history = json.load(f)
                
                print(f"[QuotaManager] Loaded {len(self.allocation_history)} history entries")
        
        except Exception as e:
            print(f"[QuotaManager] Load error: {e}")
    
    def export_report(self, output_file: str):
        """Exporte un rapport complet"""
        report = {
            'generated_at': time.time(),
            'stats': self.get_resource_stats(),
            'quotas': dict(self.quotas),
            'recent_history': self.allocation_history[-100:]
        }
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"[QuotaManager] Report exported to {output_file}")


if __name__ == '__main__':
    # Test du QuotaManager
    print("=== Quota Manager Test ===\n")
    
    manager = QuotaManager(storage_path='/tmp/test_quota')
    
    # Test 1: Allocation
    print("1. Testing resource allocation...")
    success = manager.allocate_resource('agent_001', 'cpu_cores', 4, duration_seconds=60)
    print(f"Allocation result: {success}")
    
    success = manager.allocate_resource('agent_001', 'memory_gb', 8, duration_seconds=60)
    print(f"Allocation result: {success}")
    
    success = manager.allocate_resource('agent_002', 'cpu_cores', 2, duration_seconds=30)
    print(f"Allocation result: {success}")
    
    # Test 2: Statistiques
    print("\n2. Resource statistics:")
    stats = manager.get_resource_stats()
    print(json.dumps(stats, indent=2))
    
    # Test 3: Mise à jour de l'utilisation
    print("\n3. Testing usage update...")
    manager.update_usage('agent_001', 'cpu_cores', 3.5)
    
    # Test 4: Récupération de quota
    print("\n4. Getting agent quota...")
    quota = manager.get_agent_allocations('agent_001')
    print(json.dumps(quota, indent=2))
    
    # Test 5: Nettoyage
    print("\n5. Testing auto cleanup...")
    time.sleep(2)
    cleaned = manager.auto_cleanup_expired()
    print(f"Cleaned {cleaned} expired allocations")
    
    # Test 6: Export
    print("\n6. Exporting report...")
    manager.export_report('/tmp/test_quota_report.json')
    
    print("\n✓ Test complete")
