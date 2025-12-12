"""Moteur polymorphique pour auto-mutation du code"""
import random
import string
import hashlib
import os
import sys


class PolymorphicEngine:
    """Moteur de polymorphisme et obfuscation"""
    
    def __init__(self):
        self.mutation_count = 0
        self.transformations = [
            'rename_variables',
            'reorder_functions',
            'insert_dead_code',
            'obfuscate_strings'
        ]
    
    def mutate_self(self):
        """Auto-mutation du code du Proto"""
        print(f"[PolymorphicEngine] Performing self-mutation #{self.mutation_count}")
        
        try:
            # Lecture du code source actuel
            source_file = __file__
            with open(source_file, 'r') as f:
                source = f.read()
            
            # Application de transformations
            mutated = self._apply_transformations(source)
            
            # Génération nouveau fichier
            new_file = self._generate_mutated_filename()
            with open(new_file, 'w') as f:
                f.write(mutated)
            
            self.mutation_count += 1
            
            print(f"[PolymorphicEngine] Mutation complete, new file: {new_file}")
            
        except Exception as e:
            print(f"[PolymorphicEngine] Mutation failed: {e}")
    
    def _apply_transformations(self, code: str) -> str:
        """Applique des transformations au code"""
        result = code
        
        # Sélection aléatoire de transformations
        num_transforms = random.randint(1, len(self.transformations))
        chosen = random.sample(self.transformations, num_transforms)
        
        for transform in chosen:
            if transform == 'rename_variables':
                result = self._rename_variables(result)
            elif transform == 'reorder_functions':
                result = self._reorder_functions(result)
            elif transform == 'insert_dead_code':
                result = self._insert_dead_code(result)
            elif transform == 'obfuscate_strings':
                result = self._obfuscate_strings(result)
        
        return result
    
    def _rename_variables(self, code: str) -> str:
        """Renomme les variables"""
        import re
        
        # Recherche de variables locales
        var_pattern = r'\b([a-z_][a-z0-9_]*)\b'
        variables = set(re.findall(var_pattern, code, re.IGNORECASE))
        
        # Exclusion mots-clés Python
        keywords = {
            'def', 'class', 'if', 'else', 'elif', 'for', 'while', 'try',
            'except', 'finally', 'import', 'from', 'return', 'yield', 'pass',
            'break', 'continue', 'True', 'False', 'None', 'and', 'or', 'not',
            'in', 'is', 'with', 'as', 'lambda', 'self', 'print', 'range',
            'len', 'str', 'int', 'float', 'list', 'dict', 'set', 'tuple'
        }
        
        # Exclusion noms de modules communs
        modules = {'os', 'sys', 'time', 'random', 'asyncio', 'hashlib'}
        
        variables -= keywords
        variables -= modules
        
        # Génération de nouveaux noms
        mapping = {}
        for var in variables:
            if len(var) > 2:  # Seulement variables de 3+ caractères
                new_name = self._generate_obfuscated_name(var)
                mapping[var] = new_name
        
        # Remplacement
        result = code
        for old, new in mapping.items():
            # Remplacement avec word boundaries
            result = re.sub(rf'\b{re.escape(old)}\b', new, result)
        
        return result
    
    def _reorder_functions(self, code: str) -> str:
        """Réorganise les fonctions"""
        lines = code.split('\n')
        
        # Extraction des fonctions
        functions = []
        current_func = []
        in_function = False
        indent_level = 0
        
        for line in lines:
            if line.strip().startswith('def '):
                if current_func:
                    functions.append('\n'.join(current_func))
                current_func = [line]
                in_function = True
                indent_level = len(line) - len(line.lstrip())
            elif in_function:
                current_line_indent = len(line) - len(line.lstrip())
                if line.strip() and current_line_indent <= indent_level and not line.strip().startswith('#'):
                    # Fin de la fonction
                    functions.append('\n'.join(current_func))
                    current_func = [line]
                    in_function = False
                else:
                    current_func.append(line)
            else:
                if current_func:
                    current_func.append(line)
        
        if current_func:
            functions.append('\n'.join(current_func))
        
        # Mélange (sauf __init__ et méthodes spéciales)
        special_funcs = []
        regular_funcs = []
        
        for func in functions:
            if 'def __' in func or 'def _apply_transformations' in func:
                special_funcs.append(func)
            else:
                regular_funcs.append(func)
        
        random.shuffle(regular_funcs)
        
        # Reconstruction
        result = '\n\n'.join(special_funcs + regular_funcs)
        
        return result
    
    def _insert_dead_code(self, code: str) -> str:
        """Insère du code inutile"""
        lines = code.split('\n')
        
        # Insertion de code mort
        num_insertions = len(lines) // 10  # 10% du code
        
        dead_code_templates = [
            "    _x{} = {} * {}",
            "    _tmp{} = str({}) + str({})",
            "    _unused{} = len(str({}))",
            "    pass  # Obfuscation {}",
            "    _var{} = random.randint(1, 100) if False else None"
        ]
        
        for _ in range(num_insertions):
            template = random.choice(dead_code_templates)
            dead_line = template.format(
                random.randint(1000, 9999),
                random.randint(1, 100),
                random.randint(1, 100)
            )
            
            # Insertion à position aléatoire
            insert_pos = random.randint(0, len(lines))
            lines.insert(insert_pos, dead_line)
        
        return '\n'.join(lines)
    
    def _obfuscate_strings(self, code: str) -> str:
        """Obfuscate les chaînes de caractères"""
        import re
        
        # Recherche de chaînes simples
        string_pattern = r'"([^"]{5,30})"'
        
        def replace_string(match):
            original = match.group(1)
            # Conversion en hex
            hex_version = ''.join(f'\\x{ord(c):02x}' for c in original)
            return f'"{hex_version}"'
        
        # Obfuscation sélective (30% des chaînes)
        result = code
        matches = list(re.finditer(string_pattern, code))
        
        for match in random.sample(matches, min(len(matches), len(matches) // 3)):
            if 'import' not in match.group(0) and 'def ' not in match.group(0):
                original = match.group(0)
                obfuscated = replace_string(match)
                result = result.replace(original, obfuscated, 1)
        
        return result
    
    def _generate_obfuscated_name(self, original: str) -> str:
        """Génère un nom obfusqué"""
        # Hash du nom original
        hash_val = hashlib.md5(original.encode()).hexdigest()[:8]
        
        # Préfixes possibles
        prefixes = ['var', 'obj', 'tmp', 'val', 'data', 'buf', 'ref']
        prefix = random.choice(prefixes)
        
        return f"{prefix}_{hash_val}"
    
    def _generate_mutated_filename(self) -> str:
        """Génère un nom de fichier pour le code muté"""
        timestamp = int(time.time()) if 'time' in dir() else 0
        random_suffix = ''.join(random.choices(string.ascii_lowercase, k=6))
        
        return f"/tmp/polymorphic_{timestamp}_{random_suffix}.py"


def obfuscate_payload(payload: str) -> str:
    """Obfuscate un payload"""
    engine = PolymorphicEngine()
    return engine._apply_transformations(payload)


def generate_polymorphic_variant(base_code: str) -> str:
    """Génère une variante polymorphe du code"""
    engine = PolymorphicEngine()
    
    # Application de toutes les transformations
    result = base_code
    for transform in engine.transformations:
        if transform == 'rename_variables':
            result = engine._rename_variables(result)
        elif transform == 'reorder_functions':
            result = engine._reorder_functions(result)
        elif transform == 'insert_dead_code':
            result = engine._insert_dead_code(result)
        elif transform == 'obfuscate_strings':
            result = engine._obfuscate_strings(result)
    
    return result
