"""Proof of Memory pour allocation de stockage"""
import hashlib
import secrets
import time
import asyncio
from typing import Dict, List, Optional
import random


class ProofOfMemoryEngine:
    """Moteur PoM pour allocation de stockage"""
    
    def __init__(self):
        self.storage_challenges = []
        self.data_shards = {}
        self.allocations = []
        
    def issue_memory_challenge(self, reward: Dict = None) -> Dict:
        """Émet un challenge de stockage"""
        # Génération d'un shard de données
        shard_size = 5 * 1024 * 1024  # 5MB
        shard_id = secrets.token_hex(16)
        shard_data = secrets.token_bytes(shard_size)
        shard_hash = hashlib.sha256(shard_data).hexdigest()
        
        # Sélection d'indices aléatoires pour vérification
        verification_indices = random.sample(
            range(shard_size),
            k=min(100, shard_size)
        )
        
        challenge = {
            'challenge_id': secrets.token_hex(16),
            'shard_id': shard_id,
            'shard_data': shard_data,
            'shard_hash': shard_hash,
            'shard_size': shard_size,
            'verification_indices': verification_indices,
            'timestamp': time.time(),
            'timeout': 300,  # 5 minutes
            'reward': reward or {
                'storage_mb': 50,
                'duration': 7200,  # 2 heures
                'bandwidth_boost': 1.5
            }
        }
        
        self.storage_challenges.append(challenge)
        self.data_shards[shard_id] = shard_data
        
        print(f"[PoM] Storage challenge issued: {shard_id[:8]}... ({shard_size / 1024 / 1024:.2f}MB)")
        
        return challenge
    
    def verify_storage_proof(self, proof: Dict, challenge: Dict) -> bool:
        """Vérifie qu'un nœud stocke bien le shard"""
        node_id = proof.get('node_id')
        shard_id = proof.get('shard_id')
        
        # Vérification du challenge ID
        if shard_id != challenge['shard_id']:
            return False
        
        # Vérification timeout
        elapsed = time.time() - challenge['timestamp']
        if elapsed > challenge['timeout']:
            print(f"[PoM] Proof timeout: {elapsed:.2f}s")
            return False
        
        # Vérification des samples
        data_samples = proof.get('data_samples', {})
        
        if not data_samples:
            return False
        
        # Vérification de chaque sample
        original_shard = self.data_shards.get(shard_id)
        if not original_shard:
            return False
        
        for idx in challenge['verification_indices']:
            if str(idx) not in data_samples:
                print(f"[PoM] Missing sample at index {idx}")
                return False
            
            expected_byte = original_shard[idx]
            provided_byte = data_samples[str(idx)]
            
            if expected_byte != provided_byte:
                print(f"[PoM] Sample mismatch at index {idx}")
                return False
        
        # Vérification du hash partiel
        sample_data = b''.join(
            original_shard[i:i+1] for i in challenge['verification_indices']
        )
        expected_sample_hash = hashlib.sha256(sample_data).hexdigest()
        provided_hash = proof.get('sample_hash')
        
        if provided_hash != expected_sample_hash:
            print(f"[PoM] Sample hash mismatch")
            return False
        
        print(f"[PoM] Valid storage proof from {node_id}")
        
        # Allocation de la récompense
        self._allocate_storage_reward(node_id, challenge['reward'])
        
        return True
    
    def _allocate_storage_reward(self, node_id: str, reward: Dict):
        """Alloue le stockage au nœud gagnant"""
        print(f"[PoM] Allocating storage to {node_id}:")
        print(f"  - Storage: +{reward['storage_mb']}MB")
        print(f"  - Duration: {reward['duration']}s")
        print(f"  - Bandwidth boost: {reward.get('bandwidth_boost', 1.0)}x")
        
        allocation = {
            'node_id': node_id,
            'reward': reward,
            'allocated_at': time.time(),
            'expires_at': time.time() + reward['duration']
        }
        
        self.allocations.append(allocation)
    
    def get_active_allocations(self) -> List[Dict]:
        """Retourne les allocations actives"""
        current_time = time.time()
        
        active = [
            alloc for alloc in self.allocations
            if alloc['expires_at'] > current_time
        ]
        
        return active
    
    def cleanup_expired_allocations(self):
        """Nettoie les allocations expirées"""
        current_time = time.time()
        
        expired = [
            alloc for alloc in self.allocations
            if alloc['expires_at'] <= current_time
        ]
        
        for alloc in expired:
            print(f"[PoM] Storage allocation expired for {alloc['node_id']}")
            self.allocations.remove(alloc)
    
    def cleanup_old_shards(self, max_age: int = 3600):
        """Nettoie les anciens shards"""
        current_time = time.time()
        
        for challenge in list(self.storage_challenges):
            age = current_time - challenge['timestamp']
            if age > max_age:
                shard_id = challenge['shard_id']
                if shard_id in self.data_shards:
                    del self.data_shards[shard_id]
                self.storage_challenges.remove(challenge)


class StorageNode:
    """Nœud participant au PoM"""
    
    def __init__(self, node_id: str):
        self.node_id = node_id
        self.stored_shards = {}
        
    async def store_challenge_data(self, challenge: Dict) -> Dict:
        """Stocke les données du challenge"""
        shard_id = challenge['shard_id']
        shard_data = challenge['shard_data']
        
        print(f"[Storage-{self.node_id}] Storing shard {shard_id[:8]}...")
        
        # Simulation de compression
        await asyncio.sleep(0.1)  # Simule temps d'écriture
        
        # Stockage en mémoire (dans un vrai système: sur disque)
        self.stored_shards[shard_id] = shard_data
        
        print(f"[Storage-{self.node_id}] Shard stored successfully")
        
        return await self._prepare_proof(challenge)
    
    async def _prepare_proof(self, challenge: Dict) -> Dict:
        """Prépare la preuve de stockage"""
        shard_id = challenge['shard_id']
        shard_data = self.stored_shards.get(shard_id)
        
        if not shard_data:
            return None
        
        # Extraction des samples demandés
        verification_indices = challenge['verification_indices']
        samples = {
            str(idx): shard_data[idx]
            for idx in verification_indices
        }
        
        # Calcul du hash des samples
        sample_data = b''.join(
            shard_data[i:i+1] for i in verification_indices
        )
        sample_hash = hashlib.sha256(sample_data).hexdigest()
        
        proof = {
            'node_id': self.node_id,
            'shard_id': shard_id,
            'data_samples': samples,
            'sample_hash': sample_hash,
            'timestamp': time.time()
        }
        
        return proof
    
    def get_storage_usage(self) -> Dict:
        """Retourne l'utilisation du stockage"""
        total_bytes = sum(len(data) for data in self.stored_shards.values())
        
        return {
            'node_id': self.node_id,
            'shards_count': len(self.stored_shards),
            'total_bytes': total_bytes,
            'total_mb': total_bytes / 1024 / 1024
        }


class DistributedPoMCoordinator:
    """Coordinateur distribué pour PoM"""
    
    def __init__(self, node_ids: List[str]):
        self.engine = ProofOfMemoryEngine()
        self.storage_nodes = {
            node_id: StorageNode(node_id) 
            for node_id in node_ids
        }
        
    async def run_challenge_cycle(self):
        """Exécute un cycle de challenge PoM"""
        # Émission du challenge
        challenge = self.engine.issue_memory_challenge()
        
        # Sélection des participants
        num_participants = int(len(self.storage_nodes) * random.uniform(0.3, 0.5))
        selected_nodes = random.sample(
            list(self.storage_nodes.values()),
            num_participants
        )
        
        print(f"[PoMCoordinator] {num_participants} storage nodes selected")
        
        # Distribution et stockage du shard
        storage_tasks = [
            node.store_challenge_data(challenge)
            for node in selected_nodes
        ]
        
        proofs = await asyncio.gather(*storage_tasks)
        
        # Validation des preuves
        valid_proofs = []
        for proof in proofs:
            if proof and self.engine.verify_storage_proof(proof, challenge):
                valid_proofs.append(proof)
        
        print(f"[PoMCoordinator] {len(valid_proofs)} valid proofs received")
        
        # Sélection d'un gagnant aléatoire parmi les valides
        if valid_proofs:
            winner = random.choice(valid_proofs)
            print(f"[PoMCoordinator] Winner: {winner['node_id']}")
    
    def get_stats(self) -> Dict:
        """Statistiques du système PoM"""
        total_storage = sum(
            node.get_storage_usage()['total_mb']
            for node in self.storage_nodes.values()
        )
        
        return {
            'total_challenges': len(self.engine.storage_challenges),
            'active_allocations': len(self.engine.get_active_allocations()),
            'registered_nodes': len(self.storage_nodes),
            'total_storage_mb': total_storage
        }
    
    async def cleanup_cycle(self):
        """Cycle de nettoyage"""
        self.engine.cleanup_expired_allocations()
        self.engine.cleanup_old_shards()


async def test_pom():
    """Test du système PoM"""
    print("=== Testing Proof of Memory System ===\n")
    
    # Création des nœuds de stockage
    node_ids = [f'storage_{i:03d}' for i in range(8)]
    coordinator = DistributedPoMCoordinator(node_ids)
    
    # Exécution de quelques cycles
    for cycle in range(3):
        print(f"\n--- Cycle {cycle + 1} ---")
        await coordinator.run_challenge_cycle()
        await asyncio.sleep(2)
    
    # Nettoyage
    await coordinator.cleanup_cycle()
    
    # Affichage des stats
    print("\n=== Final Stats ===")
    stats = coordinator.get_stats()
    for key, value in stats.items():
        print(f"{key}: {value}")


if __name__ == '__main__':
    asyncio.run(test_pom())
