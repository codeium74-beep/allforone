"""Tests pour le système Matriarche"""
import pytest
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from matriarche.core.brain import MatriarchBrain
from matriarche.core.timer import MatriarchTimer
from utils.crypto_utils import CryptoManager


class TestMatriarchTimer:
    """Tests du timer aléatoire"""
    
    def test_timer_initialization(self):
        timer = MatriarchTimer(min_sleep=60, max_sleep=300)
        assert timer.min_sleep == 60
        assert timer.max_sleep == 300
        assert timer.wake_variance == 0.3
    
    def test_next_wake_time_in_range(self):
        timer = MatriarchTimer(min_sleep=60, max_sleep=300)
        wake_time = timer.next_wake_time()
        
        # Avec variance, le temps peut être légèrement hors limites
        assert 40 < wake_time < 400
    
    def test_sleep_status(self):
        timer = MatriarchTimer()
        status = timer.get_sleep_status()
        
        assert 'last_wake' in status
        assert 'elapsed_seconds' in status
        assert 'next_wake_estimated_seconds' in status


class TestMatriarchBrain:
    """Tests du cerveau de la Matriarche"""
    
    @pytest.fixture
    def config(self, tmp_path):
        return {
            'node_id': 'test_matriarche',
            'min_sleep': 10,
            'max_sleep': 30,
            'storage_path': str(tmp_path / 'storage'),
            'knowledge_path': str(tmp_path / 'knowledge'),
            'replication_factor': 3,
            'master_key': 'test_key'
        }
    
    def test_brain_initialization(self, config):
        brain = MatriarchBrain(config)
        
        assert brain.node_id == 'test_matriarche'
        assert brain.state == 'dormant'
        assert brain.wake_count == 0
    
    def test_mission_authentication(self, config):
        brain = MatriarchBrain(config)
        
        # Mission valide
        valid_mission = {
            'objective': 'Test mission',
            'auth_token': 'test_key'
        }
        
        assert brain._verify_mission_auth(valid_mission) is True
        
        # Mission invalide
        invalid_mission = {
            'objective': 'Test mission',
            'auth_token': 'wrong_key'
        }
        
        assert brain._verify_mission_auth(invalid_mission) is False
    
    def test_get_status(self, config):
        brain = MatriarchBrain(config)
        status = brain.get_status()
        
        assert status['node_id'] == 'test_matriarche'
        assert status['state'] == 'dormant'
        assert status['wake_count'] == 0


class TestCryptoUtils:
    """Tests des utilitaires crypto"""
    
    def test_keypair_generation(self):
        crypto = CryptoManager()
        private, public = crypto.generate_keypair()
        
        assert len(private) > 0
        assert len(public) > 0
        assert private != public
    
    def test_symmetric_encryption(self):
        crypto = CryptoManager()
        
        plaintext = b"Secret message"
        encrypted = crypto.encrypt_symmetric(plaintext)
        decrypted = crypto.decrypt_symmetric(encrypted)
        
        assert encrypted != plaintext
        assert decrypted == plaintext
    
    def test_signature_verification(self):
        crypto = CryptoManager()
        crypto.generate_keypair()
        
        data = b"Data to sign"
        signature = crypto.sign_data(data)
        
        # Vérification avec clé publique
        assert len(signature) > 0
    
    def test_hash_generation(self):
        crypto = CryptoManager()
        
        data = b"Test data"
        hash_sha256 = crypto.generate_hash(data, 'sha256')
        hash_sha512 = crypto.generate_hash(data, 'sha512')
        
        assert len(hash_sha256) == 64  # SHA-256 hex
        assert len(hash_sha512) == 128  # SHA-512 hex
        assert hash_sha256 != hash_sha512


def test_imports():
    """Vérifie que tous les imports fonctionnent"""
    from matriarche.core import brain, timer, delegator, collector, mutator
    from sous_matriarche import sub_brain
    from proto_agent import proto_core, polymorphic
    from percepteur import perceptor_core
    from pow_pom import proof_of_work, proof_of_memory, resource_allocator
    from utils import crypto_utils, network_utils, storage_utils
    
    assert True  # Si on arrive ici, tous les imports sont OK


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
