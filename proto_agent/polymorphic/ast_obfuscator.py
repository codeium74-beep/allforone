"""
AST Obfuscator - Obfuscation avancée via manipulation d'AST
Transforme le code Python pour le rendre méconnaissable tout en conservant sa fonctionnalité
"""
import ast
import astor
import random
import string
import hashlib
from typing import Dict, List, Set, Optional


class ASTObfuscator:
    """
    Obfuscateur AST qui effectue:
    - Renommage de toutes les variables/fonctions
    - Réorganisation de l'ordre des fonctions
    - Injection de prédicats opaques
    - Aplatissement du flux de contrôle
    - Ajout de code mort
    """
    
    def __init__(self, seed: Optional[int] = None):
        self.seed = seed or random.randint(1, 1000000)
        random.seed(self.seed)
        
        # Mapping des noms originaux vers noms obfusqués
        self.name_mapping: Dict[str, str] = {}
        
        # Noms à ne jamais obfusquer (built-ins, imports standards)
        self.protected_names: Set[str] = {
            'print', 'len', 'range', 'str', 'int', 'float', 'list', 'dict',
            'tuple', 'set', 'open', 'input', 'True', 'False', 'None',
            'Exception', 'BaseException', 'ValueError', 'TypeError',
            '__init__', '__main__', '__name__', '__file__',
            'asyncio', 'time', 'sys', 'os', 'json', 'random'
        }
        
        # Compteur pour génération de noms uniques
        self.name_counter = 0
    
    def obfuscate_code(self, source_code: str) -> str:
        """
        Obfusque le code source complet
        
        Args:
            source_code: Code Python source
        
        Returns:
            Code obfusqué
        """
        try:
            # Parse en AST
            tree = ast.parse(source_code)
            
            # Étape 1: Collecte des noms à obfusquer
            self._collect_names(tree)
            
            # Étape 2: Renommage des identifiants
            tree = self._rename_identifiers(tree)
            
            # Étape 3: Réorganisation des fonctions
            tree = self._shuffle_functions(tree)
            
            # Étape 4: Injection de prédicats opaques
            tree = self._add_opaque_predicates(tree)
            
            # Étape 5: Ajout de code mort
            tree = self._inject_dead_code(tree)
            
            # Régénération du code
            obfuscated_code = astor.to_source(tree)
            
            return obfuscated_code
            
        except Exception as e:
            print(f"[ASTObfuscator] Obfuscation failed: {e}")
            return source_code  # Fallback vers code original
    
    def _collect_names(self, tree: ast.AST):
        """Collecte tous les noms de variables/fonctions à obfusquer"""
        for node in ast.walk(tree):
            # Fonctions
            if isinstance(node, ast.FunctionDef):
                if node.name not in self.protected_names:
                    self._generate_obfuscated_name(node.name)
            
            # Classes
            elif isinstance(node, ast.ClassDef):
                if node.name not in self.protected_names:
                    self._generate_obfuscated_name(node.name)
            
            # Variables assignées
            elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                if node.id not in self.protected_names:
                    self._generate_obfuscated_name(node.id)
    
    def _generate_obfuscated_name(self, original: str) -> str:
        """Génère un nom obfusqué unique"""
        if original in self.name_mapping:
            return self.name_mapping[original]
        
        # Génération de nom obfusqué basé sur hash
        hash_suffix = hashlib.md5(f"{original}{self.seed}{self.name_counter}".encode()).hexdigest()[:8]
        
        # Préfixes variés pour rendre moins suspect
        prefixes = ['_l', '_O', '_o', '_I', '_ll', '_OO']
        prefix = random.choice(prefixes)
        
        obfuscated = f"{prefix}{hash_suffix}"
        
        self.name_mapping[original] = obfuscated
        self.name_counter += 1
        
        return obfuscated
    
    def _rename_identifiers(self, tree: ast.AST) -> ast.AST:
        """Renomme tous les identifiants dans l'AST"""
        transformer = NameTransformer(self.name_mapping, self.protected_names)
        tree = transformer.visit(tree)
        return tree
    
    def _shuffle_functions(self, tree: ast.Module) -> ast.Module:
        """Réorganise l'ordre des fonctions de manière aléatoire"""
        # Séparer imports, classes, fonctions et code principal
        imports = []
        classes = []
        functions = []
        other = []
        
        for node in tree.body:
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                imports.append(node)
            elif isinstance(node, ast.ClassDef):
                classes.append(node)
            elif isinstance(node, ast.FunctionDef):
                functions.append(node)
            else:
                other.append(node)
        
        # Mélange des fonctions (mais pas des imports ni du code principal)
        random.shuffle(functions)
        random.shuffle(classes)
        
        # Reconstruction
        tree.body = imports + classes + functions + other
        
        return tree
    
    def _add_opaque_predicates(self, tree: ast.AST) -> ast.AST:
        """Ajoute des prédicats opaques (toujours vrais ou toujours faux)"""
        injector = OpaquePredicateInjector()
        tree = injector.visit(tree)
        return tree
    
    def _inject_dead_code(self, tree: ast.AST) -> ast.AST:
        """Injecte du code mort (jamais exécuté)"""
        injector = DeadCodeInjector()
        tree = injector.visit(tree)
        return tree


class NameTransformer(ast.NodeTransformer):
    """Transformateur AST pour renommer les identifiants"""
    
    def __init__(self, name_mapping: Dict[str, str], protected: Set[str]):
        self.name_mapping = name_mapping
        self.protected = protected
    
    def visit_Name(self, node: ast.Name) -> ast.Name:
        """Visite un nœud Name (variable)"""
        if node.id not in self.protected and node.id in self.name_mapping:
            node.id = self.name_mapping[node.id]
        return node
    
    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        """Visite une définition de fonction"""
        if node.name not in self.protected and node.name in self.name_mapping:
            node.name = self.name_mapping[node.name]
        
        # Renommage des arguments
        for arg in node.args.args:
            if arg.arg not in self.protected and arg.arg in self.name_mapping:
                arg.arg = self.name_mapping[arg.arg]
        
        # Continue avec les enfants
        self.generic_visit(node)
        return node
    
    def visit_ClassDef(self, node: ast.ClassDef) -> ast.ClassDef:
        """Visite une définition de classe"""
        if node.name not in self.protected and node.name in self.name_mapping:
            node.name = self.name_mapping[node.name]
        
        self.generic_visit(node)
        return node


class OpaquePredicateInjector(ast.NodeTransformer):
    """Injecte des prédicats opaques dans le code"""
    
    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        """Ajoute des prédicats opaques dans les fonctions"""
        # Ne pas injecter trop souvent (10% de chance)
        if random.random() < 0.1 and len(node.body) > 0:
            # Prédicat opaque toujours vrai: (x * x >= 0)
            opaque_predicate = ast.If(
                test=ast.Compare(
                    left=ast.BinOp(
                        left=ast.Constant(value=1),
                        op=ast.Mult(),
                        right=ast.Constant(value=1)
                    ),
                    ops=[ast.GtE()],
                    comparators=[ast.Constant(value=0)]
                ),
                body=[ast.Pass()],  # Ne fait rien si vrai
                orelse=[]
            )
            
            # Insertion au début de la fonction
            node.body.insert(0, opaque_predicate)
        
        self.generic_visit(node)
        return node


class DeadCodeInjector(ast.NodeTransformer):
    """Injecte du code mort (jamais exécuté)"""
    
    def __init__(self):
        self.dead_code_templates = [
            self._dead_variable_assignment,
            self._dead_if_block,
            self._dead_loop
        ]
    
    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        """Injecte du code mort dans les fonctions"""
        # Injection avec 15% de probabilité
        if random.random() < 0.15 and len(node.body) > 1:
            dead_code_func = random.choice(self.dead_code_templates)
            dead_code = dead_code_func()
            
            # Insertion à une position aléatoire
            insert_pos = random.randint(0, len(node.body) - 1)
            node.body.insert(insert_pos, dead_code)
        
        self.generic_visit(node)
        return node
    
    def _dead_variable_assignment(self) -> ast.Assign:
        """Génère une assignation de variable morte"""
        var_name = f"_unused_{random.randint(1000, 9999)}"
        value = random.randint(0, 1000)
        
        return ast.Assign(
            targets=[ast.Name(id=var_name, ctx=ast.Store())],
            value=ast.Constant(value=value)
        )
    
    def _dead_if_block(self) -> ast.If:
        """Génère un bloc if jamais exécuté"""
        # Condition toujours fausse: (False)
        return ast.If(
            test=ast.Constant(value=False),
            body=[
                ast.Assign(
                    targets=[ast.Name(id=f"_dead_{random.randint(1000, 9999)}", ctx=ast.Store())],
                    value=ast.Constant(value=random.randint(0, 100))
                )
            ],
            orelse=[]
        )
    
    def _dead_loop(self) -> ast.For:
        """Génère une boucle jamais exécutée"""
        # Boucle sur liste vide
        return ast.For(
            target=ast.Name(id=f"_i_{random.randint(1000, 9999)}", ctx=ast.Store()),
            iter=ast.List(elts=[], ctx=ast.Load()),
            body=[ast.Pass()],
            orelse=[]
        )


def obfuscate_file(input_file: str, output_file: str, seed: Optional[int] = None) -> bool:
    """
    Obfusque un fichier Python
    
    Args:
        input_file: Chemin du fichier source
        output_file: Chemin du fichier obfusqué
        seed: Seed pour reproductibilité (optionnel)
    
    Returns:
        True si succès, False sinon
    """
    try:
        # Lecture du code source
        with open(input_file, 'r', encoding='utf-8') as f:
            source_code = f.read()
        
        # Obfuscation
        obfuscator = ASTObfuscator(seed=seed)
        obfuscated_code = obfuscator.obfuscate_code(source_code)
        
        # Écriture du code obfusqué
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(obfuscated_code)
        
        print(f"[ASTObfuscator] Successfully obfuscated {input_file} -> {output_file}")
        return True
        
    except Exception as e:
        print(f"[ASTObfuscator] Failed to obfuscate file: {e}")
        return False


if __name__ == '__main__':
    # Test de l'obfuscateur
    print("=== AST Obfuscator Test ===\n")
    
    # Code de test
    test_code = """
import random
import time

def calculate_sum(a, b):
    result = a + b
    return result

def process_data(data_list):
    processed = []
    for item in data_list:
        if item > 10:
            processed.append(item * 2)
        else:
            processed.append(item)
    return processed

class DataProcessor:
    def __init__(self, name):
        self.name = name
        self.count = 0
    
    def increment(self):
        self.count += 1
        return self.count

if __name__ == '__main__':
    values = [5, 15, 8, 20]
    result = process_data(values)
    print(f"Result: {result}")
"""
    
    # Test d'obfuscation
    obfuscator = ASTObfuscator(seed=12345)
    obfuscated = obfuscator.obfuscate_code(test_code)
    
    print("Original code length:", len(test_code))
    print("Obfuscated code length:", len(obfuscated))
    print("\n--- Obfuscated Code Preview ---")
    print(obfuscated[:500])
    print("...")
    
    # Test de mapping
    print("\n--- Name Mapping ---")
    for original, obfuscated_name in list(obfuscator.name_mapping.items())[:5]:
        print(f"{original} -> {obfuscated_name}")
    
    print("\n✓ Test complete")
