"""
Feedback Loop - Système d'apprentissage par rétroaction
Enregistre les succès et échecs pour améliorer les décisions futures
"""
import time
import json
from pathlib import Path
from typing import Dict, List, Optional
from collections import defaultdict


class FeedbackLoop:
    """
    Système de boucle de rétroaction pour apprentissage continu
    
    Enregistre:
    - Plans générés par le TacticalBrain
    - Résultats d'exécution (succès/échec)
    - Contexte d'échec pour éviter les répétitions
    - Métriques de performance
    """
    
    def __init__(self, storage_path: str = '/tmp/matriarche_feedback', max_history: int = 100):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.max_history = max_history
        
        # Historique des opérations
        self.history = []  # [(plan, result, timestamp)]
        
        # Statistiques agrégées
        self.stats = {
            'total_operations': 0,
            'successful_operations': 0,
            'failed_operations': 0,
            'success_rate': 0.0,
            'by_action_type': defaultdict(lambda: {'success': 0, 'failure': 0}),
            'by_target_type': defaultdict(lambda: {'success': 0, 'failure': 0})
        }
        
        # Patterns d'échec
        self.failure_patterns = []
        
        # Chargement de l'historique persisté
        self._load_from_disk()
    
    def record_operation(self, plan: Dict, success: bool, result: Dict):
        """
        Enregistre le résultat d'une opération
        
        Args:
            plan: Le plan tactique généré par le TacticalBrain
            success: True si l'opération a réussi
            result: Détails du résultat (error message, output, etc.)
        """
        timestamp = time.time()
        
        operation_record = {
            'plan': plan,
            'success': success,
            'result': result,
            'timestamp': timestamp,
            'action': plan.get('action', 'unknown'),
            'target': plan.get('target', 'unknown'),
            'priority': plan.get('priority', 'medium')
        }
        
        # Ajout à l'historique
        self.history.append(operation_record)
        
        # Mise à jour des statistiques
        self._update_statistics(operation_record)
        
        # Détection de patterns d'échec
        if not success:
            self._analyze_failure(operation_record)
        
        # Limite la taille de l'historique en mémoire
        if len(self.history) > self.max_history:
            self.history.pop(0)
        
        # Sauvegarde périodique (tous les 10 enregistrements)
        if len(self.history) % 10 == 0:
            self._save_to_disk()
        
        print(f"[FeedbackLoop] Recorded {'SUCCESS' if success else 'FAILURE'}: {plan.get('action')} on {plan.get('target')}")
    
    def _update_statistics(self, record: Dict):
        """Met à jour les statistiques agrégées"""
        self.stats['total_operations'] += 1
        
        if record['success']:
            self.stats['successful_operations'] += 1
        else:
            self.stats['failed_operations'] += 1
        
        # Taux de succès global
        self.stats['success_rate'] = (
            self.stats['successful_operations'] / self.stats['total_operations']
            if self.stats['total_operations'] > 0 else 0.0
        )
        
        # Statistiques par type d'action
        action = record['action']
        if record['success']:
            self.stats['by_action_type'][action]['success'] += 1
        else:
            self.stats['by_action_type'][action]['failure'] += 1
        
        # Statistiques par type de cible
        target = record['target']
        if record['success']:
            self.stats['by_target_type'][target]['success'] += 1
        else:
            self.stats['by_target_type'][target]['failure'] += 1
    
    def _analyze_failure(self, record: Dict):
        """Analyse un échec pour détecter des patterns"""
        failure_pattern = {
            'action': record['action'],
            'target': record['target'],
            'error': record['result'].get('error', 'Unknown error'),
            'timestamp': record['timestamp'],
            'context': {
                'priority': record['priority'],
                'plan_details': record['plan']
            }
        }
        
        # Détection de patterns répétitifs
        similar_failures = [
            f for f in self.failure_patterns
            if f['action'] == failure_pattern['action'] and
               f['target'] == failure_pattern['target'] and
               (record['timestamp'] - f['timestamp']) < 3600  # Dernière heure
        ]
        
        if len(similar_failures) >= 2:
            # Pattern critique: même échec répété 3+ fois
            failure_pattern['critical'] = True
            failure_pattern['repeat_count'] = len(similar_failures) + 1
            print(f"[FeedbackLoop] ⚠️  CRITICAL FAILURE PATTERN: {failure_pattern['action']} on {failure_pattern['target']} failed {failure_pattern['repeat_count']} times")
        else:
            failure_pattern['critical'] = False
        
        self.failure_patterns.append(failure_pattern)
        
        # Limite la taille des patterns
        if len(self.failure_patterns) > 50:
            self.failure_patterns.pop(0)
    
    def get_feedback_context(self, max_failures: int = 5) -> str:
        """
        Génère un contexte de feedback pour le TacticalBrain
        
        Args:
            max_failures: Nombre maximum d'échecs récents à inclure
        
        Returns:
            String formatté avec les échecs récents à éviter
        """
        recent_failures = [
            record for record in self.history[-20:]
            if not record['success']
        ][-max_failures:]
        
        if not recent_failures:
            return "No recent failures. All previous operations succeeded."
        
        context_lines = [
            "RECENT FAILURES TO AVOID:",
            ""
        ]
        
        for i, failure in enumerate(recent_failures, 1):
            action = failure['action']
            target = failure['target']
            error = failure['result'].get('error', 'Unknown')
            
            # Troncature de l'erreur si trop longue
            if len(error) > 150:
                error = error[:150] + "..."
            
            context_lines.append(
                f"{i}. Action '{action}' on target '{target}' failed: {error}"
            )
        
        # Ajout des patterns critiques
        critical_patterns = [p for p in self.failure_patterns if p.get('critical', False)]
        if critical_patterns:
            context_lines.append("")
            context_lines.append("CRITICAL PATTERNS (avoid at all costs):")
            for pattern in critical_patterns[-3:]:  # Top 3
                context_lines.append(
                    f"- {pattern['action']} on {pattern['target']}: Failed {pattern['repeat_count']} times"
                )
        
        return "\n".join(context_lines)
    
    def get_success_patterns(self, action_type: Optional[str] = None) -> List[Dict]:
        """
        Retourne les patterns de succès pour un type d'action
        
        Args:
            action_type: Type d'action (exploit, bruteforce, etc.) ou None pour tous
        
        Returns:
            Liste des opérations réussies
        """
        successful_operations = [
            record for record in self.history
            if record['success']
        ]
        
        if action_type:
            successful_operations = [
                op for op in successful_operations
                if op['action'] == action_type
            ]
        
        return successful_operations
    
    def get_statistics(self) -> Dict:
        """Retourne les statistiques complètes"""
        # Conversion des defaultdict en dict normal pour JSON
        stats_copy = dict(self.stats)
        stats_copy['by_action_type'] = dict(stats_copy['by_action_type'])
        stats_copy['by_target_type'] = dict(stats_copy['by_target_type'])
        
        # Ajout de métriques calculées
        stats_copy['recent_success_rate'] = self._calculate_recent_success_rate(window=10)
        stats_copy['total_failures_recorded'] = len(self.failure_patterns)
        stats_copy['critical_patterns'] = len([p for p in self.failure_patterns if p.get('critical', False)])
        
        return stats_copy
    
    def _calculate_recent_success_rate(self, window: int = 10) -> float:
        """Calcule le taux de succès sur les N dernières opérations"""
        if len(self.history) == 0:
            return 0.0
        
        recent = self.history[-window:]
        successes = sum(1 for r in recent if r['success'])
        
        return successes / len(recent) if recent else 0.0
    
    def get_recommendation(self, proposed_plan: Dict) -> Dict:
        """
        Évalue un plan proposé et donne une recommandation
        
        Args:
            proposed_plan: Plan tactique proposé
        
        Returns:
            Dict avec recommandation et score de confiance
        """
        action = proposed_plan.get('action', 'unknown')
        target = proposed_plan.get('target', 'unknown')
        
        # Vérification contre les patterns d'échec critiques
        critical_matches = [
            p for p in self.failure_patterns
            if p.get('critical', False) and
               p['action'] == action and
               p['target'] == target
        ]
        
        if critical_matches:
            return {
                'recommended': False,
                'confidence': 0.1,
                'reason': f"Critical failure pattern detected: {action} on {target} has failed {critical_matches[0]['repeat_count']} times recently",
                'alternative_suggested': True,
                'alternative': self._suggest_alternative(action, target)
            }
        
        # Calcul du taux de succès historique pour ce type d'action
        action_stats = self.stats['by_action_type'].get(action, {'success': 0, 'failure': 0})
        total_action = action_stats['success'] + action_stats['failure']
        
        if total_action > 0:
            success_rate = action_stats['success'] / total_action
            
            return {
                'recommended': success_rate > 0.5,
                'confidence': success_rate,
                'reason': f"Historical success rate for {action}: {success_rate:.2%} ({action_stats['success']}/{total_action} succeeded)",
                'alternative_suggested': False
            }
        else:
            # Pas d'historique pour cette action
            return {
                'recommended': True,
                'confidence': 0.5,
                'reason': f"No historical data for {action}. Proceeding with caution.",
                'alternative_suggested': False
            }
    
    def _suggest_alternative(self, failed_action: str, failed_target: str) -> Dict:
        """Suggère une action alternative basée sur les succès passés"""
        # Recherche d'actions réussies sur la même cible
        successful_on_target = [
            r for r in self.history
            if r['success'] and r['target'] == failed_target and r['action'] != failed_action
        ]
        
        if successful_on_target:
            # Retourner l'action la plus récente qui a fonctionné
            most_recent = max(successful_on_target, key=lambda x: x['timestamp'])
            return {
                'action': most_recent['action'],
                'reason': f"This action succeeded on {failed_target} previously"
            }
        
        # Recherche de l'action la plus fiable en général
        best_action = None
        best_rate = 0.0
        
        for action_type, stats in self.stats['by_action_type'].items():
            total = stats['success'] + stats['failure']
            if total >= 3:  # Au moins 3 essais
                rate = stats['success'] / total
                if rate > best_rate:
                    best_rate = rate
                    best_action = action_type
        
        if best_action:
            return {
                'action': best_action,
                'reason': f"Most reliable action overall (success rate: {best_rate:.2%})"
            }
        
        return {
            'action': 'reconnaissance',
            'reason': 'Fallback to safe reconnaissance action'
        }
    
    def _save_to_disk(self):
        """Sauvegarde l'historique et les statistiques sur disque"""
        try:
            # Sauvegarde de l'historique
            history_file = self.storage_path / 'feedback_history.json'
            with open(history_file, 'w') as f:
                json.dump(self.history[-self.max_history:], f, indent=2)
            
            # Sauvegarde des statistiques
            stats_file = self.storage_path / 'feedback_stats.json'
            with open(stats_file, 'w') as f:
                json.dump(self.get_statistics(), f, indent=2)
            
            # Sauvegarde des patterns d'échec
            patterns_file = self.storage_path / 'failure_patterns.json'
            with open(patterns_file, 'w') as f:
                json.dump(self.failure_patterns, f, indent=2)
            
            print(f"[FeedbackLoop] Saved {len(self.history)} records to disk")
            
        except Exception as e:
            print(f"[FeedbackLoop] Error saving to disk: {e}")
    
    def _load_from_disk(self):
        """Charge l'historique et les statistiques depuis le disque"""
        try:
            # Chargement de l'historique
            history_file = self.storage_path / 'feedback_history.json'
            if history_file.exists():
                with open(history_file, 'r') as f:
                    self.history = json.load(f)
                
                # Reconstruction des statistiques depuis l'historique
                for record in self.history:
                    self._update_statistics(record)
                
                print(f"[FeedbackLoop] Loaded {len(self.history)} records from disk")
            
            # Chargement des patterns d'échec
            patterns_file = self.storage_path / 'failure_patterns.json'
            if patterns_file.exists():
                with open(patterns_file, 'r') as f:
                    self.failure_patterns = json.load(f)
                
                print(f"[FeedbackLoop] Loaded {len(self.failure_patterns)} failure patterns")
            
        except Exception as e:
            print(f"[FeedbackLoop] Error loading from disk: {e}")
    
    def reset(self):
        """Réinitialise complètement le feedback loop"""
        self.history = []
        self.failure_patterns = []
        self.stats = {
            'total_operations': 0,
            'successful_operations': 0,
            'failed_operations': 0,
            'success_rate': 0.0,
            'by_action_type': defaultdict(lambda: {'success': 0, 'failure': 0}),
            'by_target_type': defaultdict(lambda: {'success': 0, 'failure': 0})
        }
        
        print("[FeedbackLoop] Reset complete")
    
    def export_report(self, output_file: str):
        """Exporte un rapport complet au format JSON"""
        report = {
            'generated_at': time.time(),
            'statistics': self.get_statistics(),
            'recent_history': self.history[-20:],
            'failure_patterns': self.failure_patterns,
            'recommendations': {
                'most_reliable_actions': self._get_most_reliable_actions(top_n=3),
                'actions_to_avoid': self._get_actions_to_avoid(top_n=3)
            }
        }
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"[FeedbackLoop] Report exported to {output_file}")
    
    def _get_most_reliable_actions(self, top_n: int = 3) -> List[Dict]:
        """Retourne les actions les plus fiables"""
        action_rates = []
        
        for action, stats in self.stats['by_action_type'].items():
            total = stats['success'] + stats['failure']
            if total >= 2:  # Au moins 2 essais
                rate = stats['success'] / total
                action_rates.append({
                    'action': action,
                    'success_rate': rate,
                    'total_attempts': total
                })
        
        # Tri par taux de succès
        action_rates.sort(key=lambda x: x['success_rate'], reverse=True)
        
        return action_rates[:top_n]
    
    def _get_actions_to_avoid(self, top_n: int = 3) -> List[Dict]:
        """Retourne les actions à éviter"""
        action_rates = []
        
        for action, stats in self.stats['by_action_type'].items():
            total = stats['success'] + stats['failure']
            if total >= 2:  # Au moins 2 essais
                failure_rate = stats['failure'] / total
                action_rates.append({
                    'action': action,
                    'failure_rate': failure_rate,
                    'total_attempts': total
                })
        
        # Tri par taux d'échec
        action_rates.sort(key=lambda x: x['failure_rate'], reverse=True)
        
        return action_rates[:top_n]


if __name__ == '__main__':
    # Test du FeedbackLoop
    print("=== FeedbackLoop Test ===\n")
    
    feedback = FeedbackLoop(storage_path='/tmp/test_feedback')
    
    # Simulation d'opérations
    print("1. Recording operations...")
    
    plans = [
        {'action': 'exploit', 'target': '192.168.1.100', 'priority': 'high'},
        {'action': 'exploit', 'target': '192.168.1.100', 'priority': 'high'},
        {'action': 'bruteforce', 'target': '192.168.1.101', 'priority': 'medium'},
        {'action': 'exploit', 'target': '192.168.1.102', 'priority': 'high'},
        {'action': 'reconnaissance', 'target': '192.168.1.0/24', 'priority': 'low'},
    ]
    
    results = [
        (False, {'error': 'Target patched against exploit'}),
        (False, {'error': 'Target patched against exploit'}),
        (True, {'output': 'SSH access obtained'}),
        (True, {'output': 'Exploit successful'}),
        (True, {'output': '50 hosts discovered'}),
    ]
    
    for plan, (success, result) in zip(plans, results):
        feedback.record_operation(plan, success, result)
        time.sleep(0.1)
    
    # Affichage du contexte
    print("\n2. Feedback context:")
    print(feedback.get_feedback_context())
    
    # Statistiques
    print("\n3. Statistics:")
    print(json.dumps(feedback.get_statistics(), indent=2))
    
    # Test de recommandation
    print("\n4. Recommendation for new plan:")
    new_plan = {'action': 'exploit', 'target': '192.168.1.100', 'priority': 'high'}
    recommendation = feedback.get_recommendation(new_plan)
    print(json.dumps(recommendation, indent=2))
    
    # Export
    print("\n5. Exporting report...")
    feedback.export_report('/tmp/test_feedback_report.json')
    
    print("\n✓ Test complete")
