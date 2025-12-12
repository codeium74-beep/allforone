"""Allocateur de ressources via API Proxmox (simulation)"""
import time
from typing import Dict, List, Optional
import asyncio


class ResourceAllocator:
    """Gestion de l'allocation dynamique de ressources"""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.allocations = {}
        self.max_cpu_per_vm = self.config.get('max_cpu_per_vm', 8)
        self.max_ram_per_vm = self.config.get('max_ram_per_vm', 16384)  # MB
        self.max_storage_per_vm = self.config.get('max_storage_per_vm', 102400)  # MB
        
    async def allocate_cpu(self, node_id: str, cores: int, duration: int) -> bool:
        """Alloue des cores CPU à un nœud"""
        print(f"[ResourceAllocator] Allocating {cores} CPU cores to {node_id} for {duration}s")
        
        # Vérification des limites
        current_allocation = self.allocations.get(node_id, {})
        current_cpu = current_allocation.get('cpu_cores', 0)
        
        if current_cpu + cores > self.max_cpu_per_vm:
            print(f"[ResourceAllocator] CPU allocation would exceed max: {self.max_cpu_per_vm}")
            return False
        
        # Simulation d'allocation via API Proxmox
        # Dans un vrai système:
        # - Connexion à Proxmox API
        # - Modification de la config VM
        # - Redémarrage si nécessaire
        
        await asyncio.sleep(0.1)  # Simule latence API
        
        # Enregistrement de l'allocation
        if node_id not in self.allocations:
            self.allocations[node_id] = {
                'cpu_cores': 0,
                'ram_mb': 0,
                'storage_mb': 0,
                'allocations': []
            }
        
        allocation_record = {
            'type': 'cpu',
            'amount': cores,
            'allocated_at': time.time(),
            'expires_at': time.time() + duration
        }
        
        self.allocations[node_id]['cpu_cores'] += cores
        self.allocations[node_id]['allocations'].append(allocation_record)
        
        # Programmation du retrait
        asyncio.create_task(self._schedule_deallocation(node_id, allocation_record))
        
        print(f"[ResourceAllocator] CPU allocated successfully. Total: {self.allocations[node_id]['cpu_cores']} cores")
        
        return True
    
    async def allocate_ram(self, node_id: str, mb: int, duration: int) -> bool:
        """Alloue de la RAM à un nœud"""
        print(f"[ResourceAllocator] Allocating {mb}MB RAM to {node_id} for {duration}s")
        
        # Vérification des limites
        current_allocation = self.allocations.get(node_id, {})
        current_ram = current_allocation.get('ram_mb', 0)
        
        if current_ram + mb > self.max_ram_per_vm:
            print(f"[ResourceAllocator] RAM allocation would exceed max: {self.max_ram_per_vm}MB")
            return False
        
        await asyncio.sleep(0.1)
        
        # Enregistrement
        if node_id not in self.allocations:
            self.allocations[node_id] = {
                'cpu_cores': 0,
                'ram_mb': 0,
                'storage_mb': 0,
                'allocations': []
            }
        
        allocation_record = {
            'type': 'ram',
            'amount': mb,
            'allocated_at': time.time(),
            'expires_at': time.time() + duration
        }
        
        self.allocations[node_id]['ram_mb'] += mb
        self.allocations[node_id]['allocations'].append(allocation_record)
        
        asyncio.create_task(self._schedule_deallocation(node_id, allocation_record))
        
        print(f"[ResourceAllocator] RAM allocated successfully. Total: {self.allocations[node_id]['ram_mb']}MB")
        
        return True
    
    async def allocate_storage(self, node_id: str, mb: int, duration: int) -> bool:
        """Alloue du stockage à un nœud"""
        print(f"[ResourceAllocator] Allocating {mb}MB storage to {node_id} for {duration}s")
        
        # Vérification des limites
        current_allocation = self.allocations.get(node_id, {})
        current_storage = current_allocation.get('storage_mb', 0)
        
        if current_storage + mb > self.max_storage_per_vm:
            print(f"[ResourceAllocator] Storage allocation would exceed max: {self.max_storage_per_vm}MB")
            return False
        
        await asyncio.sleep(0.1)
        
        # Enregistrement
        if node_id not in self.allocations:
            self.allocations[node_id] = {
                'cpu_cores': 0,
                'ram_mb': 0,
                'storage_mb': 0,
                'allocations': []
            }
        
        allocation_record = {
            'type': 'storage',
            'amount': mb,
            'allocated_at': time.time(),
            'expires_at': time.time() + duration
        }
        
        self.allocations[node_id]['storage_mb'] += mb
        self.allocations[node_id]['allocations'].append(allocation_record)
        
        asyncio.create_task(self._schedule_deallocation(node_id, allocation_record))
        
        print(f"[ResourceAllocator] Storage allocated successfully. Total: {self.allocations[node_id]['storage_mb']}MB")
        
        return True
    
    async def _schedule_deallocation(self, node_id: str, allocation: Dict):
        """Programme le retrait d'une allocation"""
        duration = allocation['expires_at'] - allocation['allocated_at']
        
        await asyncio.sleep(duration)
        
        # Retrait de l'allocation
        if node_id in self.allocations:
            alloc_type = allocation['type']
            amount = allocation['amount']
            
            if alloc_type == 'cpu':
                self.allocations[node_id]['cpu_cores'] -= amount
            elif alloc_type == 'ram':
                self.allocations[node_id]['ram_mb'] -= amount
            elif alloc_type == 'storage':
                self.allocations[node_id]['storage_mb'] -= amount
            
            # Retrait du record
            if allocation in self.allocations[node_id]['allocations']:
                self.allocations[node_id]['allocations'].remove(allocation)
            
            print(f"[ResourceAllocator] Deallocated {amount} {alloc_type} from {node_id}")
    
    def get_node_resources(self, node_id: str) -> Optional[Dict]:
        """Retourne les ressources allouées à un nœud"""
        return self.allocations.get(node_id)
    
    def get_all_allocations(self) -> Dict:
        """Retourne toutes les allocations"""
        return self.allocations
    
    def get_global_usage(self) -> Dict:
        """Retourne l'utilisation globale"""
        total_cpu = sum(alloc.get('cpu_cores', 0) for alloc in self.allocations.values())
        total_ram = sum(alloc.get('ram_mb', 0) for alloc in self.allocations.values())
        total_storage = sum(alloc.get('storage_mb', 0) for alloc in self.allocations.values())
        
        return {
            'total_cpu_cores': total_cpu,
            'total_ram_mb': total_ram,
            'total_storage_mb': total_storage,
            'nodes_with_allocations': len(self.allocations)
        }
    
    def cleanup_expired(self):
        """Nettoie les allocations expirées"""
        current_time = time.time()
        
        for node_id, node_alloc in list(self.allocations.items()):
            expired = [
                alloc for alloc in node_alloc['allocations']
                if alloc['expires_at'] <= current_time
            ]
            
            for alloc in expired:
                alloc_type = alloc['type']
                amount = alloc['amount']
                
                if alloc_type == 'cpu':
                    node_alloc['cpu_cores'] -= amount
                elif alloc_type == 'ram':
                    node_alloc['ram_mb'] -= amount
                elif alloc_type == 'storage':
                    node_alloc['storage_mb'] -= amount
                
                node_alloc['allocations'].remove(alloc)
            
            # Suppression des nœuds sans allocation
            if not node_alloc['allocations']:
                del self.allocations[node_id]


class HybridResourceManager:
    """Gestionnaire hybride PoW + PoM"""
    
    def __init__(self, allocator: ResourceAllocator):
        self.allocator = allocator
        
    async def process_pow_reward(self, node_id: str, reward: Dict):
        """Traite une récompense PoW"""
        cpu_cores = reward.get('cpu_cores', 0)
        duration = reward.get('duration', 3600)
        
        if cpu_cores > 0:
            success = await self.allocator.allocate_cpu(node_id, cpu_cores, duration)
            return success
        
        return False
    
    async def process_pom_reward(self, node_id: str, reward: Dict):
        """Traite une récompense PoM"""
        storage_mb = reward.get('storage_mb', 0)
        duration = reward.get('duration', 7200)
        
        if storage_mb > 0:
            success = await self.allocator.allocate_storage(node_id, storage_mb, duration)
            return success
        
        return False
    
    def get_node_power(self, node_id: str) -> Dict:
        """Calcule la "puissance" totale d'un nœud"""
        resources = self.allocator.get_node_resources(node_id)
        
        if not resources:
            return {'power_score': 0, 'resources': {}}
        
        # Calcul d'un score de puissance
        power_score = (
            resources.get('cpu_cores', 0) * 100 +
            resources.get('ram_mb', 0) / 1024 * 50 +
            resources.get('storage_mb', 0) / 1024 * 10
        )
        
        return {
            'power_score': power_score,
            'resources': resources
        }


async def test_allocator():
    """Test de l'allocateur"""
    print("=== Testing Resource Allocator ===\n")
    
    allocator = ResourceAllocator({
        'max_cpu_per_vm': 8,
        'max_ram_per_vm': 16384,
        'max_storage_per_vm': 102400
    })
    
    # Allocations CPU
    await allocator.allocate_cpu('node_001', 2, 10)
    await allocator.allocate_cpu('node_002', 4, 15)
    
    # Allocations RAM
    await allocator.allocate_ram('node_001', 4096, 10)
    
    # Allocations Storage
    await allocator.allocate_storage('node_003', 10240, 20)
    
    print("\n--- Current Allocations ---")
    for node_id, alloc in allocator.get_all_allocations().items():
        print(f"{node_id}: CPU={alloc['cpu_cores']}, RAM={alloc['ram_mb']}MB, Storage={alloc['storage_mb']}MB")
    
    print("\n--- Global Usage ---")
    usage = allocator.get_global_usage()
    for key, value in usage.items():
        print(f"{key}: {value}")
    
    # Attente expiration
    print("\n--- Waiting for expirations ---")
    await asyncio.sleep(12)
    
    print("\n--- Allocations After Expiration ---")
    for node_id, alloc in allocator.get_all_allocations().items():
        print(f"{node_id}: CPU={alloc['cpu_cores']}, RAM={alloc['ram_mb']}MB, Storage={alloc['storage_mb']}MB")


if __name__ == '__main__':
    asyncio.run(test_allocator())
