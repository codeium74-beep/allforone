"""Collecteur d'intelligence depuis les Sous-Matriarches"""
import asyncio
import time
from typing import List, Dict, Optional


class IntelligenceCollector:
    """Collecte passive des rapports via Percepteurs"""
    
    def __init__(self, brain):
        self.brain = brain
        self.collected_reports = []
        self.last_collection = 0
        
    async def collect_from_sub_matriarches(self) -> List[Dict]:
        """Collecte les rapports de toutes les Sous-Matriarches"""
        reports = []
        
        for sub in self.brain.sub_matriarches:
            try:
                report = await self._request_report(sub['id'])
                if report:
                    reports.append(report)
            except Exception as e:
                print(f"[Collector] Error collecting from {sub['id']}: {e}")
        
        self.collected_reports.extend(reports)
        self.last_collection = time.time()
        
        return reports
    
    async def _request_report(self, sub_id: str) -> Optional[Dict]:
        """Demande un rapport à une Sous-Matriarche via Percepteur"""
        # Construction de la requête
        request = {
            'type': 'status_report_request',
            'from': self.brain.node_id,
            'target': sub_id,
            'timestamp': time.time(),
            'nonce': self.brain.crypto.generate_nonce()
        }
        
        # Chiffrement de la requête
        request_json = str(request).encode()
        encrypted_request = self.brain.crypto.encrypt_symmetric(request_json)
        
        # Stockage de la requête pour récupération par Percepteur
        request_id = f"report_request_{sub_id}_{int(time.time())}"
        self.brain.storage.store(request_id, encrypted_request)
        
        # Attente de la réponse (timeout 30s)
        response = await self._wait_for_response(sub_id, timeout=30)
        
        if response:
            # Validation du rapport
            if self._validate_report(response):
                return self._process_report(response)
        
        return None
    
    async def _wait_for_response(self, sub_id: str, timeout: float) -> Optional[Dict]:
        """Attend la réponse d'une Sous-Matriarche"""
        start_time = time.time()
        response_id = f"report_response_{sub_id}"
        
        while time.time() - start_time < timeout:
            try:
                # Tentative de récupération de la réponse
                response_data = self.brain.storage.retrieve(response_id)
                if response_data:
                    # Déchiffrement
                    decrypted = self.brain.crypto.decrypt_symmetric(response_data)
                    response = eval(decrypted.decode())
                    
                    # Nettoyage
                    self.brain.storage.delete(response_id)
                    
                    return response
            except Exception as e:
                pass
            
            await asyncio.sleep(1)
        
        return None
    
    def _validate_report(self, report: Dict) -> bool:
        """Valide l'intégrité et l'authenticité d'un rapport"""
        # Vérification des champs obligatoires
        required_fields = ['sub_id', 'timestamp', 'signature']
        if not all(field in report for field in required_fields):
            return False
        
        # Vérification de la signature
        sub_info = next(
            (s for s in self.brain.sub_matriarches if s['id'] == report['sub_id']),
            None
        )
        
        if not sub_info:
            return False
        
        # Extraction de la signature et des données
        signature = report.pop('signature')
        report_data = str(report).encode()
        
        # Vérification
        is_valid = self.brain.crypto.verify_signature(
            report_data,
            signature,
            sub_info['public_key']
        )
        
        # Remise de la signature
        report['signature'] = signature
        
        return is_valid
    
    def _process_report(self, report: Dict) -> Dict:
        """Traite et enrichit un rapport"""
        processed = {
            'sub_id': report['sub_id'],
            'timestamp': report['timestamp'],
            'received_at': time.time(),
            'protos_status': report.get('protos_status', {}),
            'discoveries': report.get('discoveries', []),
            'mission_progress': report.get('mission_progress', {}),
            'p2p_exchanges': report.get('p2p_exchanges', [])
        }
        
        # Extraction des découvertes importantes
        processed['discovered_systems'] = self._extract_systems(processed['discoveries'])
        processed['paths'] = self._extract_paths(processed['discoveries'])
        processed['vulnerabilities'] = self._extract_vulnerabilities(processed['discoveries'])
        
        return processed
    
    def _extract_systems(self, discoveries: List[Dict]) -> List[Dict]:
        """Extrait les systèmes découverts"""
        systems = []
        for discovery in discoveries:
            if discovery.get('type') == 'system':
                systems.append({
                    'id': discovery.get('id'),
                    'ip': discovery.get('ip'),
                    'hostname': discovery.get('hostname'),
                    'os': discovery.get('os'),
                    'services': discovery.get('services', [])
                })
        return systems
    
    def _extract_paths(self, discoveries: List[Dict]) -> List[Dict]:
        """Extrait les chemins réseau découverts"""
        paths = []
        for discovery in discoveries:
            if discovery.get('type') == 'path':
                paths.append({
                    'from': discovery.get('from'),
                    'to': discovery.get('to'),
                    'method': discovery.get('method'),
                    'success_rate': discovery.get('success_rate', 0.0)
                })
        return paths
    
    def _extract_vulnerabilities(self, discoveries: List[Dict]) -> List[Dict]:
        """Extrait les vulnérabilités trouvées"""
        vulns = []
        for discovery in discoveries:
            if discovery.get('type') == 'vulnerability':
                vulns.append({
                    'target': discovery.get('target'),
                    'vulnerability': discovery.get('vulnerability'),
                    'severity': discovery.get('severity'),
                    'exploitable': discovery.get('exploitable', False)
                })
        return vulns
    
    def get_intelligence_summary(self) -> Dict:
        """Génère un résumé de l'intelligence collectée"""
        total_systems = set()
        total_paths = []
        total_vulns = []
        
        for report in self.collected_reports:
            for system in report.get('discovered_systems', []):
                total_systems.add(system['id'])
            
            total_paths.extend(report.get('paths', []))
            total_vulns.extend(report.get('vulnerabilities', []))
        
        return {
            'total_reports': len(self.collected_reports),
            'unique_systems': len(total_systems),
            'total_paths': len(total_paths),
            'total_vulnerabilities': len(total_vulns),
            'last_collection': self.last_collection,
            'high_severity_vulns': len([
                v for v in total_vulns if v.get('severity') == 'high'
            ])
        }
