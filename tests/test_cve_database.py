"""Tests pour le module CVEDatabase"""
import pytest
import json
import tempfile
import sys
from pathlib import Path

# Ajout du chemin parent pour imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.cve_database import CVEDatabase


class TestCVEDatabase:
    """Tests de la base de données CVE"""
    
    def test_database_initialization(self):
        """Test l'initialisation de la base de données"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = f"{tmpdir}/test_cve.json"
            db = CVEDatabase(db_path=db_path)
            
            assert db is not None
            assert db.cve_data == {}
            assert db.cpe_index == {}
            assert db.service_index == {}
    
    def test_parse_cpe(self):
        """Test le parsing de CPE strings"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = f"{tmpdir}/test_cve.json"
            db = CVEDatabase(db_path=db_path)
            
            cpe = "cpe:2.3:a:apache:http_server:2.4.41:*:*:*:*:*:*:*"
            result = db._parse_cpe(cpe)
            
            assert result is not None
            assert result['vendor'] == 'apache'
            assert result['product'] == 'http_server'
            assert result['version'] == '2.4.41'
    
    def test_parse_cpe_invalid(self):
        """Test le parsing de CPE invalide"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = f"{tmpdir}/test_cve.json"
            db = CVEDatabase(db_path=db_path)
            
            result = db._parse_cpe("invalid_cpe")
            assert result is None
    
    def test_index_cve_entry(self):
        """Test l'indexation d'une entrée CVE"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = f"{tmpdir}/test_cve.json"
            db = CVEDatabase(db_path=db_path)
            
            cve_entry = {
                'cve_id': 'CVE-2021-44228',
                'description': 'Log4j RCE vulnerability',
                'cvss_score': 10.0,
                'cpe_list': ['cpe:2.3:a:apache:log4j:2.14.1'],
                'affected_products': [
                    {
                        'vendor': 'apache',
                        'product': 'log4j',
                        'version': '2.14.1'
                    }
                ]
            }
            
            db.cve_data[cve_entry['cve_id']] = cve_entry
            db._index_cve_entry(cve_entry)
            
            # Vérifier index CPE
            assert 'cpe:2.3:a:apache:log4j:2.14.1' in db.cpe_index
            assert 'CVE-2021-44228' in db.cpe_index['cpe:2.3:a:apache:log4j:2.14.1']
            
            # Vérifier index service
            assert 'apache:log4j' in db.service_index
            assert 'log4j' in db.service_index
    
    def test_search_by_service(self):
        """Test la recherche par service"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = f"{tmpdir}/test_cve.json"
            db = CVEDatabase(db_path=db_path)
            
            # Ajouter des CVE de test
            cve1 = {
                'cve_id': 'CVE-2021-44228',
                'description': 'Log4j RCE',
                'cvss_score': 10.0,
                'cpe_list': [],
                'affected_products': [
                    {'vendor': 'apache', 'product': 'log4j', 'version': '2.14.1'}
                ]
            }
            
            cve2 = {
                'cve_id': 'CVE-2021-45046',
                'description': 'Log4j DoS',
                'cvss_score': 9.0,
                'cpe_list': [],
                'affected_products': [
                    {'vendor': 'apache', 'product': 'log4j', 'version': '2.15.0'}
                ]
            }
            
            db.cve_data[cve1['cve_id']] = cve1
            db.cve_data[cve2['cve_id']] = cve2
            db._index_cve_entry(cve1)
            db._index_cve_entry(cve2)
            
            # Recherche par service
            results = db.search_by_service('log4j')
            
            assert len(results) == 2
            assert results[0]['cvss_score'] >= results[1]['cvss_score']  # Trié par CVSS
    
    def test_search_by_service_with_version(self):
        """Test la recherche par service avec version"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = f"{tmpdir}/test_cve.json"
            db = CVEDatabase(db_path=db_path)
            
            cve = {
                'cve_id': 'CVE-2021-44228',
                'description': 'Log4j RCE',
                'cvss_score': 10.0,
                'cpe_list': [],
                'affected_products': [
                    {'vendor': 'apache', 'product': 'log4j', 'version': '2.14.1'}
                ]
            }
            
            db.cve_data[cve['cve_id']] = cve
            db._index_cve_entry(cve)
            
            # Recherche avec version exacte
            results = db.search_by_service('log4j', '2.14.1')
            
            assert len(results) == 1
            assert results[0]['cve_id'] == 'CVE-2021-44228'
    
    def test_get_cve_by_id(self):
        """Test la récupération d'un CVE par ID"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = f"{tmpdir}/test_cve.json"
            db = CVEDatabase(db_path=db_path)
            
            cve = {
                'cve_id': 'CVE-2021-44228',
                'description': 'Log4j RCE',
                'cvss_score': 10.0
            }
            
            db.cve_data[cve['cve_id']] = cve
            
            result = db.get_cve_by_id('CVE-2021-44228')
            
            assert result is not None
            assert result['cve_id'] == 'CVE-2021-44228'
            assert result['cvss_score'] == 10.0
    
    def test_get_high_severity_cves(self):
        """Test la récupération des CVE critiques"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = f"{tmpdir}/test_cve.json"
            db = CVEDatabase(db_path=db_path)
            
            # Ajouter CVE avec différents scores
            for i, score in enumerate([10.0, 9.5, 7.5, 5.0, 3.0]):
                cve = {
                    'cve_id': f'CVE-2021-{i}',
                    'description': f'Test CVE {i}',
                    'cvss_score': score
                }
                db.cve_data[cve['cve_id']] = cve
            
            results = db.get_high_severity_cves(min_cvss=7.0)
            
            assert len(results) == 3  # 10.0, 9.5, 7.5
            assert all(r['cvss_score'] >= 7.0 for r in results)
            assert results[0]['cvss_score'] >= results[-1]['cvss_score']  # Trié
    
    def test_search_by_keyword(self):
        """Test la recherche par mot-clé"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = f"{tmpdir}/test_cve.json"
            db = CVEDatabase(db_path=db_path)
            
            cve1 = {
                'cve_id': 'CVE-2021-1',
                'description': 'Remote Code Execution vulnerability',
                'cvss_score': 9.0
            }
            
            cve2 = {
                'cve_id': 'CVE-2021-2',
                'description': 'SQL Injection vulnerability',
                'cvss_score': 7.0
            }
            
            db.cve_data[cve1['cve_id']] = cve1
            db.cve_data[cve2['cve_id']] = cve2
            
            results = db.search_by_keyword('execution')
            
            assert len(results) == 1
            assert results[0]['cve_id'] == 'CVE-2021-1'
    
    def test_get_stats(self):
        """Test les statistiques de la base"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = f"{tmpdir}/test_cve.json"
            db = CVEDatabase(db_path=db_path)
            
            # Ajouter CVE avec différents scores
            scores = [10.0, 9.5, 8.0, 6.5, 3.0]
            for i, score in enumerate(scores):
                cve = {
                    'cve_id': f'CVE-2021-{i}',
                    'description': f'Test CVE {i}',
                    'cvss_score': score
                }
                db.cve_data[cve['cve_id']] = cve
            
            stats = db.get_stats()
            
            assert stats['total'] == 5
            assert stats['critical'] == 2  # >= 9.0
            assert stats['high'] == 1  # 7.0-8.9
            assert stats['medium'] == 1  # 4.0-6.9
            assert stats['low'] == 1  # < 4.0
    
    def test_get_stats_empty(self):
        """Test stats sur base vide"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = f"{tmpdir}/test_cve.json"
            db = CVEDatabase(db_path=db_path)
            
            stats = db.get_stats()
            
            assert stats['total'] == 0
    
    def test_get_exploits_for_cve(self):
        """Test la récupération d'exploits"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = f"{tmpdir}/test_cve.json"
            db = CVEDatabase(db_path=db_path)
            
            cve = {
                'cve_id': 'CVE-2021-44228',
                'description': 'Log4j RCE',
                'cvss_score': 10.0,
                'references': [
                    {
                        'url': 'https://www.exploit-db.com/exploits/12345',
                        'name': 'Exploit-DB',
                        'tags': []
                    }
                ]
            }
            
            db.cve_data[cve['cve_id']] = cve
            
            exploits = db.get_exploits_for_cve('CVE-2021-44228')
            
            assert len(exploits) > 0
            assert any('exploit-db' in e['source'] for e in exploits)
    
    def test_save_and_load_database(self):
        """Test sauvegarde et chargement de la base"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = f"{tmpdir}/test_cve.json"
            
            # Créer et sauvegarder
            db1 = CVEDatabase(db_path=db_path)
            
            cve = {
                'cve_id': 'CVE-2021-44228',
                'description': 'Test CVE',
                'cvss_score': 10.0,
                'cpe_list': [],
                'affected_products': []
            }
            
            db1.cve_data[cve['cve_id']] = cve
            db1._save_database()
            
            # Charger dans nouvelle instance
            db2 = CVEDatabase(db_path=db_path)
            
            assert len(db2.cve_data) == 1
            assert 'CVE-2021-44228' in db2.cve_data
            assert db2.cve_data['CVE-2021-44228']['cvss_score'] == 10.0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
