"""
String Obfuscator - Obfuscation des chaînes de caractères
Encode les strings pour éviter la détection par signatures
"""
import ast
import astor
import base64
import random
from typing import List


class StringObfuscator:
    """
    Obfusque les chaînes de caractères via:
    - Encodage Base64
    - Encodage hexadécimal
    - XOR avec clé
    - Séparation et concaténation
    """
    
    def __init__(self, obfuscation_rate: float = 0.8):
        """
        Args:
            obfuscation_rate: Probabilité d'obfusquer une string (0.0-1.0)
        """
        self.obfuscation_rate = obfuscation_rate
        self.xor_key = random.randint(1, 255)
    
    def obfuscate_code(self, source_code: str) -> str:
        """Obfusque les strings dans le code"""
        try:
            tree = ast.parse(source_code)
            
            # Transformation
            transformer = StringTransformer(self.obfuscation_rate, self.xor_key)
            tree = transformer.visit(tree)
            
            # Régénération
            obfuscated = astor.to_source(tree)
            
            return obfuscated
            
        except Exception as e:
            print(f"[StringObfuscator] Failed: {e}")
            return source_code
    
    @staticmethod
    def encode_base64(text: str) -> str:
        """Encode une string en base64"""
        encoded = base64.b64encode(text.encode()).decode()
        return f"__import__('base64').b64decode('{encoded}').decode()"
    
    @staticmethod
    def encode_hex(text: str) -> str:
        """Encode une string en hexadécimal"""
        hex_str = text.encode().hex()
        return f"bytes.fromhex('{hex_str}').decode()"
    
    @staticmethod
    def encode_xor(text: str, key: int) -> str:
        """Encode avec XOR"""
        xored = ''.join(chr(ord(c) ^ key) for c in text)
        xored_hex = xored.encode('latin-1').hex()
        return f"''.join(chr(c ^ {key}) for c in bytes.fromhex('{xored_hex}'))"
    
    @staticmethod
    def split_string(text: str) -> str:
        """Sépare une string et la reconstruit"""
        if len(text) < 4:
            return f"'{text}'"
        
        # Coupe en morceaux
        mid = len(text) // 2
        part1 = text[:mid]
        part2 = text[mid:]
        
        return f"'{part1}' + '{part2}'"


class StringTransformer(ast.NodeTransformer):
    """Transforme les strings dans l'AST"""
    
    def __init__(self, obfuscation_rate: float, xor_key: int):
        self.obfuscation_rate = obfuscation_rate
        self.xor_key = xor_key
        self.methods = [
            StringObfuscator.encode_base64,
            StringObfuscator.encode_hex,
            lambda text: StringObfuscator.encode_xor(text, self.xor_key),
            StringObfuscator.split_string
        ]
    
    def visit_Constant(self, node: ast.Constant) -> ast.AST:
        """Visite les constantes (dont strings)"""
        # Ne traiter que les strings
        if not isinstance(node.value, str):
            return node
        
        # Ne pas obfusquer les strings vides ou très courtes
        if len(node.value) < 2:
            return node
        
        # Ne pas obfusquer les strings de docstrings
        # (détection heuristique: contient des sauts de ligne)
        if '\n' in node.value or len(node.value) > 100:
            return node
        
        # Probabilité d'obfuscation
        if random.random() > self.obfuscation_rate:
            return node
        
        # Sélection de la méthode d'obfuscation
        method = random.choice(self.methods)
        
        try:
            # Génération du code obfusqué
            obfuscated_code = method(node.value)
            
            # Parse en expression
            obfuscated_expr = ast.parse(obfuscated_code, mode='eval').body
            
            return obfuscated_expr
            
        except Exception as e:
            # En cas d'erreur, retourner la string originale
            return node


def obfuscate_strings_in_file(input_file: str, output_file: str, rate: float = 0.8) -> bool:
    """Obfusque les strings d'un fichier"""
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            source = f.read()
        
        obfuscator = StringObfuscator(obfuscation_rate=rate)
        obfuscated = obfuscator.obfuscate_code(source)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(obfuscated)
        
        print(f"[StringObfuscator] Obfuscated strings in {input_file} -> {output_file}")
        return True
        
    except Exception as e:
        print(f"[StringObfuscator] Failed: {e}")
        return False


if __name__ == '__main__':
    # Test
    print("=== String Obfuscator Test ===\n")
    
    test_code = """
def greet(name):
    message = "Hello, " + name
    print(message)
    return "Success"

def process():
    data = "important_data"
    key = "secret_key"
    result = data + key
    return result
"""
    
    obfuscator = StringObfuscator(obfuscation_rate=1.0)
    obfuscated = obfuscator.obfuscate_code(test_code)
    
    print("Original:")
    print(test_code)
    print("\n" + "="*50 + "\n")
    print("Obfuscated:")
    print(obfuscated)
    
    print("\n✓ Test complete")
