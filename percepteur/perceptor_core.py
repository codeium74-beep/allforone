"""Core du Percepteur - Filtration et validation des communications"""
import asyncio
import time
import re
import sys
from pathlib import Path
from typing import Dict, Optional, List

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.crypto_utils import CryptoManager
from utils.storage_utils import DistributedStorage


class Perceptor:
    """Filtre et valide les communications vers la Matriarche"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.node_id = config.get('node_id', f'perceptor_{int(time.time())}')
        
        # Crypto
        self.crypto = CryptoManager()
        self.crypto.generate_keypair()
        
        # Stockage
        storage_path = config.get('storage_path', f'/tmp/perceptor_{self.node_id}')
        self.storage = DistributedStorage(storage_path)
        
        # Liste des Sous-Matriarches autorisées
        self.trusted_subs = config.get('trusted_subs', [])
        self.matriarche_id = config.get('matriarche_id')
        
        # Règles de validation
        self.validation_rules = self._init_validation_rules()
        
        # Logs d'activité suspecte
        self.suspicious_activity = []
        self.quarantined_reports = []
        
        self.running = False
    
    async def start(self):
        """Démarre le cycle de vie du Percepteur"""
        self.running = True
        print(f"[{self.node_id}] Perceptor starting...")
        
        # Boucles de surveillance
        await asyncio.gather(
            self._relay_loop(),
            self._monitoring_loop()
        )
    
    async def _relay_loop(self):
        """Boucle de relais des communications"""
        while self.running:
            try:
                # Vérification des rapports en attente
                await self._check_pending_reports()
                
                await asyncio.sleep(30)
                
            except Exception as e:
                print(f"[{self.node_id}] Error in relay loop: {e}")
                await asyncio.sleep(60)
    
    async def _monitoring_loop(self):
        """Surveillance des activités suspectes"""
        while self.running:
            try:
                # Nettoyage des anciens logs
                self._cleanup_old_logs()
                
                # Analyse des patterns suspects
                await self._analyze_patterns()
                
                await asyncio.sleep(300)
                
            except Exception as e:
                print(f"[{self.node_id}] Error in monitoring: {e}")
                await asyncio.sleep(600)
    
    async def _check_pending_reports(self):
        """Vérifie et traite les rapports en attente"""
        # Recherche de rapports de Sub-Matriarches
        for sub_id in self.trusted_subs:
            try:
                report_data = self.storage.retrieve(f'report_response_{sub_id}')
                if report_data:
                    report = eval(report_data.decode())
                    await self._process_report(report, sub_id)
            except Exception as e:
                pass
    
    async def _process_report(self, report: Dict, sub_id: str):
        """Traite et valide un rapport"""
        print(f"[{self.node_id}] Processing report from {sub_id}")
        
        # Validation de l'identité
        if not self._verify_sender_identity(report, sub_id):
            self._log_suspicious_activity(report, 'invalid_identity')
            return
        
        # Validation du contenu
        if not self._scan_for_corruption(report):
            self._quarantine_report(report, 'content_scan_failed')
            return
        
        # Validation cryptographique
        if not self._verify_cryptographic_proof(report):
            self._log_suspicious_activity(report, 'crypto_validation_failed')
            return
        
        # Transmission sécurisée vers Matriarche
        await self._relay_to_matriarche(report)
    
    def _verify_sender_identity(self, report: Dict, expected_sub_id: str) -> bool:
        """Vérifie l'identité de l'expéditeur"""
        reported_id = report.get('sub_id')
        
        if reported_id != expected_sub_id:
            return False
        
        # Vérification que la Sub est dans la liste de confiance
        if expected_sub_id not in self.trusted_subs:
            return False
        
        return True
    
    def _scan_for_corruption(self, report: Dict) -> bool:
        """Détecte les tentatives d'injection ou de corruption"""
        # Conversion en chaîne pour analyse
        report_str = str(report)
        
        # Patterns dangereux
        dangerous_patterns = [
            r'exec\s*\(',
            r'eval\s*\(',
            r'__import__\s*\(',
            r'subprocess\.',
            r'os\.system\s*\(',
            r'open\s*\([^)]*["\']w',  # Écriture de fichiers
            r'rm\s+-rf',
            r'del\s+\[',
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, report_str, re.IGNORECASE):
                print(f"[{self.node_id}] Dangerous pattern detected: {pattern}")
                return False
        
        # Vérification de la taille (protection DoS)
        if len(report_str) > 1024 * 1024:  # 1MB max
            print(f"[{self.node_id}] Report too large: {len(report_str)} bytes")
            return False
        
        # Vérification de la structure
        required_fields = ['sub_id', 'timestamp', 'protos_status']
        if not all(field in report for field in required_fields):
            print(f"[{self.node_id}] Missing required fields")
            return False
        
        return True
    
    def _verify_cryptographic_proof(self, report: Dict) -> bool:
        """Vérifie la preuve cryptographique"""
        # Vérification du timestamp (pas trop ancien)
        timestamp = report.get('timestamp', 0)
        age = time.time() - timestamp
        
        if age > 3600:  # 1 heure max
            print(f"[{self.node_id}] Report too old: {age} seconds")
            return False
        
        if age < -300:  # Pas dans le futur (avec tolérance de 5 min)
            print(f"[{self.node_id}] Report from future: {age} seconds")
            return False
        
        # Vérification de la signature si présente
        if 'signature' in report:
            # Note: nécessiterait la clé publique de la Sub
            # Ici: validation simplifiée
            signature = report.get('signature')
            if not signature or len(signature) < 32:
                return False
        
        # Vérification du hash si présent
        if 'report_hash' in report:
            # Recalcul du hash
            report_copy = report.copy()
            report_copy.pop('report_hash', None)
            report_copy.pop('signature', None)
            
            computed_hash = self.crypto.generate_hash(str(report_copy).encode())
            
            if computed_hash != report.get('report_hash'):
                print(f"[{self.node_id}] Hash mismatch")
                return False
        
        return True
    
    async def _relay_to_matriarche(self, report: Dict):
        """Relaie le rapport vers la Matriarche"""
        print(f"[{self.node_id}] Relaying report to Matriarche")
        
        # Ajout de métadonnées de validation
        validated_report = {
            **report,
            'validated_by': self.node_id,
            'validation_timestamp': time.time(),
            'relay_hop': 1
        }
        
        # Stockage pour récupération par Matriarche
        content_id = f"validated_report_{report.get('sub_id')}_{int(time.time())}"
        report_data = str(validated_report).encode()
        
        self.storage.store(content_id, report_data)
    
    def _log_suspicious_activity(self, report: Dict, reason: str):
        """Log une activité suspecte"""
        log_entry = {
            'timestamp': time.time(),
            'source': report.get('sub_id', 'unknown'),
            'reason': reason,
            'report_preview': str(report)[:200]
        }
        
        self.suspicious_activity.append(log_entry)
        
        print(f"[{self.node_id}] SUSPICIOUS ACTIVITY: {reason} from {log_entry['source']}")
    
    def _quarantine_report(self, report: Dict, reason: str):
        """Quarantaine un rapport suspect"""
        quarantine_entry = {
            'timestamp': time.time(),
            'reason': reason,
            'report': report
        }
        
        self.quarantined_reports.append(quarantine_entry)
        
        print(f"[{self.node_id}] Report quarantined: {reason}")
    
    def _init_validation_rules(self) -> List[Dict]:
        """Initialise les règles de validation"""
        return [
            {
                'name': 'size_limit',
                'type': 'size',
                'max_bytes': 1024 * 1024
            },
            {
                'name': 'age_limit',
                'type': 'timestamp',
                'max_age_seconds': 3600
            },
            {
                'name': 'required_fields',
                'type': 'structure',
                'fields': ['sub_id', 'timestamp', 'protos_status']
            }
        ]
    
    def _cleanup_old_logs(self):
        """Nettoie les anciens logs"""
        current_time = time.time()
        max_age = 86400  # 24 heures
        
        # Nettoyage activités suspectes
        self.suspicious_activity = [
            log for log in self.suspicious_activity
            if current_time - log['timestamp'] < max_age
        ]
        
        # Nettoyage quarantaine
        self.quarantined_reports = [
            report for report in self.quarantined_reports
            if current_time - report['timestamp'] < max_age
        ]
    
    async def _analyze_patterns(self):
        """Analyse les patterns d'activité suspecte"""
        if len(self.suspicious_activity) < 3:
            return
        
        # Recherche de patterns répétés
        recent = [log for log in self.suspicious_activity
                 if time.time() - log['timestamp'] < 3600]
        
        if len(recent) > 5:
            print(f"[{self.node_id}] WARNING: High suspicious activity rate")
            
            # Alerte potentielle (à implémenter)
    
    def add_trusted_sub(self, sub_id: str):
        """Ajoute une Sous-Matriarche à la liste de confiance"""
        if sub_id not in self.trusted_subs:
            self.trusted_subs.append(sub_id)
            print(f"[{self.node_id}] Added trusted sub: {sub_id}")
    
    def remove_trusted_sub(self, sub_id: str):
        """Retire une Sous-Matriarche de la liste de confiance"""
        if sub_id in self.trusted_subs:
            self.trusted_subs.remove(sub_id)
            print(f"[{self.node_id}] Removed trusted sub: {sub_id}")
    
    def get_security_status(self) -> Dict:
        """Retourne le statut de sécurité"""
        return {
            'node_id': self.node_id,
            'trusted_subs_count': len(self.trusted_subs),
            'suspicious_activities': len(self.suspicious_activity),
            'quarantined_reports': len(self.quarantined_reports),
            'last_activity': time.time()
        }
    
    async def shutdown(self):
        """Arrêt propre"""
        print(f"[{self.node_id}] Shutting down...")
        self.running = False


async def main():
    """Point d'entrée"""
    config = {
        'node_id': 'perceptor_001',
        'matriarche_id': 'matriarche_001',
        'trusted_subs': ['sub_001', 'sub_002', 'sub_003'],
        'storage_path': '/tmp/perceptor_001'
    }
    
    perceptor = Perceptor(config)
    
    try:
        await perceptor.start()
    except KeyboardInterrupt:
        await perceptor.shutdown()


if __name__ == '__main__':
    asyncio.run(main())
