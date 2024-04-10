import ast
import os

def extract_strings(lst):
    strings = set()
    for item in lst:
        if isinstance(item, str):
            strings.add(item)
        elif isinstance(item, list):
            strings.update(extract_strings(item))
    return list(strings)

def get_import_statements(code):
    tree = ast.parse(code)
    transformer = ReplaceTryNodeTransformer()
    new_tree = transformer.visit(tree)
    code = ast.unparse(new_tree)
    imports = []
    root = ast.parse(code)
    visitor = ImportVisitor()
    visitor.visit(root)
    
    for node in visitor.import_nodes:
        if isinstance(node, ast.Import):
            for alias in node.names:
                import_str = "import {}".format(alias.name)
                imports.append(import_str)
        elif isinstance(node, ast.ImportFrom):
            module_name = node.module if node.module is not None else ""
            for alias in node.names:
                import_str = "from {} import {}".format(module_name, alias.name)
                imports.append(import_str)
    return extract_strings(imports)

class ImportVisitor(ast.NodeVisitor):
    """
    AST Visitor class that marks Import and ImportFrom nodes that are not inside try/except or if/else blocks.
    """
    def __init__(self):
        self.import_nodes = []
        self.current_block = False
        
    def visit_Import(self, node):
        if not self.current_block:
            self.import_nodes.append(node)
        self.generic_visit(node)
        
    def visit_ImportFrom(self, node):
        if not self.current_block:
            self.import_nodes.append(node)
        self.generic_visit(node)
        
    def visit_Try(self, node):
        previous_block = self.current_block
        self.current_block = True
        self.generic_visit(node)
        self.current_block = previous_block

        
    def visit_If(self, node):
        previous_block = self.current_block
        self.current_block = True
        self.generic_visit(node)
        self.current_block = previous_block

class ReplaceTryNodeTransformer(ast.NodeTransformer):
    def visit_Try(self, node):
        if len(node.finalbody) > 0:
            if not (isinstance(node.finalbody[0],ast.Pass) and len(node.finalbody) == 1):
                final_ret = ''
                final_ret += ast.unparse(node.finalbody)
                final_ret += '\ntry:\n'
                final_ret += '\n'.join(['    ' + line for line in ast.unparse(node.body).split('\n')])
                if len(node.handlers) > 0:
                    final_ret += '\n' + ast.unparse(node.handlers)
                if len(node.orelse) > 0:
                    final_ret += '\nelse:\n'
                    final_ret += '\n'.join(['    ' + line for line in ast.unparse(node.orelse).split('\n')])
                final_ret += '\nfinally:\n    pass'
                new_tree = ast.parse(final_ret)
                return ast.NodeTransformer.generic_visit(self,new_tree)
            else:
                return ast.NodeTransformer.generic_visit(self, node)
        else:
            return ast.NodeTransformer.generic_visit(self, node)
    def generic_visit(self, node):
        return ast.NodeTransformer.generic_visit(self, node)

def get_blocks(code):
    if code == '':
        return []
    blocks = []
    tree = ast.parse(code)
    transformer = ReplaceTryNodeTransformer()
    new_tree = transformer.visit(tree)
    code = ast.unparse(new_tree)
    root = ast.parse(code)
    visitor = BlocksVisitor()
    visitor.visit(root)
    for node in visitor.block_nodes:
        if isinstance(node, ast.Try):
            blocks.append(ast.unparse(node))
        elif isinstance(node, ast.If):
            blocks.append(ast.unparse(node))
        else:
            add = get_blocks(ast.unparse(node))
            if len(add) > 0:
                blocks.append(add)
    return extract_strings(blocks)

class BlocksVisitor(ast.NodeVisitor):
    def __init__(self):
        self.block_nodes = []
        self.current_block = False
        
    def visit_Try(self, node):

        if not self.current_block:
            self.block_nodes.append(node)
            self.current_block = True
        self.generic_visit(node)
        self.current_block = False

    def visit_If(self, node):
        if not self.current_block:
            self.block_nodes.append(node)
            self.current_block = True
        self.generic_visit(node)
        self.current_block = False

def saperate_code(code):
    tree = ast.parse(code)

    blocks = []
    tmp = []
    end_flag = 0
    if isinstance(tree.body[0],ast.If):
        while True:
            for node in ast.walk(tree):
                if isinstance(node,ast.If):
                    blocks.append(ast.unparse(node.body))
                    if ast.unparse(node.test) == "__name__ == '__main__'" or ast.unparse(node.test) == "'__main__' == __name__":
                        end_flag = 1
                    elif len(node.orelse) == 0:
                        tmp.append([])
                        end_flag = 1
                    elif isinstance(node.orelse[0],ast.If):
                        tree = ast.parse(ast.unparse(node.orelse))
                    else:
                        tmp.append(ast.unparse(node.orelse))
                        end_flag = 1
                    break
            if end_flag == 1:
                break
        if len(tmp) > 0:
            blocks.append(tmp[-1])
    else:
        for node in ast.walk(tree):
            if isinstance(node, ast.Try):
                blocks.append(ast.unparse(node.body))
                if len(node.handlers) > 0:
                    for handler in node.handlers:
                        blocks.append(ast.unparse(handler.body))
                if len(node.orelse) > 0:
                    temp = blocks[0]
                    temp += '\n{}'.format(ast.unparse(node.orelse))
                    blocks[0] = temp
                break
    return blocks

def process(code):
    retlist = []
    if code == []:
        return []
    if not code.strip() == '':
        outer_ret = get_import_statements(code)
        if not len(outer_ret) == 0:
            retlist.append(outer_ret)
        inner_ret = get_blocks(code)
        if not len(inner_ret) == 0:
            for i in inner_ret:
                ret_code = []
                sp_code = saperate_code(i)
                if not len(sp_code) == 0:
                    for j in sp_code:
                        ret_code.append(process(j))
                retlist.append(ret_code)
    return retlist

def is_nested_empty_list(l):
    if isinstance(l, list):
        if len(l) == 0:
            return True
        else:
            return all(is_nested_empty_list(i) for i in l)
    else:
        return False

def get_array(path):
    with open(path,'r') as r1:
        code = r1.read()
    retlist = get_blocks(code)
    if len(retlist) == 0:
        return []
    else:
        final = []
        for ret in retlist:
            out = []
            inner_ret = saperate_code(ret)
            for inner in inner_ret:
                out.append(process(inner))
            if not is_nested_empty_list(out):
                final.append(out)
        return final