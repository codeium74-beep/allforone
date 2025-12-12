"""Utilitaires cryptographiques pour communications sécurisées"""
import hashlib
import secrets
import base64
from typing import Tuple, Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization


class CryptoManager:
    """Gestion des opérations cryptographiques"""
    
    def __init__(self):
        self.symmetric_key = Fernet.generate_key()
        self.fernet = Fernet(self.symmetric_key)
        self._private_key = None
        self._public_key = None
        
    def generate_keypair(self) -> Tuple[bytes, bytes]:
        """Génère une paire de clés RSA"""
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        public_key = private_key.public_key()
        
        self._private_key = private_key
        self._public_key = public_key
        
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        return private_pem, public_pem
    
    def encrypt_symmetric(self, data: bytes) -> bytes:
        """Chiffrement symétrique rapide"""
        return self.fernet.encrypt(data)
    
    def decrypt_symmetric(self, encrypted_data: bytes) -> bytes:
        """Déchiffrement symétrique"""
        return self.fernet.decrypt(encrypted_data)
    
    def encrypt_asymmetric(self, data: bytes, public_key_pem: bytes) -> bytes:
        """Chiffrement asymétrique avec clé publique"""
        public_key = serialization.load_pem_public_key(public_key_pem)
        
        encrypted = public_key.encrypt(
            data,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return encrypted
    
    def decrypt_asymmetric(self, encrypted_data: bytes) -> bytes:
        """Déchiffrement asymétrique avec clé privée"""
        if not self._private_key:
            raise ValueError("Private key not initialized")
        
        decrypted = self._private_key.decrypt(
            encrypted_data,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return decrypted
    
    def sign_data(self, data: bytes) -> bytes:
        """Signe des données avec la clé privée"""
        if not self._private_key:
            raise ValueError("Private key not initialized")
        
        signature = self._private_key.sign(
            data,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return signature
    
    def verify_signature(self, data: bytes, signature: bytes, 
                        public_key_pem: bytes) -> bool:
        """Vérifie une signature avec une clé publique"""
        try:
            public_key = serialization.load_pem_public_key(public_key_pem)
            public_key.verify(
                signature,
                data,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return True
        except Exception:
            return False
    
    @staticmethod
    def generate_hash(data: bytes, algorithm: str = 'sha256') -> str:
        """Génère un hash des données"""
        if algorithm == 'sha256':
            return hashlib.sha256(data).hexdigest()
        elif algorithm == 'sha512':
            return hashlib.sha512(data).hexdigest()
        elif algorithm == 'blake2b':
            return hashlib.blake2b(data).hexdigest()
        else:
            raise ValueError(f"Unknown algorithm: {algorithm}")
    
    @staticmethod
    def generate_nonce(length: int = 32) -> str:
        """Génère un nonce aléatoire"""
        return secrets.token_hex(length)
    
    @staticmethod
    def generate_uuid() -> str:
        """Génère un UUID unique"""
        import uuid
        return str(uuid.uuid4())


def obfuscate_string(s: str, key: Optional[bytes] = None) -> str:
    """Obfuscation simple de chaîne"""
    if key is None:
        key = secrets.token_bytes(16)
    
    result = bytearray()
    for i, char in enumerate(s.encode()):
        result.append(char ^ key[i % len(key)])
    
    return base64.b64encode(bytes(result)).decode()


def deobfuscate_string(obfuscated: str, key: bytes) -> str:
    """Désobfuscation de chaîne"""
    data = base64.b64decode(obfuscated.encode())
    
    result = bytearray()
    for i, byte in enumerate(data):
        result.append(byte ^ key[i % len(key)])
    
    return bytes(result).decode()
