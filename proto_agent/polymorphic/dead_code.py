"""
Dead Code Generator - Génération de code mort
Injecte du code jamais exécuté pour complexifier l'analyse
"""
import ast
import astor
import random
from typing import List


class DeadCodeGenerator:
    """
    Génère et injecte du code mort sophistiqué:
    - Fonctions jamais appelées
    - Variables jamais utilisées
    - Boucles jamais exécutées
    - Branches conditionnelles impossibles
    """
    
    def __init__(self, injection_rate: float = 0.15):
        """
        Args:
            injection_rate: Probabilité d'injecter du code mort
        """
        self.injection_rate = injection_rate
    
    def inject_into_code(self, source_code: str) -> str:
        """Injecte du code mort dans le code source"""
        try:
            tree = ast.parse(source_code)
            
            # Injection
            injector = DeadCodeInjector(self.injection_rate)
            tree = injector.visit(tree)
            
            # Régénération
            modified = astor.to_source(tree)
            
            return modified
            
        except Exception as e:
            print(f"[DeadCodeGenerator] Failed: {e}")
            return source_code
    
    @staticmethod
    def generate_dead_function() -> ast.FunctionDef:
        """Génère une fonction morte"""
        func_name = f"_unused_func_{random.randint(1000, 9999)}"
        
        # Corps aléatoire
        body = [
            ast.Assign(
                targets=[ast.Name(id="_x", ctx=ast.Store())],
                value=ast.Constant(value=random.randint(0, 1000))
            ),
            ast.Return(value=ast.Name(id="_x", ctx=ast.Load()))
        ]
        
        return ast.FunctionDef(
            name=func_name,
            args=ast.arguments(
                posonlyargs=[],
                args=[],
                kwonlyargs=[],
                kw_defaults=[],
                defaults=[]
            ),
            body=body,
            decorator_list=[]
        )
    
    @staticmethod
    def generate_dead_class() -> ast.ClassDef:
        """Génère une classe morte"""
        class_name = f"_UnusedClass{random.randint(1000, 9999)}"
        
        # Méthode __init__
        init_method = ast.FunctionDef(
            name="__init__",
            args=ast.arguments(
                posonlyargs=[],
                args=[ast.arg(arg="self", annotation=None)],
                kwonlyargs=[],
                kw_defaults=[],
                defaults=[]
            ),
            body=[
                ast.Assign(
                    targets=[ast.Attribute(
                        value=ast.Name(id="self", ctx=ast.Load()),
                        attr="_value",
                        ctx=ast.Store()
                    )],
                    value=ast.Constant(value=0)
                )
            ],
            decorator_list=[]
        )
        
        return ast.ClassDef(
            name=class_name,
            bases=[],
            keywords=[],
            body=[init_method],
            decorator_list=[]
        )
    
    @staticmethod
    def generate_impossible_condition() -> ast.If:
        """Génère une condition impossible (toujours fausse)"""
        # Conditions impossibles variées
        impossible_conditions = [
            # False
            ast.Constant(value=False),
            # 1 > 2
            ast.Compare(
                left=ast.Constant(value=1),
                ops=[ast.Gt()],
                comparators=[ast.Constant(value=2)]
            ),
            # "a" == "b"
            ast.Compare(
                left=ast.Constant(value="a"),
                ops=[ast.Eq()],
                comparators=[ast.Constant(value="b")]
            ),
            # [] and True
            ast.BoolOp(
                op=ast.And(),
                values=[ast.List(elts=[], ctx=ast.Load()), ast.Constant(value=True)]
            )
        ]
        
        condition = random.choice(impossible_conditions)
        
        # Corps (du code qui ne sera jamais exécuté)
        body = [
            ast.Assign(
                targets=[ast.Name(id=f"_dead_{random.randint(1000, 9999)}", ctx=ast.Store())],
                value=ast.Constant(value=random.randint(0, 100))
            ),
            ast.Expr(
                value=ast.Call(
                    func=ast.Name(id="print", ctx=ast.Load()),
                    args=[ast.Constant(value="This will never print")],
                    keywords=[]
                )
            )
        ]
        
        return ast.If(
            test=condition,
            body=body,
            orelse=[]
        )
    
    @staticmethod
    def generate_empty_loop() -> ast.For:
        """Génère une boucle sur une séquence vide"""
        return ast.For(
            target=ast.Name(id=f"_unused_iter_{random.randint(1000, 9999)}", ctx=ast.Store()),
            iter=ast.List(elts=[], ctx=ast.Load()),
            body=[
                ast.Assign(
                    targets=[ast.Name(id="_dummy", ctx=ast.Store())],
                    value=ast.Constant(value=1)
                )
            ],
            orelse=[]
        )
    
    @staticmethod
    def generate_fake_import() -> ast.Import:
        """Génère un import fictif (module inexistant)"""
        fake_modules = [
            "_internal_utils",
            "_system_core",
            "_platform_spec",
            "_debug_helpers"
        ]
        
        module = random.choice(fake_modules) + f"_{random.randint(100, 999)}"
        
        return ast.Try(
            body=[
                ast.Import(names=[ast.alias(name=module, asname=None)])
            ],
            handlers=[
                ast.ExceptHandler(
                    type=ast.Name(id="ImportError", ctx=ast.Load()),
                    name=None,
                    body=[ast.Pass()]
                )
            ],
            orelse=[],
            finalbody=[]
        )


class DeadCodeInjector(ast.NodeTransformer):
    """Injecteur de code mort dans l'AST"""
    
    def __init__(self, injection_rate: float):
        self.injection_rate = injection_rate
        self.generators = [
            DeadCodeGenerator.generate_dead_function,
            DeadCodeGenerator.generate_impossible_condition,
            DeadCodeGenerator.generate_empty_loop,
            DeadCodeGenerator.generate_fake_import
        ]
    
    def visit_Module(self, node: ast.Module) -> ast.Module:
        """Injecte du code mort au niveau module"""
        # Injection de fonctions/classes mortes
        if random.random() < self.injection_rate:
            dead_func = DeadCodeGenerator.generate_dead_function()
            # Insertion à une position aléatoire
            insert_pos = random.randint(0, len(node.body))
            node.body.insert(insert_pos, dead_func)
        
        if random.random() < self.injection_rate * 0.5:  # Moins fréquent
            dead_class = DeadCodeGenerator.generate_dead_class()
            insert_pos = random.randint(0, len(node.body))
            node.body.insert(insert_pos, dead_class)
        
        self.generic_visit(node)
        return node
    
    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        """Injecte du code mort dans les fonctions"""
        if len(node.body) > 1 and random.random() < self.injection_rate:
            # Sélection d'un générateur
            generator = random.choice(self.generators)
            
            # Génération et injection
            dead_code = generator()
            insert_pos = random.randint(0, len(node.body))
            node.body.insert(insert_pos, dead_code)
        
        self.generic_visit(node)
        return node


def inject_dead_code_in_file(input_file: str, output_file: str, rate: float = 0.15) -> bool:
    """Injecte du code mort dans un fichier"""
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            source = f.read()
        
        generator = DeadCodeGenerator(injection_rate=rate)
        modified = generator.inject_into_code(source)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(modified)
        
        print(f"[DeadCodeGenerator] Injected dead code: {input_file} -> {output_file}")
        return True
        
    except Exception as e:
        print(f"[DeadCodeGenerator] Failed: {e}")
        return False


if __name__ == '__main__':
    # Test
    print("=== Dead Code Generator Test ===\n")
    
    test_code = """
def calculate(x, y):
    result = x + y
    return result

def main():
    value = calculate(10, 20)
    print(value)
"""
    
    generator = DeadCodeGenerator(injection_rate=0.5)
    modified = generator.inject_into_code(test_code)
    
    print("Original:")
    print(test_code)
    print("\n" + "="*50 + "\n")
    print("With Dead Code:")
    print(modified[:1000])
    
    print("\n✓ Test complete")
