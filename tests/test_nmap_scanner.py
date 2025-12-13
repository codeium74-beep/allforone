"""Tests pour le module NmapScanner"""
import pytest
import sys
from pathlib import Path

# Ajout du chemin parent pour imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from proto_agent.recon.nmap_scanner import NmapScanner, quick_scan


class TestNmapScanner:
    """Tests du scanner Nmap"""
    
    def test_scanner_initialization(self):
        """Test l'initialisation du scanner"""
        scanner = NmapScanner()
        assert scanner is not None
        assert scanner.nm is not None
        assert scanner.scan_history == []
    
    def test_scan_arguments(self):
        """Test la génération des arguments de scan"""
        scanner = NmapScanner()
        
        # Fast scan
        args = scanner._get_scan_arguments('fast')
        assert '-sS' in args
        assert '-T4' in args
        
        # Normal scan
        args = scanner._get_scan_arguments('normal')
        assert '-sV' in args
        assert '-sC' in args
        
        # Thorough scan
        args = scanner._get_scan_arguments('thorough')
        assert '-p-' in args
        assert '-O' in args
    
    def test_port_check_localhost(self):
        """Test la vérification de port sur localhost"""
        scanner = NmapScanner()
        
        # Port 22 (SSH) devrait être ouvert sur beaucoup de systèmes
        # Note: Ce test peut échouer selon la configuration
        # On teste juste que la fonction s'exécute sans erreur
        result = scanner.check_port_open('127.0.0.1', 22)
        assert isinstance(result, bool)
    
    def test_scan_history_management(self):
        """Test la gestion de l'historique"""
        scanner = NmapScanner()
        
        # Ajout manuel d'entrée d'historique pour test
        scanner.scan_history.append({
            'target': '192.168.1.0/24',
            'type': 'fast',
            'timestamp': 123456789,
            'duration': 5.5,
            'hosts_found': 3
        })
        
        history = scanner.get_scan_history()
        assert len(history) == 1
        assert history[0]['target'] == '192.168.1.0/24'
        
        scanner.clear_history()
        assert len(scanner.scan_history) == 0
    
    @pytest.mark.skipif(True, reason="Requires actual network and nmap installed")
    def test_scan_network_real(self):
        """Test scan réseau réel (skip par défaut)"""
        scanner = NmapScanner()
        results = scanner.scan_network('127.0.0.1', 'fast')
        
        assert isinstance(results, dict)
        # Localhost devrait être détecté
        assert '127.0.0.1' in results or len(results) == 0
    
    @pytest.mark.skipif(True, reason="Requires actual network and nmap installed")
    def test_scan_single_host_real(self):
        """Test scan d'un hôte unique (skip par défaut)"""
        scanner = NmapScanner()
        result = scanner.scan_single_host('127.0.0.1', [22, 80, 443])
        
        assert isinstance(result, dict)
    
    @pytest.mark.skipif(True, reason="Requires actual network and nmap installed")
    def test_stealth_scan_real(self):
        """Test scan furtif (skip par défaut)"""
        scanner = NmapScanner()
        result = scanner.stealth_scan('127.0.0.1')
        
        assert isinstance(result, dict)
        if result:
            assert result.get('scan_type') == 'stealth'
    
    def test_extract_ports_empty(self):
        """Test extraction de ports sans données"""
        scanner = NmapScanner()
        ports = scanner._extract_ports('invalid_host')
        
        assert isinstance(ports, list)
        assert len(ports) == 0
    
    def test_parse_os_detection_empty(self):
        """Test parsing OS sans données"""
        scanner = NmapScanner()
        os_list = scanner._parse_os_detection('invalid_host')
        
        assert isinstance(os_list, list)
        assert len(os_list) == 0


class TestQuickScan:
    """Tests de la fonction utilitaire quick_scan"""
    
    @pytest.mark.skipif(True, reason="Requires actual network and nmap installed")
    def test_quick_scan_execution(self):
        """Test l'exécution de quick_scan (skip par défaut)"""
        result = quick_scan('127.0.0.1')
        assert isinstance(result, dict)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
