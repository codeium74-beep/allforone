"""Utilitaires réseau pour découverte et communication P2P"""
import socket
import struct
import asyncio
import json
import random
from typing import Dict, List, Optional, Tuple
from zeroconf import ServiceBrowser, ServiceInfo, Zeroconf
import time


class P2PDiscovery:
    """Service de découverte P2P via mDNS/Zeroconf"""
    
    def __init__(self, service_type: str = "_matriarche._tcp.local."):
        self.service_type = service_type
        self.zeroconf = Zeroconf()
        self.discovered_peers = {}
        self.own_service_info = None
        
    def register_service(self, name: str, port: int, properties: Dict = None):
        """Enregistre ce nœud comme service découvrable"""
        if properties is None:
            properties = {}
        
        # Conversion des propriétés en bytes
        props = {k: str(v).encode('utf-8') for k, v in properties.items()}
        
        info = ServiceInfo(
            self.service_type,
            f"{name}.{self.service_type}",
            addresses=[socket.inet_aton(self._get_local_ip())],
            port=port,
            properties=props,
            server=f"{name}.local."
        )
        
        self.zeroconf.register_service(info)
        self.own_service_info = info
        
    def discover_peers(self, timeout: float = 5.0) -> List[Dict]:
        """Découvre les pairs disponibles"""
        listener = ServiceListener(self.discovered_peers)
        browser = ServiceBrowser(self.zeroconf, self.service_type, listener)
        
        time.sleep(timeout)
        browser.cancel()
        
        return list(self.discovered_peers.values())
    
    def unregister_service(self):
        """Désenregistre le service"""
        if self.own_service_info:
            self.zeroconf.unregister_service(self.own_service_info)
    
    def close(self):
        """Ferme le service Zeroconf"""
        self.zeroconf.close()
    
    @staticmethod
    def _get_local_ip() -> str:
        """Obtient l'IP locale"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"


class ServiceListener:
    """Listener pour les services découverts"""
    
    def __init__(self, discovered_peers: Dict):
        self.discovered_peers = discovered_peers
    
    def add_service(self, zeroconf: Zeroconf, service_type: str, name: str):
        """Appelé quand un service est découvert"""
        info = zeroconf.get_service_info(service_type, name)
        if info:
            self.discovered_peers[name] = {
                'name': name,
                'addresses': [socket.inet_ntoa(addr) for addr in info.addresses],
                'port': info.port,
                'properties': {k: v.decode('utf-8') for k, v in info.properties.items()}
            }
    
    def remove_service(self, zeroconf: Zeroconf, service_type: str, name: str):
        """Appelé quand un service disparaît"""
        if name in self.discovered_peers:
            del self.discovered_peers[name]
    
    def update_service(self, zeroconf: Zeroconf, service_type: str, name: str):
        """Appelé quand un service est mis à jour"""
        self.add_service(zeroconf, service_type, name)


class MulticastBeacon:
    """Système de beacon multicast pour découverte rapide"""
    
    MULTICAST_GROUP = '224.0.0.251'
    MULTICAST_PORT = 5353
    
    def __init__(self, node_id: str, node_type: str):
        self.node_id = node_id
        self.node_type = node_type
        self.sock = None
        
    def start_broadcasting(self, interval: float = 30.0):
        """Commence à broadcaster des beacons"""
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
        
        while True:
            beacon = self._create_beacon()
            self.sock.sendto(beacon, (self.MULTICAST_GROUP, self.MULTICAST_PORT))
            
            # Intervalle aléatoire pour stealth
            sleep_time = interval * random.uniform(0.7, 1.3)
            time.sleep(sleep_time)
    
    def listen_for_beacons(self, timeout: float = 10.0) -> List[Dict]:
        """Écoute les beacons d'autres nœuds"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('', self.MULTICAST_PORT))
        
        mreq = struct.pack("4sl", socket.inet_aton(self.MULTICAST_GROUP), socket.INADDR_ANY)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        sock.settimeout(timeout)
        
        discovered = []
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                data, addr = sock.recvfrom(1024)
                beacon_data = json.loads(data.decode('utf-8'))
                
                if beacon_data['node_id'] != self.node_id:
                    beacon_data['source_ip'] = addr[0]
                    discovered.append(beacon_data)
            except socket.timeout:
                break
            except Exception as e:
                continue
        
        sock.close()
        return discovered
    
    def _create_beacon(self) -> bytes:
        """Crée un message beacon"""
        beacon = {
            'node_id': self.node_id,
            'node_type': self.node_type,
            'timestamp': time.time(),
            'version': '1.0'
        }
        return json.dumps(beacon).encode('utf-8')


class StealthCommunicator:
    """Communicateur avec obfuscation du trafic"""
    
    def __init__(self, crypto_manager):
        self.crypto = crypto_manager
        self.junk_ratio = 0.2  # 20% de données inutiles
        
    async def send_stealth(self, data: bytes, host: str, port: int):
        """Envoie des données avec obfuscation"""
        # Chiffrement
        encrypted = self.crypto.encrypt_symmetric(data)
        
        # Ajout de junk data
        payload = self._add_junk_data(encrypted)
        
        # Fragmentation aléatoire
        fragments = self._fragment_data(payload)
        
        # Envoi avec délais aléatoires
        reader, writer = await asyncio.open_connection(host, port)
        
        for fragment in fragments:
            writer.write(fragment)
            await writer.drain()
            
            # Délai aléatoire entre fragments (100-500ms)
            await asyncio.sleep(random.uniform(0.1, 0.5))
        
        writer.close()
        await writer.wait_closed()
    
    async def receive_stealth(self, reader: asyncio.StreamReader) -> bytes:
        """Reçoit et désobfuscate des données"""
        # Réassemblage
        payload = await reader.read()
        
        # Retrait du junk
        cleaned = self._remove_junk_data(payload)
        
        # Déchiffrement
        decrypted = self.crypto.decrypt_symmetric(cleaned)
        
        return decrypted
    
    def _add_junk_data(self, data: bytes) -> bytes:
        """Ajoute des données inutiles pour obfuscation"""
        junk_size = int(len(data) * self.junk_ratio)
        junk = secrets.token_bytes(junk_size)
        
        # Insertion aléatoire du junk
        result = bytearray()
        data_pos = 0
        junk_pos = 0
        
        # Header: taille des vraies données
        result.extend(len(data).to_bytes(4, 'big'))
        
        while data_pos < len(data) or junk_pos < len(junk):
            if random.random() > self.junk_ratio and data_pos < len(data):
                result.append(data[data_pos])
                data_pos += 1
            elif junk_pos < len(junk):
                result.append(junk[junk_pos])
                junk_pos += 1
        
        return bytes(result)
    
    def _remove_junk_data(self, payload: bytes) -> bytes:
        """Retire les données inutiles"""
        # Lecture taille vraies données
        data_size = int.from_bytes(payload[:4], 'big')
        
        # Extraction données (simple: prendre les N premiers octets après header)
        # Note: version simplifiée, à améliorer avec marqueurs
        return payload[4:4+data_size]
    
    def _fragment_data(self, data: bytes, 
                      min_size: int = 512, 
                      max_size: int = 4096) -> List[bytes]:
        """Fragment les données en morceaux aléatoires"""
        fragments = []
        pos = 0
        
        while pos < len(data):
            fragment_size = random.randint(min_size, max_size)
            fragment_size = min(fragment_size, len(data) - pos)
            
            fragments.append(data[pos:pos+fragment_size])
            pos += fragment_size
        
        return fragments


def get_random_port(min_port: int = 10000, max_port: int = 65000) -> int:
    """Génère un port aléatoire disponible"""
    while True:
        port = random.randint(min_port, max_port)
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(('', port))
            sock.close()
            return port
        except OSError:
            continue
