"""Module de fingerprinting - Identification services et technologies"""
import socket
import ssl
import requests
import re
import logging
from typing import Dict, List, Optional
from urllib.parse import urlparse
from datetime import datetime

logger = logging.getLogger(__name__)


class Fingerprinter:
    """Fingerprinter pour identification de services, CMS, technologies"""
    
    def __init__(self, timeout: int = 5):
        """
        Initialise le fingerprinter
        
        Args:
            timeout: Timeout pour les connexions (secondes)
        """
        self.timeout = timeout
        
        # User agents variés pour éviter détection
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15'
        ]
        
        # Signatures CMS
        self.cms_signatures = {
            'WordPress': [
                r'/wp-content/',
                r'/wp-includes/',
                r'wp-json',
                r'<meta name="generator" content="WordPress'
            ],
            'Joomla': [
                r'/components/com_',
                r'/media/jui/',
                r'Joomla!',
                r'/administrator/'
            ],
            'Drupal': [
                r'Drupal',
                r'/sites/default/',
                r'/misc/drupal.js',
                r'X-Generator.*Drupal'
            ],
            'Magento': [
                r'/skin/frontend/',
                r'/js/mage/',
                r'Mage.Cookies'
            ],
            'PrestaShop': [
                r'/themes/prestashop/',
                r'prestashop',
                r'/modules/blockcart/'
            ],
            'Shopify': [
                r'cdn.shopify.com',
                r'Shopify.theme',
                r'myshopify.com'
            ]
        }
        
        # Signatures WAF
        self.waf_signatures = {
            'Cloudflare': ['__cfduid', 'cf-ray', 'cloudflare'],
            'AWS WAF': ['x-amzn-requestid', 'x-amz-cf-id'],
            'Imperva': ['incap_ses', '_incap_', 'imperva'],
            'Akamai': ['akamai', 'ak-bmsc', 'bm_sz'],
            'Sucuri': ['sucuri', 'x-sucuri'],
            'ModSecurity': ['mod_security', 'NOYB']
        }
    
    def grab_banner(self, ip: str, port: int) -> Optional[str]:
        """
        Récupère le banner d'un service via connexion raw socket
        
        Args:
            ip: Adresse IP
            port: Numéro de port
            
        Returns:
            Banner string ou None
        """
        logger.info(f"[Fingerprint] Grabbing banner from {ip}:{port}")
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            sock.connect((ip, port))
            
            # Envoi d'une requête basique pour provoquer réponse
            try:
                sock.send(b'HEAD / HTTP/1.0\r\n\r\n')
            except:
                pass
            
            # Réception du banner
            banner = sock.recv(4096)
            sock.close()
            
            banner_str = banner.decode('utf-8', errors='ignore').strip()
            
            logger.info(f"[Fingerprint] Banner received: {banner_str[:100]}...")
            return banner_str
            
        except socket.timeout:
            logger.warning(f"[Fingerprint] Timeout grabbing banner from {ip}:{port}")
            return None
        except Exception as e:
            logger.error(f"[Fingerprint] Failed to grab banner: {e}")
            return None
    
    def http_fingerprint(self, url: str) -> Dict:
        """
        Fingerprinting HTTP complet d'une URL
        
        Args:
            url: URL cible (ex: http://example.com)
            
        Returns:
            Dict avec informations complètes:
            {
                "server": "nginx/1.18.0",
                "technologies": ["PHP 7.4", "MySQL", "jQuery 3.5"],
                "cms": "WordPress 5.8",
                "waf": "Cloudflare",
                "headers": {...},
                "cookies": {...},
                "response_time": 0.234
            }
        """
        logger.info(f"[Fingerprint] HTTP fingerprinting {url}")
        
        result = {
            'url': url,
            'server': 'unknown',
            'technologies': [],
            'cms': None,
            'waf': None,
            'headers': {},
            'cookies': {},
            'response_time': 0,
            'status_code': 0,
            'ssl_info': {}
        }
        
        try:
            # Sélection user agent aléatoire
            import random
            headers = {
                'User-Agent': random.choice(self.user_agents)
            }
            
            # Requête HTTP
            start_time = datetime.now()
            response = requests.get(url, headers=headers, timeout=self.timeout, 
                                   verify=False, allow_redirects=True)
            response_time = (datetime.now() - start_time).total_seconds()
            
            result['status_code'] = response.status_code
            result['response_time'] = response_time
            result['headers'] = dict(response.headers)
            result['cookies'] = dict(response.cookies)
            
            # Extraction server
            if 'Server' in response.headers:
                result['server'] = response.headers['Server']
            
            # Détection WAF
            result['waf'] = self._detect_waf(response)
            
            # Détection CMS
            result['cms'] = self._identify_cms(response)
            
            # Détection technologies
            result['technologies'] = self._identify_technologies(response)
            
            # Si HTTPS, infos SSL
            if url.startswith('https://'):
                parsed = urlparse(url)
                result['ssl_info'] = self.ssl_certificate_info(parsed.hostname, 443)
            
            logger.info(f"[Fingerprint] HTTP fingerprint complete: {result['cms'] or 'Unknown CMS'}, "
                       f"Server: {result['server']}, WAF: {result['waf'] or 'None'}")
            
            return result
            
        except requests.exceptions.Timeout:
            logger.warning(f"[Fingerprint] Timeout connecting to {url}")
            result['error'] = 'Timeout'
            return result
        except requests.exceptions.ConnectionError:
            logger.warning(f"[Fingerprint] Connection failed to {url}")
            result['error'] = 'Connection failed'
            return result
        except Exception as e:
            logger.error(f"[Fingerprint] HTTP fingerprinting failed: {e}")
            result['error'] = str(e)
            return result
    
    def ssl_certificate_info(self, hostname: str, port: int = 443) -> Dict:
        """
        Récupère les informations du certificat SSL/TLS
        
        Args:
            hostname: Nom d'hôte
            port: Port SSL (443 par défaut)
            
        Returns:
            Dict avec informations certificat
        """
        logger.info(f"[Fingerprint] Getting SSL certificate info for {hostname}:{port}")
        
        cert_info = {
            'issuer': {},
            'subject': {},
            'version': 0,
            'serialNumber': '',
            'notBefore': '',
            'notAfter': '',
            'subjectAltName': [],
            'expired': False
        }
        
        try:
            context = ssl.create_default_context()
            
            with socket.create_connection((hostname, port), timeout=self.timeout) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert = ssock.getpeercert()
                    
                    if cert:
                        # Issuer
                        cert_info['issuer'] = dict(x[0] for x in cert.get('issuer', []))
                        
                        # Subject
                        cert_info['subject'] = dict(x[0] for x in cert.get('subject', []))
                        
                        # Version
                        cert_info['version'] = cert.get('version', 0)
                        
                        # Serial Number
                        cert_info['serialNumber'] = cert.get('serialNumber', '')
                        
                        # Validity dates
                        cert_info['notBefore'] = cert.get('notBefore', '')
                        cert_info['notAfter'] = cert.get('notAfter', '')
                        
                        # Subject Alternative Names
                        if 'subjectAltName' in cert:
                            cert_info['subjectAltName'] = [x[1] for x in cert['subjectAltName']]
                        
                        # Check if expired
                        from datetime import datetime
                        not_after = datetime.strptime(cert_info['notAfter'], '%b %d %H:%M:%S %Y %Z')
                        cert_info['expired'] = datetime.now() > not_after
            
            logger.info(f"[Fingerprint] SSL cert retrieved: Issued by {cert_info['issuer'].get('organizationName', 'Unknown')}")
            return cert_info
            
        except socket.timeout:
            logger.warning(f"[Fingerprint] SSL timeout for {hostname}:{port}")
            return {}
        except Exception as e:
            logger.error(f"[Fingerprint] SSL certificate retrieval failed: {e}")
            return {}
    
    def identify_vulnerabilities(self, fingerprint_data: Dict) -> List[Dict]:
        """
        Identifie les vulnérabilités potentielles basées sur le fingerprinting
        
        Args:
            fingerprint_data: Résultat de http_fingerprint()
            
        Returns:
            Liste de vulnérabilités potentielles
        """
        logger.info("[Fingerprint] Identifying potential vulnerabilities")
        
        vulnerabilities = []
        
        # Check server version pour vulns connues
        server = fingerprint_data.get('server', '')
        
        # Apache vulnérabilités connues
        if 'Apache' in server:
            version_match = re.search(r'Apache/(\d+\.\d+\.\d+)', server)
            if version_match:
                version = version_match.group(1)
                if version < '2.4.49':
                    vulnerabilities.append({
                        'type': 'outdated_software',
                        'component': 'Apache',
                        'version': version,
                        'description': 'Apache version outdated, multiple CVEs',
                        'severity': 'high',
                        'recommendation': 'Upgrade to Apache 2.4.51+'
                    })
        
        # Nginx vulnérabilités
        elif 'nginx' in server:
            version_match = re.search(r'nginx/(\d+\.\d+\.\d+)', server)
            if version_match:
                version = version_match.group(1)
                if version < '1.20.0':
                    vulnerabilities.append({
                        'type': 'outdated_software',
                        'component': 'nginx',
                        'version': version,
                        'description': 'Nginx version outdated',
                        'severity': 'medium',
                        'recommendation': 'Upgrade to nginx 1.20.0+'
                    })
        
        # WordPress vulns
        cms = fingerprint_data.get('cms')
        if cms and 'WordPress' in cms:
            vulnerabilities.append({
                'type': 'cms_detected',
                'component': 'WordPress',
                'description': 'WordPress detected - check for plugin vulnerabilities',
                'severity': 'info',
                'recommendation': 'Run WPScan for detailed analysis'
            })
            
            # Check for common WP paths
            vulnerabilities.append({
                'type': 'information_disclosure',
                'component': 'WordPress',
                'description': 'WordPress paths exposed (/wp-content/, /wp-json/)',
                'severity': 'low',
                'recommendation': 'Consider hiding WordPress signatures'
            })
        
        # Headers manquants (security headers)
        headers = fingerprint_data.get('headers', {})
        
        if 'X-Frame-Options' not in headers:
            vulnerabilities.append({
                'type': 'missing_security_header',
                'component': 'X-Frame-Options',
                'description': 'Missing X-Frame-Options header - clickjacking risk',
                'severity': 'medium',
                'recommendation': 'Add X-Frame-Options: DENY or SAMEORIGIN'
            })
        
        if 'X-Content-Type-Options' not in headers:
            vulnerabilities.append({
                'type': 'missing_security_header',
                'component': 'X-Content-Type-Options',
                'description': 'Missing X-Content-Type-Options header',
                'severity': 'low',
                'recommendation': 'Add X-Content-Type-Options: nosniff'
            })
        
        if 'Strict-Transport-Security' not in headers and fingerprint_data.get('url', '').startswith('https'):
            vulnerabilities.append({
                'type': 'missing_security_header',
                'component': 'HSTS',
                'description': 'Missing HSTS header on HTTPS site',
                'severity': 'medium',
                'recommendation': 'Add Strict-Transport-Security header'
            })
        
        # SSL certificate issues
        ssl_info = fingerprint_data.get('ssl_info', {})
        if ssl_info.get('expired'):
            vulnerabilities.append({
                'type': 'ssl_issue',
                'component': 'SSL Certificate',
                'description': 'SSL certificate expired',
                'severity': 'critical',
                'recommendation': 'Renew SSL certificate immediately'
            })
        
        logger.info(f"[Fingerprint] Found {len(vulnerabilities)} potential vulnerabilities")
        
        return vulnerabilities
    
    def _detect_waf(self, response: requests.Response) -> Optional[str]:
        """
        Détecte la présence d'un WAF
        
        Args:
            response: Objet Response de requests
            
        Returns:
            Nom du WAF ou None
        """
        headers_lower = {k.lower(): v.lower() for k, v in response.headers.items()}
        cookies_lower = {k.lower(): v.lower() for k, v in response.cookies.items()}
        
        for waf_name, signatures in self.waf_signatures.items():
            for signature in signatures:
                sig_lower = signature.lower()
                
                # Check headers
                for header_key, header_value in headers_lower.items():
                    if sig_lower in header_key or sig_lower in header_value:
                        return waf_name
                
                # Check cookies
                for cookie_key in cookies_lower.keys():
                    if sig_lower in cookie_key:
                        return waf_name
        
        return None
    
    def _identify_cms(self, response: requests.Response) -> Optional[str]:
        """
        Identifie le CMS utilisé
        
        Args:
            response: Objet Response de requests
            
        Returns:
            Nom du CMS ou None
        """
        content = response.text
        headers = response.headers
        
        for cms_name, signatures in self.cms_signatures.items():
            matches = 0
            for signature in signatures:
                # Check dans le contenu HTML
                if re.search(signature, content, re.IGNORECASE):
                    matches += 1
                
                # Check dans les headers
                for header_value in headers.values():
                    if re.search(signature, header_value, re.IGNORECASE):
                        matches += 1
            
            # Si au moins 2 signatures matchent, c'est probablement ce CMS
            if matches >= 2:
                # Try to extract version
                version = self._extract_cms_version(cms_name, content, headers)
                if version:
                    return f"{cms_name} {version}"
                return cms_name
        
        return None
    
    def _extract_cms_version(self, cms_name: str, content: str, headers: Dict) -> Optional[str]:
        """
        Extrait la version du CMS si possible
        
        Args:
            cms_name: Nom du CMS
            content: Contenu HTML
            headers: Headers HTTP
            
        Returns:
            Version ou None
        """
        version_patterns = {
            'WordPress': [
                r'<meta name="generator" content="WordPress ([0-9.]+)"',
                r'wp-includes/js/wp-embed.min.js\?ver=([0-9.]+)'
            ],
            'Joomla': [
                r'<meta name="generator" content="Joomla! ([0-9.]+)"'
            ],
            'Drupal': [
                r'<meta name="generator" content="Drupal ([0-9.]+)"',
                r'X-Generator.*Drupal ([0-9.]+)'
            ]
        }
        
        if cms_name in version_patterns:
            for pattern in version_patterns[cms_name]:
                # Check content
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    return match.group(1)
                
                # Check headers
                for header_value in headers.values():
                    match = re.search(pattern, header_value, re.IGNORECASE)
                    if match:
                        return match.group(1)
        
        return None
    
    def _identify_technologies(self, response: requests.Response) -> List[str]:
        """
        Identifie les technologies utilisées
        
        Args:
            response: Objet Response de requests
            
        Returns:
            Liste de technologies détectées
        """
        technologies = []
        content = response.text
        headers = response.headers
        
        # Technologies web communes
        tech_signatures = {
            'PHP': [r'X-Powered-By.*PHP', r'\.php'],
            'ASP.NET': [r'X-AspNet-Version', r'X-Powered-By.*ASP.NET'],
            'Node.js': [r'X-Powered-By.*Express'],
            'jQuery': [r'jquery[-.](min.)?js'],
            'React': [r'react[-.](min.)?js', r'react-dom'],
            'Vue.js': [r'vue[-.](min.)?js'],
            'Angular': [r'angular[-.](min.)?js'],
            'Bootstrap': [r'bootstrap[-.](min.)?css', r'bootstrap[-.](min.)?js'],
            'MySQL': [r'X-Powered-By.*MySQL'],
            'PostgreSQL': [r'X-Powered-By.*PostgreSQL'],
            'Redis': [r'X-Powered-By.*Redis'],
            'Nginx': [r'Server.*nginx'],
            'Apache': [r'Server.*Apache'],
            'IIS': [r'Server.*IIS']
        }
        
        for tech_name, patterns in tech_signatures.items():
            for pattern in patterns:
                # Check content
                if re.search(pattern, content, re.IGNORECASE):
                    if tech_name not in technologies:
                        technologies.append(tech_name)
                    break
                
                # Check headers
                for header_value in headers.values():
                    if re.search(pattern, header_value, re.IGNORECASE):
                        if tech_name not in technologies:
                            technologies.append(tech_name)
                        break
        
        return technologies


# Fonction utilitaire pour test rapide
def quick_fingerprint(url: str) -> Dict:
    """
    Fonction utilitaire pour fingerprinting rapide
    
    Args:
        url: URL cible
        
    Returns:
        Résultats du fingerprinting
    """
    fp = Fingerprinter()
    return fp.http_fingerprint(url)


if __name__ == '__main__':
    # Test du fingerprinter
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python fingerprint.py <url>")
        print("Example: python fingerprint.py http://example.com")
        sys.exit(1)
    
    url = sys.argv[1]
    
    if not url.startswith('http'):
        url = 'http://' + url
    
    print(f"\n[*] Starting fingerprinting of {url}...\n")
    
    fp = Fingerprinter()
    result = fp.http_fingerprint(url)
    
    print(f"\n{'='*60}")
    print(f"URL: {result['url']}")
    print(f"Status: {result['status_code']}")
    print(f"Server: {result['server']}")
    print(f"Response Time: {result['response_time']:.3f}s")
    
    if result.get('waf'):
        print(f"WAF Detected: {result['waf']}")
    
    if result.get('cms'):
        print(f"CMS: {result['cms']}")
    
    if result.get('technologies'):
        print(f"Technologies: {', '.join(result['technologies'])}")
    
    if result.get('ssl_info'):
        ssl_info = result['ssl_info']
        if ssl_info:
            print(f"\nSSL Certificate:")
            print(f"  Issuer: {ssl_info.get('issuer', {}).get('organizationName', 'Unknown')}")
            print(f"  Subject: {ssl_info.get('subject', {}).get('commonName', 'Unknown')}")
            print(f"  Valid Until: {ssl_info.get('notAfter', 'Unknown')}")
            print(f"  Expired: {ssl_info.get('expired', False)}")
    
    # Check vulnerabilities
    print(f"\n{'='*60}")
    print("Vulnerability Assessment:")
    
    vulns = fp.identify_vulnerabilities(result)
    if vulns:
        for vuln in vulns:
            print(f"\n[{vuln['severity'].upper()}] {vuln['type']}")
            print(f"  Component: {vuln['component']}")
            print(f"  Description: {vuln['description']}")
            print(f"  Recommendation: {vuln['recommendation']}")
    else:
        print("No obvious vulnerabilities detected")
    
    print(f"\n{'='*60}\n")
