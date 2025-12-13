"""Tests pour le module Fingerprinter"""
import pytest
import sys
from pathlib import Path

# Ajout du chemin parent pour imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from proto_agent.recon.fingerprint import Fingerprinter, quick_fingerprint


class TestFingerprinter:
    """Tests du fingerprinter"""
    
    def test_fingerprinter_initialization(self):
        """Test l'initialisation du fingerprinter"""
        fp = Fingerprinter()
        assert fp is not None
        assert fp.timeout == 5
        assert len(fp.user_agents) > 0
        assert len(fp.cms_signatures) > 0
        assert len(fp.waf_signatures) > 0
    
    def test_fingerprinter_custom_timeout(self):
        """Test l'initialisation avec timeout personnalisé"""
        fp = Fingerprinter(timeout=10)
        assert fp.timeout == 10
    
    def test_waf_signatures_structure(self):
        """Test la structure des signatures WAF"""
        fp = Fingerprinter()
        
        assert 'Cloudflare' in fp.waf_signatures
        assert 'AWS WAF' in fp.waf_signatures
        assert isinstance(fp.waf_signatures['Cloudflare'], list)
    
    def test_cms_signatures_structure(self):
        """Test la structure des signatures CMS"""
        fp = Fingerprinter()
        
        assert 'WordPress' in fp.cms_signatures
        assert 'Joomla' in fp.cms_signatures
        assert 'Drupal' in fp.cms_signatures
        assert isinstance(fp.cms_signatures['WordPress'], list)
    
    @pytest.mark.skipif(True, reason="Requires actual network connection")
    def test_grab_banner_real(self):
        """Test grab_banner sur un serveur réel (skip par défaut)"""
        fp = Fingerprinter()
        banner = fp.grab_banner('example.com', 80)
        
        if banner:
            assert isinstance(banner, str)
            assert len(banner) > 0
    
    @pytest.mark.skipif(True, reason="Requires actual network connection")
    def test_http_fingerprint_real(self):
        """Test http_fingerprint sur un site réel (skip par défaut)"""
        fp = Fingerprinter()
        result = fp.http_fingerprint('http://example.com')
        
        assert isinstance(result, dict)
        assert 'server' in result
        assert 'status_code' in result
        assert 'headers' in result
    
    @pytest.mark.skipif(True, reason="Requires actual network connection")
    def test_ssl_certificate_info_real(self):
        """Test ssl_certificate_info sur un site HTTPS (skip par défaut)"""
        fp = Fingerprinter()
        cert_info = fp.ssl_certificate_info('example.com', 443)
        
        if cert_info:
            assert isinstance(cert_info, dict)
            assert 'issuer' in cert_info or cert_info == {}
    
    def test_identify_vulnerabilities_empty(self):
        """Test identify_vulnerabilities avec données vides"""
        fp = Fingerprinter()
        
        empty_data = {
            'server': '',
            'cms': None,
            'headers': {},
            'ssl_info': {}
        }
        
        vulns = fp.identify_vulnerabilities(empty_data)
        
        assert isinstance(vulns, list)
        # Devrait détecter des headers manquants
        assert any(v['type'] == 'missing_security_header' for v in vulns)
    
    def test_identify_vulnerabilities_apache_old(self):
        """Test détection de vulns sur Apache outdated"""
        fp = Fingerprinter()
        
        data = {
            'server': 'Apache/2.4.41',
            'cms': None,
            'headers': {},
            'ssl_info': {}
        }
        
        vulns = fp.identify_vulnerabilities(data)
        
        # Devrait détecter Apache outdated
        assert any('Apache' in v.get('component', '') for v in vulns)
    
    def test_identify_vulnerabilities_wordpress(self):
        """Test détection de vulns WordPress"""
        fp = Fingerprinter()
        
        data = {
            'server': 'nginx',
            'cms': 'WordPress 5.8',
            'headers': {},
            'ssl_info': {}
        }
        
        vulns = fp.identify_vulnerabilities(data)
        
        # Devrait détecter WordPress
        assert any('WordPress' in v.get('component', '') for v in vulns)
    
    def test_identify_vulnerabilities_missing_headers(self):
        """Test détection de security headers manquants"""
        fp = Fingerprinter()
        
        data = {
            'server': 'nginx',
            'cms': None,
            'headers': {
                'Content-Type': 'text/html'
            },
            'ssl_info': {},
            'url': 'https://example.com'
        }
        
        vulns = fp.identify_vulnerabilities(data)
        
        # Devrait détecter headers manquants
        missing_header_vulns = [v for v in vulns if v['type'] == 'missing_security_header']
        assert len(missing_header_vulns) > 0
    
    def test_identify_vulnerabilities_expired_cert(self):
        """Test détection de certificat SSL expiré"""
        fp = Fingerprinter()
        
        data = {
            'server': 'nginx',
            'cms': None,
            'headers': {},
            'ssl_info': {
                'expired': True
            }
        }
        
        vulns = fp.identify_vulnerabilities(data)
        
        # Devrait détecter cert expiré
        assert any(v['type'] == 'ssl_issue' for v in vulns)
        assert any(v['severity'] == 'critical' for v in vulns)
    
    def test_detect_waf_cloudflare(self):
        """Test détection WAF Cloudflare"""
        fp = Fingerprinter()
        
        # Mock response
        class MockResponse:
            headers = {'cf-ray': '12345', 'server': 'cloudflare'}
            cookies = {}
            text = ''
        
        response = MockResponse()
        waf = fp._detect_waf(response)
        
        assert waf == 'Cloudflare'
    
    def test_detect_waf_none(self):
        """Test absence de WAF"""
        fp = Fingerprinter()
        
        class MockResponse:
            headers = {'server': 'nginx'}
            cookies = {}
            text = ''
        
        response = MockResponse()
        waf = fp._detect_waf(response)
        
        assert waf is None
    
    def test_identify_cms_wordpress(self):
        """Test identification WordPress"""
        fp = Fingerprinter()
        
        class MockResponse:
            headers = {}
            cookies = {}
            text = '''
                <html>
                <head>
                    <meta name="generator" content="WordPress 5.8" />
                </head>
                <body>
                    <script src="/wp-content/themes/theme.js"></script>
                    <link href="/wp-includes/css/style.css" />
                </body>
                </html>
            '''
        
        response = MockResponse()
        cms = fp._identify_cms(response)
        
        assert cms is not None
        assert 'WordPress' in cms
    
    def test_identify_cms_joomla(self):
        """Test identification Joomla"""
        fp = Fingerprinter()
        
        class MockResponse:
            headers = {}
            cookies = {}
            text = '''
                <html>
                <body>
                    <script src="/components/com_content/script.js"></script>
                    <script src="/media/jui/js/jquery.js"></script>
                    <div>Joomla! is Free Software</div>
                </body>
                </html>
            '''
        
        response = MockResponse()
        cms = fp._identify_cms(response)
        
        assert cms is not None
        assert 'Joomla' in cms
    
    def test_identify_technologies_php(self):
        """Test identification PHP"""
        fp = Fingerprinter()
        
        class MockResponse:
            headers = {'X-Powered-By': 'PHP/7.4.3'}
            cookies = {}
            text = '<html><a href="index.php">Home</a></html>'
        
        response = MockResponse()
        technologies = fp._identify_technologies(response)
        
        assert 'PHP' in technologies
    
    def test_identify_technologies_jquery(self):
        """Test identification jQuery"""
        fp = Fingerprinter()
        
        class MockResponse:
            headers = {}
            cookies = {}
            text = '<html><script src="jquery-3.5.1.min.js"></script></html>'
        
        response = MockResponse()
        technologies = fp._identify_technologies(response)
        
        assert 'jQuery' in technologies
    
    def test_extract_cms_version_wordpress(self):
        """Test extraction version WordPress"""
        fp = Fingerprinter()
        
        content = '<meta name="generator" content="WordPress 5.8.1" />'
        headers = {}
        
        version = fp._extract_cms_version('WordPress', content, headers)
        
        assert version == '5.8.1'


class TestQuickFingerprint:
    """Tests de la fonction utilitaire quick_fingerprint"""
    
    @pytest.mark.skipif(True, reason="Requires actual network connection")
    def test_quick_fingerprint_execution(self):
        """Test l'exécution de quick_fingerprint (skip par défaut)"""
        result = quick_fingerprint('http://example.com')
        assert isinstance(result, dict)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
