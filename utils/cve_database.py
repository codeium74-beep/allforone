"""Base de données CVE locale - Import et recherche de vulnérabilités"""
import json
import gzip
import logging
import re
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import requests

logger = logging.getLogger(__name__)


class CVEDatabase:
    """Base de données locale pour CVE (Common Vulnerabilities and Exposures)"""
    
    def __init__(self, db_path: str = './data/cve_database.json'):
        """
        Initialise la base de données CVE
        
        Args:
            db_path: Chemin vers le fichier de base de données JSON
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.cve_data = {}
        self.cpe_index = {}  # Index CPE pour recherche rapide
        self.service_index = {}  # Index par service/version
        
        # Charger la base si elle existe
        if self.db_path.exists():
            self._load_database()
    
    def import_cve_feed(self, json_path: Optional[str] = None, year: Optional[int] = None) -> bool:
        """
        Importe un feed CVE depuis NIST au format JSON
        
        Args:
            json_path: Chemin vers fichier JSON local (optionnel)
            year: Année du feed à télécharger (ex: 2023)
            
        Returns:
            True si succès, False sinon
        """
        logger.info(f"[CVEDatabase] Importing CVE feed...")
        
        try:
            if json_path:
                # Import depuis fichier local
                logger.info(f"[CVEDatabase] Loading from local file: {json_path}")
                with open(json_path, 'r') as f:
                    data = json.load(f)
            elif year:
                # Téléchargement depuis NIST
                url = f"https://nvd.nist.gov/feeds/json/cve/1.1/nvdcve-1.1-{year}.json.gz"
                logger.info(f"[CVEDatabase] Downloading from NIST: {url}")
                
                response = requests.get(url, timeout=60)
                
                if response.status_code == 200:
                    # Décompression
                    import io
                    gzip_file = io.BytesIO(response.content)
                    with gzip.open(gzip_file, 'rt', encoding='utf-8') as f:
                        data = json.load(f)
                else:
                    logger.error(f"[CVEDatabase] Failed to download: HTTP {response.status_code}")
                    return False
            else:
                logger.error("[CVEDatabase] No data source specified")
                return False
            
            # Parsing du feed NIST
            if 'CVE_Items' in data:
                items = data['CVE_Items']
            elif 'cve_items' in data:
                items = data['cve_items']
            else:
                logger.error("[CVEDatabase] Unknown JSON structure")
                return False
            
            logger.info(f"[CVEDatabase] Processing {len(items)} CVE entries...")
            
            count = 0
            for item in items:
                cve_entry = self._parse_cve_item(item)
                if cve_entry:
                    self.cve_data[cve_entry['cve_id']] = cve_entry
                    self._index_cve_entry(cve_entry)
                    count += 1
            
            logger.info(f"[CVEDatabase] Imported {count} CVE entries")
            
            # Sauvegarde de la base
            self._save_database()
            
            return True
            
        except Exception as e:
            logger.error(f"[CVEDatabase] Import failed: {e}")
            return False
    
    def search_by_cpe(self, cpe_string: str) -> List[Dict]:
        """
        Recherche CVE par CPE (Common Platform Enumeration)
        
        Args:
            cpe_string: String CPE (ex: "cpe:2.3:a:apache:http_server:2.4.41")
            
        Returns:
            Liste de CVE matchant le CPE
        """
        logger.info(f"[CVEDatabase] Searching by CPE: {cpe_string}")
        
        results = []
        
        # Recherche exacte dans l'index
        if cpe_string in self.cpe_index:
            for cve_id in self.cpe_index[cpe_string]:
                results.append(self.cve_data[cve_id])
        
        # Recherche partielle
        else:
            cpe_parts = cpe_string.split(':')
            
            for indexed_cpe, cve_ids in self.cpe_index.items():
                # Match partiel (vendor + product au minimum)
                if len(cpe_parts) >= 5:
                    indexed_parts = indexed_cpe.split(':')
                    
                    # Compare vendor et product
                    if (len(indexed_parts) >= 5 and 
                        cpe_parts[3] == indexed_parts[3] and  # vendor
                        cpe_parts[4] == indexed_parts[4]):    # product
                        
                        # Si version spécifiée, check aussi
                        if len(cpe_parts) >= 6 and len(indexed_parts) >= 6:
                            if cpe_parts[5] == indexed_parts[5]:  # version
                                for cve_id in cve_ids:
                                    if cve_id not in [r['cve_id'] for r in results]:
                                        results.append(self.cve_data[cve_id])
                        else:
                            # Pas de version → match vendor+product
                            for cve_id in cve_ids:
                                if cve_id not in [r['cve_id'] for r in results]:
                                    results.append(self.cve_data[cve_id])
        
        logger.info(f"[CVEDatabase] Found {len(results)} CVEs for CPE")
        
        return results
    
    def search_by_service(self, service: str, version: Optional[str] = None) -> List[Dict]:
        """
        Recherche CVE par nom de service et version
        
        Args:
            service: Nom du service (ex: "Apache", "nginx", "MySQL")
            version: Version optionnelle (ex: "2.4.41")
            
        Returns:
            Liste de CVE matchant
        """
        logger.info(f"[CVEDatabase] Searching by service: {service} {version or ''}")
        
        results = []
        
        search_key = service.lower()
        if version:
            search_key = f"{search_key}:{version}"
        
        # Recherche dans l'index de services
        if search_key in self.service_index:
            for cve_id in self.service_index[search_key]:
                results.append(self.cve_data[cve_id])
        
        # Recherche partielle par service uniquement
        elif version is None:
            for indexed_service, cve_ids in self.service_index.items():
                if indexed_service.startswith(search_key + ':'):
                    for cve_id in cve_ids:
                        if cve_id not in [r['cve_id'] for r in results]:
                            results.append(self.cve_data[cve_id])
        
        # Tri par score CVSS décroissant
        results.sort(key=lambda x: x.get('cvss_score', 0), reverse=True)
        
        logger.info(f"[CVEDatabase] Found {len(results)} CVEs for service")
        
        return results
    
    def get_exploits_for_cve(self, cve_id: str) -> List[Dict]:
        """
        Récupère les exploits connus pour un CVE
        
        Args:
            cve_id: ID du CVE (ex: "CVE-2021-44228")
            
        Returns:
            Liste d'exploits avec métadonnées
        """
        logger.info(f"[CVEDatabase] Getting exploits for {cve_id}")
        
        if cve_id not in self.cve_data:
            return []
        
        cve = self.cve_data[cve_id]
        
        # Exploits stockés dans l'entrée CVE
        exploits = cve.get('exploits', [])
        
        # Si pas d'exploits stockés, recherche basique
        if not exploits:
            # Check références pour liens exploit-db
            for ref in cve.get('references', []):
                url = ref.get('url', '')
                if 'exploit-db.com' in url:
                    exploits.append({
                        'name': f"Exploit-DB {url.split('/')[-1]}",
                        'source': 'exploit-db',
                        'url': url,
                        'reliability': 'medium'
                    })
                elif 'github.com' in url and 'exploit' in url.lower():
                    exploits.append({
                        'name': f"GitHub Exploit",
                        'source': 'github',
                        'url': url,
                        'reliability': 'low'
                    })
        
        return exploits
    
    def get_cve_by_id(self, cve_id: str) -> Optional[Dict]:
        """
        Récupère un CVE par son ID
        
        Args:
            cve_id: ID du CVE (ex: "CVE-2021-44228")
            
        Returns:
            Dict avec infos CVE ou None
        """
        return self.cve_data.get(cve_id)
    
    def search_by_keyword(self, keyword: str, limit: int = 50) -> List[Dict]:
        """
        Recherche CVE par mot-clé dans la description
        
        Args:
            keyword: Mot-clé à rechercher
            limit: Nombre max de résultats
            
        Returns:
            Liste de CVE matchant
        """
        logger.info(f"[CVEDatabase] Searching by keyword: {keyword}")
        
        results = []
        keyword_lower = keyword.lower()
        
        for cve in self.cve_data.values():
            description = cve.get('description', '').lower()
            
            if keyword_lower in description:
                results.append(cve)
                
                if len(results) >= limit:
                    break
        
        # Tri par score CVSS décroissant
        results.sort(key=lambda x: x.get('cvss_score', 0), reverse=True)
        
        logger.info(f"[CVEDatabase] Found {len(results)} CVEs for keyword")
        
        return results
    
    def get_high_severity_cves(self, min_cvss: float = 7.0, limit: int = 100) -> List[Dict]:
        """
        Récupère les CVE avec CVSS >= threshold
        
        Args:
            min_cvss: Score CVSS minimum
            limit: Nombre max de résultats
            
        Returns:
            Liste de CVE triés par score
        """
        logger.info(f"[CVEDatabase] Getting CVEs with CVSS >= {min_cvss}")
        
        results = []
        
        for cve in self.cve_data.values():
            cvss_score = cve.get('cvss_score', 0)
            
            if cvss_score >= min_cvss:
                results.append(cve)
        
        # Tri par score décroissant
        results.sort(key=lambda x: x.get('cvss_score', 0), reverse=True)
        
        return results[:limit]
    
    def get_stats(self) -> Dict:
        """
        Retourne des statistiques sur la base de données
        
        Returns:
            Dict avec stats
        """
        if not self.cve_data:
            return {'total': 0}
        
        cvss_scores = [cve.get('cvss_score', 0) for cve in self.cve_data.values()]
        
        critical = sum(1 for score in cvss_scores if score >= 9.0)
        high = sum(1 for score in cvss_scores if 7.0 <= score < 9.0)
        medium = sum(1 for score in cvss_scores if 4.0 <= score < 7.0)
        low = sum(1 for score in cvss_scores if score < 4.0)
        
        return {
            'total': len(self.cve_data),
            'critical': critical,
            'high': high,
            'medium': medium,
            'low': low,
            'avg_cvss': sum(cvss_scores) / len(cvss_scores) if cvss_scores else 0
        }
    
    def _parse_cve_item(self, item: Dict) -> Optional[Dict]:
        """
        Parse un item CVE du feed NIST
        
        Args:
            item: Dict item depuis le feed JSON
            
        Returns:
            Dict CVE structuré ou None
        """
        try:
            cve = item.get('cve', {})
            cve_id = cve.get('CVE_data_meta', {}).get('ID', '')
            
            if not cve_id:
                return None
            
            # Description
            description_data = cve.get('description', {}).get('description_data', [])
            description = ''
            if description_data:
                description = description_data[0].get('value', '')
            
            # CVSS Score
            impact = item.get('impact', {})
            cvss_score = 0
            cvss_vector = ''
            
            if 'baseMetricV3' in impact:
                cvss_v3 = impact['baseMetricV3'].get('cvssV3', {})
                cvss_score = cvss_v3.get('baseScore', 0)
                cvss_vector = cvss_v3.get('vectorString', '')
            elif 'baseMetricV2' in impact:
                cvss_v2 = impact['baseMetricV2'].get('cvssV2', {})
                cvss_score = cvss_v2.get('baseScore', 0)
                cvss_vector = cvss_v2.get('vectorString', '')
            
            # CPE (produits affectés)
            configurations = item.get('configurations', {})
            affected_products = []
            cpe_list = []
            
            nodes = configurations.get('nodes', [])
            for node in nodes:
                cpe_matches = node.get('cpe_match', [])
                for cpe_match in cpe_matches:
                    if cpe_match.get('vulnerable', True):
                        cpe23_uri = cpe_match.get('cpe23Uri', '')
                        if cpe23_uri:
                            cpe_list.append(cpe23_uri)
                            
                            # Parse CPE pour extraire produit
                            product_info = self._parse_cpe(cpe23_uri)
                            if product_info:
                                affected_products.append(product_info)
            
            # Références
            references = []
            ref_data = cve.get('references', {}).get('reference_data', [])
            for ref in ref_data:
                references.append({
                    'url': ref.get('url', ''),
                    'name': ref.get('name', ''),
                    'tags': ref.get('tags', [])
                })
            
            # Published date
            published_date = item.get('publishedDate', '')
            last_modified = item.get('lastModifiedDate', '')
            
            return {
                'cve_id': cve_id,
                'description': description,
                'cvss_score': cvss_score,
                'cvss_vector': cvss_vector,
                'affected_products': affected_products,
                'cpe_list': cpe_list,
                'references': references,
                'published_date': published_date,
                'last_modified': last_modified,
                'exploits': []  # À remplir avec d'autres sources
            }
            
        except Exception as e:
            logger.error(f"[CVEDatabase] Failed to parse CVE item: {e}")
            return None
    
    def _parse_cpe(self, cpe_string: str) -> Optional[Dict]:
        """
        Parse un string CPE pour extraire vendor/product/version
        
        Args:
            cpe_string: String CPE (ex: "cpe:2.3:a:apache:http_server:2.4.41")
            
        Returns:
            Dict avec vendor, product, version
        """
        try:
            parts = cpe_string.split(':')
            
            if len(parts) >= 5:
                return {
                    'vendor': parts[3],
                    'product': parts[4],
                    'version': parts[5] if len(parts) > 5 else '*',
                    'cpe': cpe_string
                }
            
            return None
            
        except Exception:
            return None
    
    def _index_cve_entry(self, cve_entry: Dict):
        """
        Index une entrée CVE pour recherche rapide
        
        Args:
            cve_entry: Dict CVE
        """
        cve_id = cve_entry['cve_id']
        
        # Index par CPE
        for cpe in cve_entry.get('cpe_list', []):
            if cpe not in self.cpe_index:
                self.cpe_index[cpe] = []
            self.cpe_index[cpe].append(cve_id)
        
        # Index par service/version
        for product in cve_entry.get('affected_products', []):
            vendor = product.get('vendor', '').lower()
            prod_name = product.get('product', '').lower()
            version = product.get('version', '*')
            
            # Index vendor:product
            service_key = f"{vendor}:{prod_name}"
            if service_key not in self.service_index:
                self.service_index[service_key] = []
            if cve_id not in self.service_index[service_key]:
                self.service_index[service_key].append(cve_id)
            
            # Index vendor:product:version
            if version != '*':
                version_key = f"{service_key}:{version}"
                if version_key not in self.service_index:
                    self.service_index[version_key] = []
                if cve_id not in self.service_index[version_key]:
                    self.service_index[version_key].append(cve_id)
            
            # Index par product name seul (pour recherche simple)
            if prod_name not in self.service_index:
                self.service_index[prod_name] = []
            if cve_id not in self.service_index[prod_name]:
                self.service_index[prod_name].append(cve_id)
    
    def _save_database(self):
        """Sauvegarde la base de données sur disque"""
        try:
            logger.info(f"[CVEDatabase] Saving database to {self.db_path}")
            
            db_dump = {
                'cve_data': self.cve_data,
                'cpe_index': self.cpe_index,
                'service_index': self.service_index,
                'updated_at': datetime.now().isoformat()
            }
            
            with open(self.db_path, 'w') as f:
                json.dump(db_dump, f, indent=2)
            
            logger.info("[CVEDatabase] Database saved successfully")
            
        except Exception as e:
            logger.error(f"[CVEDatabase] Failed to save database: {e}")
    
    def _load_database(self):
        """Charge la base de données depuis le disque"""
        try:
            logger.info(f"[CVEDatabase] Loading database from {self.db_path}")
            
            with open(self.db_path, 'r') as f:
                db_dump = json.load(f)
            
            self.cve_data = db_dump.get('cve_data', {})
            self.cpe_index = db_dump.get('cpe_index', {})
            self.service_index = db_dump.get('service_index', {})
            
            logger.info(f"[CVEDatabase] Loaded {len(self.cve_data)} CVE entries")
            
        except Exception as e:
            logger.error(f"[CVEDatabase] Failed to load database: {e}")


if __name__ == '__main__':
    # Test de la base de données
    import sys
    
    db = CVEDatabase()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'import' and len(sys.argv) > 2:
            # Import depuis fichier
            json_path = sys.argv[2]
            print(f"Importing CVE feed from {json_path}...")
            success = db.import_cve_feed(json_path=json_path)
            print(f"Import {'successful' if success else 'failed'}")
            
        elif command == 'download' and len(sys.argv) > 2:
            # Téléchargement depuis NIST
            year = int(sys.argv[2])
            print(f"Downloading CVE feed for year {year}...")
            success = db.import_cve_feed(year=year)
            print(f"Download {'successful' if success else 'failed'}")
            
        elif command == 'search':
            if len(sys.argv) > 2:
                service = sys.argv[2]
                version = sys.argv[3] if len(sys.argv) > 3 else None
                
                print(f"\nSearching CVEs for {service} {version or '(all versions)'}...")
                results = db.search_by_service(service, version)
                
                print(f"\nFound {len(results)} CVEs:\n")
                for cve in results[:10]:  # Top 10
                    print(f"{cve['cve_id']} - CVSS: {cve['cvss_score']}")
                    print(f"  {cve['description'][:200]}...")
                    print()
        
        elif command == 'stats':
            stats = db.get_stats()
            print("\n=== CVE Database Statistics ===")
            print(f"Total CVEs: {stats['total']}")
            print(f"Critical (CVSS >= 9.0): {stats.get('critical', 0)}")
            print(f"High (CVSS 7.0-8.9): {stats.get('high', 0)}")
            print(f"Medium (CVSS 4.0-6.9): {stats.get('medium', 0)}")
            print(f"Low (CVSS < 4.0): {stats.get('low', 0)}")
            print(f"Average CVSS: {stats.get('avg_cvss', 0):.2f}\n")
    
    else:
        print("Usage:")
        print("  python cve_database.py import <json_file>")
        print("  python cve_database.py download <year>")
        print("  python cve_database.py search <service> [version]")
        print("  python cve_database.py stats")
