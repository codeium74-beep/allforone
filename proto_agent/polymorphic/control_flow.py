"""
Control Flow Flattener - Aplatissement du flux de contrôle
Transforme les structures if/else/while en state machines pour complexifier l'analyse statique
"""
import ast
import astor
import random
from typing import List, Dict, Optional


class ControlFlowFlattener:
    """
    Aplatit le flux de contrôle en transformant les structures conditionnelles
    en machines à états, rendant l'analyse du code beaucoup plus difficile
    """
    
    def __init__(self):
        self.state_counter = 0
        self.flattened_functions = []
    
    def flatten_code(self, source_code: str) -> str:
        """
        Aplatit le flux de contrôle du code
        
        Args:
            source_code: Code Python source
        
        Returns:
            Code avec flux de contrôle aplati
        """
        try:
            tree = ast.parse(source_code)
            
            # Transformation
            tree = self._flatten_functions(tree)
            
            # Régénération
            flattened_code = astor.to_source(tree)
            
            return flattened_code
            
        except Exception as e:
            print(f"[ControlFlowFlattener] Flattening failed: {e}")
            return source_code
    
    def _flatten_functions(self, tree: ast.Module) -> ast.Module:
        """Aplatit les fonctions du module"""
        flattener = FunctionFlattener()
        tree = flattener.visit(tree)
        return tree


class FunctionFlattener(ast.NodeTransformer):
    """Transforme les fonctions en machines à états"""
    
    def __init__(self):
        self.state_var = "_state"
        self.next_state = 0
    
    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        """Aplatit une fonction"""
        # Ne pas aplatir les fonctions trop simples (< 3 statements)
        if len(node.body) < 3:
            self.generic_visit(node)
            return node
        
        # Ne pas aplatir avec une probabilité de 70% (pour éviter de tout casser)
        if random.random() < 0.7:
            self.generic_visit(node)
            return node
        
        # Extraction des statements de la fonction
        original_body = node.body
        
        # Création de la state machine
        state_machine = self._create_state_machine(original_body)
        
        # Remplacement du corps de la fonction
        node.body = state_machine
        
        return node
    
    def _create_state_machine(self, statements: List[ast.stmt]) -> List[ast.stmt]:
        """Crée une state machine à partir d'une liste de statements"""
        # Initialisation de la variable d'état
        state_init = ast.Assign(
            targets=[ast.Name(id=self.state_var, ctx=ast.Store())],
            value=ast.Constant(value=0)
        )
        
        # Création des états
        states = {}
        for i, stmt in enumerate(statements):
            states[i] = stmt
        
        # Construction du switch case (if/elif/else)
        state_checks = []
        
        for state_num, stmt in states.items():
            # Condition: if _state == state_num
            condition = ast.Compare(
                left=ast.Name(id=self.state_var, ctx=ast.Load()),
                ops=[ast.Eq()],
                comparators=[ast.Constant(value=state_num)]
            )
            
            # Corps: exécuter le statement + passer à l'état suivant
            body = [
                stmt,
                ast.Assign(
                    targets=[ast.Name(id=self.state_var, ctx=ast.Store())],
                    value=ast.Constant(value=state_num + 1)
                )
            ]
            
            if state_num == 0:
                # Premier état: if
                state_check = ast.If(
                    test=condition,
                    body=body,
                    orelse=[]
                )
                state_checks.append(state_check)
            else:
                # États suivants: elif imbriqués
                # On construit une chaîne if/elif
                pass
        
        # Construction de la boucle while
        # while _state < len(states):
        #     if _state == 0:
        #         ...
        #     elif _state == 1:
        #         ...
        
        # Simplifié: on utilise un if/elif/else
        if_chain = self._build_if_chain(states)
        
        # Boucle while autour
        while_loop = ast.While(
            test=ast.Compare(
                left=ast.Name(id=self.state_var, ctx=ast.Load()),
                ops=[ast.Lt()],
                comparators=[ast.Constant(value=len(states))]
            ),
            body=[if_chain],
            orelse=[]
        )
        
        return [state_init, while_loop]
    
    def _build_if_chain(self, states: Dict[int, ast.stmt]) -> ast.If:
        """Construit une chaîne if/elif/else pour les états"""
        # Construction récursive de la chaîne
        first_state = 0
        
        def build_chain(state_num: int) -> Optional[ast.If]:
            if state_num >= len(states):
                return None
            
            stmt = states[state_num]
            
            # Condition
            condition = ast.Compare(
                left=ast.Name(id=self.state_var, ctx=ast.Load()),
                ops=[ast.Eq()],
                comparators=[ast.Constant(value=state_num)]
            )
            
            # Corps
            body = [
                stmt,
                ast.Assign(
                    targets=[ast.Name(id=self.state_var, ctx=ast.Store())],
                    value=ast.Constant(value=state_num + 1)
                )
            ]
            
            # Récursion pour elif
            next_chain = build_chain(state_num + 1)
            
            return ast.If(
                test=condition,
                body=body,
                orelse=[next_chain] if next_chain else []
            )
        
        chain = build_chain(first_state)
        return chain if chain else ast.Pass()


class SwitchCaseGenerator:
    """Génère des structures switch/case simulées (dictionnaire de fonctions)"""
    
    @staticmethod
    def generate_switch(cases: Dict[int, ast.stmt]) -> List[ast.stmt]:
        """
        Génère un switch/case en Python via dictionnaire
        
        Args:
            cases: Dictionnaire {case_value: statement}
        
        Returns:
            Liste de statements implémentant le switch
        """
        # Création d'un dictionnaire de lambdas
        # switch_dict = {0: lambda: stmt0(), 1: lambda: stmt1(), ...}
        
        # Pour simplifier, on utilise un if/elif classique
        # (la vraie implémentation switch via dict nécessite plus de transformation)
        
        switch_statements = []
        
        for case_value, stmt in cases.items():
            condition = ast.Compare(
                left=ast.Name(id="_case", ctx=ast.Load()),
                ops=[ast.Eq()],
                comparators=[ast.Constant(value=case_value)]
            )
            
            if_stmt = ast.If(
                test=condition,
                body=[stmt],
                orelse=[]
            )
            
            switch_statements.append(if_stmt)
        
        return switch_statements


class LoopObfuscator:
    """Obfusque les boucles for/while"""
    
    @staticmethod
    def obfuscate_for_loop(node: ast.For) -> ast.While:
        """
        Transforme une boucle for en while équivalente
        
        for i in range(n):
            body
        
        devient:
        
        i = 0
        while i < n:
            body
            i += 1
        """
        # Extraction des éléments
        target = node.target
        iter_call = node.iter
        body = node.body
        
        # Initialisation
        init = ast.Assign(
            targets=[target],
            value=ast.Constant(value=0)
        )
        
        # Condition (simplifiée pour range)
        # On suppose iter_call est range(n)
        if isinstance(iter_call, ast.Call) and hasattr(iter_call.func, 'id'):
            if iter_call.func.id == 'range' and len(iter_call.args) > 0:
                limit = iter_call.args[0]
            else:
                # Fallback
                return node  # Ne pas transformer
        else:
            return node
        
        # Condition while
        condition = ast.Compare(
            left=target,
            ops=[ast.Lt()],
            comparators=[limit]
        )
        
        # Incrémentation
        increment = ast.AugAssign(
            target=target,
            op=ast.Add(),
            value=ast.Constant(value=1)
        )
        
        # Corps modifié (avec incrémentation à la fin)
        new_body = body + [increment]
        
        # Construction du while
        while_loop = ast.While(
            test=condition,
            body=new_body,
            orelse=node.orelse
        )
        
        # Retourner une séquence (init + while)
        # Note: cela nécessite d'être dans un contexte qui accepte plusieurs statements
        return while_loop


def flatten_file(input_file: str, output_file: str) -> bool:
    """
    Aplatit le flux de contrôle d'un fichier
    
    Args:
        input_file: Fichier source
        output_file: Fichier de sortie
    
    Returns:
        True si succès
    """
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            source = f.read()
        
        flattener = ControlFlowFlattener()
        flattened = flattener.flatten_code(source)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(flattened)
        
        print(f"[ControlFlowFlattener] Flattened {input_file} -> {output_file}")
        return True
        
    except Exception as e:
        print(f"[ControlFlowFlattener] Failed: {e}")
        return False


if __name__ == '__main__':
    # Test
    print("=== Control Flow Flattener Test ===\n")
    
    test_code = """
def process_values(data):
    result = 0
    for i in range(len(data)):
        if data[i] > 10:
            result += data[i]
        else:
            result -= data[i]
    return result

def check_status(value):
    if value > 100:
        print("High")
    elif value > 50:
        print("Medium")
    else:
        print("Low")
    return value * 2
"""
    
    flattener = ControlFlowFlattener()
    flattened = flattener.flatten_code(test_code)
    
    print("Original:")
    print(test_code)
    print("\n" + "="*50 + "\n")
    print("Flattened:")
    print(flattened[:800])
    
    print("\n✓ Test complete")
