"""
Polymorphic Engine - Système d'obfuscation et de mutation avancé
"""
from .ast_obfuscator import ASTObfuscator, obfuscate_file
from .control_flow import ControlFlowFlattener, flatten_file
from .string_obfuscation import StringObfuscator, obfuscate_strings_in_file
from .dead_code import DeadCodeGenerator, inject_dead_code_in_file

__all__ = [
    'ASTObfuscator',
    'obfuscate_file',
    'ControlFlowFlattener',
    'flatten_file',
    'StringObfuscator',
    'obfuscate_strings_in_file',
    'DeadCodeGenerator',
    'inject_dead_code_in_file',
    'PolymorphicPipeline'
]


class PolymorphicPipeline:
    """
    Pipeline complet d'obfuscation polymorphe
    Applique toutes les transformations dans un ordre optimal
    """
    
    def __init__(self, config: dict = None):
        self.config = config or {}
        
        # Configuration des transformations
        self.enable_ast_obfuscation = self.config.get('ast_obfuscation', True)
        self.enable_string_obfuscation = self.config.get('string_obfuscation', True)
        self.enable_control_flow = self.config.get('control_flow', True)
        self.enable_dead_code = self.config.get('dead_code', True)
        
        # Paramètres
        self.string_obfuscation_rate = self.config.get('string_rate', 0.8)
        self.dead_code_rate = self.config.get('dead_code_rate', 0.15)
        self.ast_seed = self.config.get('ast_seed', None)
    
    def transform(self, source_code: str) -> str:
        """
        Applique toutes les transformations polymorphes
        
        Args:
            source_code: Code Python source
        
        Returns:
            Code obfusqué
        """
        code = source_code
        
        print("[PolymorphicPipeline] Starting transformation pipeline...")
        
        # Étape 1: Obfuscation des strings (avant AST pour préserver la validité)
        if self.enable_string_obfuscation:
            print("[PolymorphicPipeline] 1/4 String obfuscation...")
            obfuscator = StringObfuscator(self.string_obfuscation_rate)
            code = obfuscator.obfuscate_code(code)
        
        # Étape 2: Injection de code mort
        if self.enable_dead_code:
            print("[PolymorphicPipeline] 2/4 Dead code injection...")
            generator = DeadCodeGenerator(self.dead_code_rate)
            code = generator.inject_into_code(code)
        
        # Étape 3: Obfuscation AST (renommage, réorganisation)
        if self.enable_ast_obfuscation:
            print("[PolymorphicPipeline] 3/4 AST obfuscation...")
            ast_obfuscator = ASTObfuscator(seed=self.ast_seed)
            code = ast_obfuscator.obfuscate_code(code)
        
        # Étape 4: Aplatissement du flux de contrôle (dernier pour éviter de casser)
        if self.enable_control_flow:
            print("[PolymorphicPipeline] 4/4 Control flow flattening...")
            flattener = ControlFlowFlattener()
            code = flattener.flatten_code(code)
        
        print("[PolymorphicPipeline] ✓ Transformation complete")
        
        return code
    
    def transform_file(self, input_file: str, output_file: str) -> bool:
        """
        Transforme un fichier complet
        
        Args:
            input_file: Fichier source
            output_file: Fichier de sortie
        
        Returns:
            True si succès
        """
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                source = f.read()
            
            transformed = self.transform(source)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(transformed)
            
            print(f"[PolymorphicPipeline] Successfully transformed {input_file} -> {output_file}")
            return True
            
        except Exception as e:
            print(f"[PolymorphicPipeline] Failed to transform file: {e}")
            return False
    
    def get_transformation_stats(self, original_code: str, transformed_code: str) -> dict:
        """Retourne des statistiques sur les transformations"""
        return {
            'original_size': len(original_code),
            'transformed_size': len(transformed_code),
            'size_increase': len(transformed_code) - len(original_code),
            'size_increase_percent': ((len(transformed_code) / len(original_code)) - 1) * 100,
            'original_lines': original_code.count('\n') + 1,
            'transformed_lines': transformed_code.count('\n') + 1,
            'ast_obfuscation': self.enable_ast_obfuscation,
            'string_obfuscation': self.enable_string_obfuscation,
            'control_flow': self.enable_control_flow,
            'dead_code': self.enable_dead_code
        }


if __name__ == '__main__':
    # Test du pipeline complet
    print("=== Polymorphic Pipeline Test ===\n")
    
    test_code = """
import random
import time

def authenticate(username, password):
    if username == "admin" and password == "secret":
        return True
    return False

def process_data(data_list):
    result = []
    for item in data_list:
        if item > 10:
            result.append(item * 2)
        else:
            result.append(item)
    return result

class UserManager:
    def __init__(self):
        self.users = {}
    
    def add_user(self, name):
        self.users[name] = {"active": True}
    
    def remove_user(self, name):
        if name in self.users:
            del self.users[name]

if __name__ == '__main__':
    manager = UserManager()
    manager.add_user("alice")
    print("User added")
"""
    
    # Configuration complète
    config = {
        'ast_obfuscation': True,
        'string_obfuscation': True,
        'control_flow': True,
        'dead_code': True,
        'string_rate': 0.8,
        'dead_code_rate': 0.2,
        'ast_seed': 12345
    }
    
    pipeline = PolymorphicPipeline(config)
    
    # Transformation
    print("Transforming code...\n")
    transformed = pipeline.transform(test_code)
    
    # Statistiques
    stats = pipeline.get_transformation_stats(test_code, transformed)
    
    print("\n=== Transformation Statistics ===")
    for key, value in stats.items():
        print(f"{key}: {value}")
    
    print("\n=== Transformed Code Preview ===")
    print(transformed[:800])
    print("...")
    
    print("\n✓ Test complete")
