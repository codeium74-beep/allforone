"""Module de scanning Nmap - VRAI SCAN RÉSEAU"""
import nmap
import socket
import time
import logging
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class NmapScanner:
    """Scanner réseau utilisant Nmap pour reconnaissance réelle"""
    
    def __init__(self):
        """Initialise le scanner Nmap"""
        self.nm = nmap.PortScanner()
        self.scan_history = []
        
    def scan_network(self, target_range: str, scan_type: str = 'fast') -> Dict:
        """
        Scan une plage réseau complète
        
        Args:
            target_range: Plage IP (ex: "192.168.1.0/24", "192.168.1.1-10")
            scan_type: Type de scan - 'fast', 'normal', 'thorough'
            
        Returns:
            Dict avec résultats structurés:
            {
                "192.168.1.10": {
                    "state": "up",
                    "ports": [
                        {"port": 22, "state": "open", "service": "ssh", "version": "OpenSSH 8.2"},
                        ...
                    ],
                    "os": ["Linux 5.4", "Ubuntu 20.04"],
                    "scan_time": 1734089234,
                    "hostname": "server.local"
                }
            }
        """
        logger.info(f"[NmapScanner] Starting {scan_type} scan of {target_range}")
        
        # Sélection des arguments selon type de scan
        scan_args = self._get_scan_arguments(scan_type)
        
        try:
            start_time = time.time()
            
            # Exécution du scan
            self.nm.scan(hosts=target_range, arguments=scan_args)
            
            scan_duration = time.time() - start_time
            
            # Extraction et structuration des résultats
            results = {}
            
            for host in self.nm.all_hosts():
                host_info = self._extract_host_info(host)
                if host_info:
                    results[host] = host_info
            
            # Enregistrement dans l'historique
            self.scan_history.append({
                'target': target_range,
                'type': scan_type,
                'timestamp': time.time(),
                'duration': scan_duration,
                'hosts_found': len(results)
            })
            
            logger.info(f"[NmapScanner] Scan completed: {len(results)} hosts found in {scan_duration:.2f}s")
            
            return results
            
        except Exception as e:
            logger.error(f"[NmapScanner] Scan failed: {e}")
            return {}
    
    def scan_single_host(self, ip: str, ports: Optional[List[int]] = None) -> Dict:
        """
        Scan un hôte spécifique
        
        Args:
            ip: Adresse IP de l'hôte
            ports: Liste de ports à scanner (None = ports communs)
            
        Returns:
            Dict avec informations détaillées sur l'hôte
        """
        logger.info(f"[NmapScanner] Scanning single host {ip}")
        
        try:
            # Construction de la liste de ports
            if ports:
                port_range = ','.join(map(str, ports))
            else:
                # Ports communs par défaut
                port_range = '21,22,23,25,53,80,110,111,135,139,143,443,445,993,995,1723,3306,3389,5900,8080'
            
            # Scan avec détection de version
            self.nm.scan(hosts=ip, ports=port_range, arguments='-sV -sC')
            
            if ip in self.nm.all_hosts():
                return self._extract_host_info(ip)
            else:
                logger.warning(f"[NmapScanner] Host {ip} not reachable or no results")
                return {}
                
        except Exception as e:
            logger.error(f"[NmapScanner] Single host scan failed: {e}")
            return {}
    
    def aggressive_scan(self, ip: str) -> Dict:
        """
        Scan agressif avec détection OS, version, scripts
        
        Args:
            ip: Adresse IP cible
            
        Returns:
            Dict avec informations complètes (OS, services, vulns détectées)
        """
        logger.info(f"[NmapScanner] Aggressive scan of {ip}")
        
        try:
            # Scan agressif: -A (OS + version + scripts + traceroute)
            self.nm.scan(hosts=ip, arguments='-A -T4')
            
            if ip in self.nm.all_hosts():
                host_info = self._extract_host_info(ip)
                
                # Ajout d'informations spécifiques au scan agressif
                host_info['scan_type'] = 'aggressive'
                host_info['traceroute'] = self._extract_traceroute(ip)
                host_info['script_results'] = self._extract_script_results(ip)
                
                return host_info
            else:
                return {}
                
        except Exception as e:
            logger.error(f"[NmapScanner] Aggressive scan failed: {e}")
            return {}
    
    def stealth_scan(self, ip: str) -> Dict:
        """
        Scan furtif (SYN scan) avec timing lent
        
        Args:
            ip: Adresse IP cible
            
        Returns:
            Dict avec résultats minimaux (ports ouverts)
        """
        logger.info(f"[NmapScanner] Stealth scan of {ip}")
        
        try:
            # SYN scan avec timing T2 (polite) pour éviter détection
            # -sS: SYN scan, -T2: timing polite, -Pn: skip ping
            self.nm.scan(hosts=ip, arguments='-sS -T2 -Pn')
            
            if ip in self.nm.all_hosts():
                # Extraction minimale pour rester furtif
                host_info = {
                    'ip': ip,
                    'state': self.nm[ip].state(),
                    'ports': self._extract_ports(ip),
                    'scan_time': time.time(),
                    'scan_type': 'stealth'
                }
                
                return host_info
            else:
                return {}
                
        except Exception as e:
            logger.error(f"[NmapScanner] Stealth scan failed: {e}")
            return {}
    
    def _get_scan_arguments(self, scan_type: str) -> str:
        """
        Retourne les arguments Nmap selon le type de scan
        
        Args:
            scan_type: 'fast', 'normal', 'thorough'
            
        Returns:
            Arguments Nmap
        """
        scan_profiles = {
            'fast': '-sS -T4 -F',  # SYN scan rapide, 100 ports communs
            'normal': '-sV -sC -T4',  # Version + scripts standards
            'thorough': '-sV -sC -O -T3 -p-'  # Tous ports + OS + version
        }
        
        return scan_profiles.get(scan_type, scan_profiles['fast'])
    
    def _extract_host_info(self, host: str) -> Dict:
        """
        Extrait toutes les informations d'un hôte scanné
        
        Args:
            host: IP de l'hôte
            
        Returns:
            Dict structuré avec toutes les infos
        """
        try:
            host_data = self.nm[host]
            
            info = {
                'ip': host,
                'state': host_data.state(),
                'ports': self._extract_ports(host),
                'os': self._parse_os_detection(host),
                'hostname': host_data.hostname() if host_data.hostname() else 'unknown',
                'scan_time': time.time()
            }
            
            return info
            
        except Exception as e:
            logger.error(f"[NmapScanner] Failed to extract host info for {host}: {e}")
            return {}
    
    def _extract_ports(self, host: str) -> List[Dict]:
        """
        Extrait les informations de tous les ports d'un hôte
        
        Args:
            host: IP de l'hôte
            
        Returns:
            Liste de dicts avec infos de chaque port
        """
        ports_info = []
        
        try:
            for proto in self.nm[host].all_protocols():
                port_list = self.nm[host][proto].keys()
                
                for port in port_list:
                    port_data = self.nm[host][proto][port]
                    
                    port_info = {
                        'port': port,
                        'protocol': proto,
                        'state': port_data['state'],
                        'service': port_data.get('name', 'unknown'),
                        'product': port_data.get('product', ''),
                        'version': port_data.get('version', ''),
                        'extrainfo': port_data.get('extrainfo', ''),
                        'cpe': port_data.get('cpe', '')
                    }
                    
                    ports_info.append(port_info)
            
            return ports_info
            
        except Exception as e:
            logger.error(f"[NmapScanner] Failed to extract ports for {host}: {e}")
            return []
    
    def _parse_os_detection(self, host: str) -> List[str]:
        """
        Parse les résultats de détection OS
        
        Args:
            host: IP de l'hôte
            
        Returns:
            Liste des OS possibles
        """
        os_list = []
        
        try:
            if 'osmatch' in self.nm[host]:
                for osmatch in self.nm[host]['osmatch']:
                    os_name = osmatch.get('name', '')
                    accuracy = osmatch.get('accuracy', '0')
                    
                    if int(accuracy) > 80:  # Seulement haute confiance
                        os_list.append(f"{os_name} ({accuracy}%)")
            
            return os_list
            
        except Exception as e:
            logger.error(f"[NmapScanner] Failed to parse OS for {host}: {e}")
            return []
    
    def _extract_traceroute(self, host: str) -> List[Dict]:
        """
        Extrait les informations de traceroute
        
        Args:
            host: IP de l'hôte
            
        Returns:
            Liste de hops avec IP et RTT
        """
        traceroute = []
        
        try:
            if 'trace' in self.nm[host]:
                for hop in self.nm[host]['trace']:
                    traceroute.append({
                        'hop': hop.get('hop', 0),
                        'ip': hop.get('ipaddr', ''),
                        'rtt': hop.get('rtt', ''),
                        'hostname': hop.get('host', '')
                    })
            
            return traceroute
            
        except Exception as e:
            logger.error(f"[NmapScanner] Failed to extract traceroute: {e}")
            return []
    
    def _extract_script_results(self, host: str) -> Dict:
        """
        Extrait les résultats des scripts NSE
        
        Args:
            host: IP de l'hôte
            
        Returns:
            Dict avec résultats des scripts
        """
        scripts = {}
        
        try:
            for proto in self.nm[host].all_protocols():
                for port in self.nm[host][proto].keys():
                    port_data = self.nm[host][proto][port]
                    
                    if 'script' in port_data:
                        for script_name, script_output in port_data['script'].items():
                            scripts[f"{port}/{script_name}"] = script_output
            
            return scripts
            
        except Exception as e:
            logger.error(f"[NmapScanner] Failed to extract scripts: {e}")
            return {}
    
    def check_port_open(self, ip: str, port: int, protocol: str = 'tcp') -> bool:
        """
        Vérifie rapidement si un port est ouvert
        
        Args:
            ip: Adresse IP
            port: Numéro de port
            protocol: 'tcp' ou 'udp'
            
        Returns:
            True si ouvert, False sinon
        """
        try:
            if protocol == 'tcp':
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                result = sock.connect_ex((ip, port))
                sock.close()
                return result == 0
            else:
                # UDP check plus complexe
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.settimeout(2)
                try:
                    sock.sendto(b'test', (ip, port))
                    sock.recvfrom(1024)
                    sock.close()
                    return True
                except:
                    sock.close()
                    return False
                    
        except Exception as e:
            logger.error(f"[NmapScanner] Port check failed: {e}")
            return False
    
    def get_scan_history(self) -> List[Dict]:
        """
        Retourne l'historique des scans effectués
        
        Returns:
            Liste des scans précédents
        """
        return self.scan_history
    
    def clear_history(self):
        """Efface l'historique des scans"""
        self.scan_history = []
        logger.info("[NmapScanner] Scan history cleared")


# Fonction utilitaire pour tests rapides
def quick_scan(target: str) -> Dict:
    """
    Fonction utilitaire pour scan rapide
    
    Args:
        target: IP ou plage IP
        
    Returns:
        Résultats du scan
    """
    scanner = NmapScanner()
    return scanner.scan_network(target, 'fast')


if __name__ == '__main__':
    # Test du scanner
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python nmap_scanner.py <target>")
        print("Example: python nmap_scanner.py 192.168.1.0/24")
        sys.exit(1)
    
    target = sys.argv[1]
    
    print(f"\n[*] Starting Nmap scan of {target}...\n")
    
    scanner = NmapScanner()
    results = scanner.scan_network(target, 'normal')
    
    print(f"\n[*] Scan completed: {len(results)} hosts found\n")
    
    for ip, info in results.items():
        print(f"\n{'='*60}")
        print(f"Host: {ip} ({info.get('hostname', 'unknown')})")
        print(f"State: {info['state']}")
        
        if info.get('os'):
            print(f"OS: {', '.join(info['os'])}")
        
        print(f"\nOpen ports:")
        for port_info in info['ports']:
            print(f"  {port_info['port']}/{port_info['protocol']} - "
                  f"{port_info['service']} {port_info.get('product', '')} "
                  f"{port_info.get('version', '')}")
    
    print(f"\n{'='*60}\n")
