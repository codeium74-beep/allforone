"""Proof of Work pour allocation CPU/GPU"""
import hashlib
import time
import secrets
import asyncio
from typing import Dict, List, Optional


class ProofOfWorkEngine:
    """Moteur PoW pour allocation de ressources CPU"""
    
    def __init__(self):
        self.current_challenge = None
        self.difficulty = 4  # Nombre de zéros requis au début du hash
        self.participants = []
        self.challenge_history = []
        
    def issue_challenge(self, reward: Dict = None) -> Optional[Dict]:
        """Émet un challenge PoW aléatoirement"""
        # Probabilité d'émission: 30%
        if random.random() > 0.7:
            return None
        
        # Génération du challenge
        challenge = {
            'challenge_id': secrets.token_hex(16),
            'nonce_target': secrets.token_hex(32),
            'difficulty': self.difficulty,
            'timestamp': time.time(),
            'timeout': 60,  # 60 secondes pour résoudre
            'reward': reward or {
                'cpu_cores': 2,
                'duration': 3600,  # 1 heure
                'priority_boost': 1.5
            }
        }
        
        self.current_challenge = challenge
        self.challenge_history.append(challenge)
        
        print(f"[PoW] Challenge issued: {challenge['challenge_id'][:8]}... (difficulty: {self.difficulty})")
        
        return challenge
    
    def validate_solution(self, solution: Dict, submitter_id: str) -> bool:
        """Valide une solution PoW"""
        if not self.current_challenge:
            return False
        
        challenge_id = solution.get('challenge_id')
        nonce = solution.get('nonce')
        
        # Vérification du challenge ID
        if challenge_id != self.current_challenge['challenge_id']:
            return False
        
        # Vérification timeout
        elapsed = time.time() - self.current_challenge['timestamp']
        if elapsed > self.current_challenge['timeout']:
            print(f"[PoW] Solution timeout: {elapsed:.2f}s")
            return False
        
        # Calcul et vérification du hash
        target = self.current_challenge['nonce_target']
        computed_hash = hashlib.sha256(f"{target}{nonce}".encode()).hexdigest()
        
        required_prefix = '0' * self.current_challenge['difficulty']
        
        if computed_hash.startswith(required_prefix):
            print(f"[PoW] Valid solution from {submitter_id}: {computed_hash[:16]}...")
            print(f"[PoW] Time to solve: {elapsed:.2f}s")
            
            # Allocation de la récompense
            self._allocate_reward(submitter_id, self.current_challenge['reward'])
            
            # Réinitialisation du challenge
            self.current_challenge = None
            
            return True
        
        return False
    
    def _allocate_reward(self, node_id: str, reward: Dict):
        """Alloue la récompense au gagnant"""
        print(f"[PoW] Allocating reward to {node_id}:")
        print(f"  - CPU cores: +{reward['cpu_cores']}")
        print(f"  - Duration: {reward['duration']}s")
        print(f"  - Priority boost: {reward.get('priority_boost', 1.0)}x")
        
        # Note: L'allocation réelle nécessiterait API Proxmox
        # Ici: enregistrement de l'allocation
        allocation = {
            'node_id': node_id,
            'reward': reward,
            'allocated_at': time.time(),
            'expires_at': time.time() + reward['duration']
        }
        
        # Stockage pour tracking
        self.participants.append(allocation)
    
    def adjust_difficulty(self, avg_solve_time: float):
        """Ajuste la difficulté dynamiquement"""
        target_time = 30  # Temps cible: 30 secondes
        
        if avg_solve_time < target_time * 0.5:
            # Trop rapide, augmente difficulté
            self.difficulty += 1
            print(f"[PoW] Difficulty increased to {self.difficulty}")
        elif avg_solve_time > target_time * 2:
            # Trop lent, diminue difficulté
            self.difficulty = max(1, self.difficulty - 1)
            print(f"[PoW] Difficulty decreased to {self.difficulty}")
    
    def get_active_allocations(self) -> List[Dict]:
        """Retourne les allocations actives"""
        current_time = time.time()
        
        active = [
            alloc for alloc in self.participants
            if alloc['expires_at'] > current_time
        ]
        
        return active
    
    def cleanup_expired_allocations(self):
        """Nettoie les allocations expirées"""
        current_time = time.time()
        
        expired = [
            alloc for alloc in self.participants
            if alloc['expires_at'] <= current_time
        ]
        
        for alloc in expired:
            print(f"[PoW] Allocation expired for {alloc['node_id']}")
            self.participants.remove(alloc)


class PoWMiner:
    """Mineur PoW pour les nœuds participants"""
    
    def __init__(self, node_id: str):
        self.node_id = node_id
        self.mining = False
        
    async def solve_challenge(self, challenge: Dict) -> Optional[Dict]:
        """Résout un challenge PoW"""
        print(f"[Miner-{self.node_id}] Starting to solve challenge...")
        
        target = challenge['nonce_target']
        difficulty = challenge['difficulty']
        timeout = challenge['timeout']
        required_prefix = '0' * difficulty
        
        self.mining = True
        start_time = time.time()
        nonce = 0
        
        while self.mining and (time.time() - start_time) < timeout:
            # Calcul du hash
            candidate_hash = hashlib.sha256(
                f"{target}{nonce}".encode()
            ).hexdigest()
            
            # Vérification
            if candidate_hash.startswith(required_prefix):
                solve_time = time.time() - start_time
                print(f"[Miner-{self.node_id}] Solution found! Nonce: {nonce}, Time: {solve_time:.2f}s")
                
                return {
                    'challenge_id': challenge['challenge_id'],
                    'nonce': str(nonce),
                    'hash': candidate_hash,
                    'solver': self.node_id,
                    'solve_time': solve_time
                }
            
            nonce += 1
            
            # Yield périodiquement pour ne pas bloquer
            if nonce % 10000 == 0:
                await asyncio.sleep(0.001)
        
        print(f"[Miner-{self.node_id}] Failed to solve in time")
        return None
    
    def stop_mining(self):
        """Arrête le mining"""
        self.mining = False


# Import manquant
import random


class DistributedPoWCoordinator:
    """Coordinateur distribué pour PoW"""
    
    def __init__(self, node_ids: List[str]):
        self.engine = ProofOfWorkEngine()
        self.miners = {node_id: PoWMiner(node_id) for node_id in node_ids}
        self.active_challenges = {}
        
    async def run_challenge_cycle(self):
        """Exécute un cycle de challenge"""
        # Émission du challenge
        challenge = self.engine.issue_challenge()
        
        if not challenge:
            print("[PoWCoordinator] No challenge issued this cycle")
            return
        
        # Sélection des participants (30-50%)
        num_participants = int(len(self.miners) * random.uniform(0.3, 0.5))
        selected_miners = random.sample(list(self.miners.values()), num_participants)
        
        print(f"[PoWCoordinator] {num_participants} miners selected")
        
        # Lancement parallèle du mining
        tasks = [
            miner.solve_challenge(challenge)
            for miner in selected_miners
        ]
        
        # Attente de la première solution
        done, pending = await asyncio.wait(
            tasks,
            return_when=asyncio.FIRST_COMPLETED
        )
        
        # Arrêt des autres mineurs
        for miner in selected_miners:
            miner.stop_mining()
        
        # Validation de la solution
        for task in done:
            solution = task.result()
            if solution:
                valid = self.engine.validate_solution(
                    solution,
                    solution['solver']
                )
                
                if valid:
                    print(f"[PoWCoordinator] Winner: {solution['solver']}")
                    break
        
        # Annulation des tâches en attente
        for task in pending:
            task.cancel()
    
    def get_stats(self) -> Dict:
        """Statistiques du système PoW"""
        return {
            'total_challenges': len(self.engine.challenge_history),
            'active_allocations': len(self.engine.get_active_allocations()),
            'current_difficulty': self.engine.difficulty,
            'registered_miners': len(self.miners)
        }


async def test_pow():
    """Test du système PoW"""
    print("=== Testing Proof of Work System ===\n")
    
    # Création des mineurs
    node_ids = [f'node_{i:03d}' for i in range(10)]
    coordinator = DistributedPoWCoordinator(node_ids)
    
    # Exécution de quelques cycles
    for cycle in range(3):
        print(f"\n--- Cycle {cycle + 1} ---")
        await coordinator.run_challenge_cycle()
        await asyncio.sleep(2)
    
    # Affichage des stats
    print("\n=== Final Stats ===")
    stats = coordinator.get_stats()
    for key, value in stats.items():
        print(f"{key}: {value}")


if __name__ == '__main__':
    asyncio.run(test_pow())
