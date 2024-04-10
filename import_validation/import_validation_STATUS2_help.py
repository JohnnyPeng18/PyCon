# -*- coding: utf-8 -*-
# This code must run in the context of Python 2.7
import ast
import astor
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
    code = astor.to_source(new_tree)
    
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
        super(ImportVisitor, self).__init__()
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
    
    def visit_TryExcept(self, node):
        previous_block = self.current_block
        self.current_block = True
        self.generic_visit(node)
        self.current_block = previous_block
    
    def visit_TryFinally(self, node):
        previous_block = self.current_block
        self.current_block = True
        if len(node.finalbody) > 0:
            self.import_nodes.extend(node.finalbody)
        self.generic_visit(node)
        self.current_block = previous_block
        
    def visit_If(self, node):
        previous_block = self.current_block
        self.current_block = True
        self.generic_visit(node)
        self.current_block = previous_block

class ReplaceTryNodeTransformer(ast.NodeTransformer):
    def visit_TryFinally(self, node):
        if isinstance(node.finalbody[0], ast.Pass) and len(node.finalbody) == 1:
            return ast.NodeTransformer.generic_visit(self, node)
        elif isinstance(node.body[0], ast.TryExcept) and len(node.body) == 1:
            final_ret = ''
            for i in range(len(node.finalbody)):
                final_ret += astor.to_source(node.finalbody[i])
            for i in range(len(node.body)):
                final_ret += astor.to_source(node.body[i])
            final_ret += '\nfinally:\n    pass\n'
            new_tree = ast.parse(final_ret)
            return ast.NodeTransformer.generic_visit(self, new_tree)
        else:
            final_ret = ''
            for i in range(len(node.finalbody)):
                final_ret += astor.to_source(node.finalbody[i])
            final_ret += 'try:\n'
            for i in range(len(node.body)):
                lines = astor.to_source(node.body[i]).split('\n')
                for j in lines:
                    final_ret += '    {}\n'.format(j)
            final_ret += '\nfinally:\n    pass\n'
            new_tree = ast.parse(final_ret)
            return ast.NodeTransformer.generic_visit(self, new_tree)
    def generic_visit(self, node):
        return ast.NodeTransformer.generic_visit(self, node)

def get_blocks(code):
    if code == '':
        return []
    blocks = []
    tree = ast.parse(code)
    transformer = ReplaceTryNodeTransformer()
    new_tree = transformer.visit(tree)
    code = astor.to_source(new_tree)
    root = ast.parse(code)
    visitor = BlocksVisitor()
    visitor.visit(root)
    for node in visitor.block_nodes:
        if isinstance(node, ast.TryExcept):
            blocks.append(astor.to_source(node))
        elif isinstance(node, ast.TryFinally):
            blocks.append(astor.to_source(node))
        elif isinstance(node, ast.If):
            blocks.append(astor.to_source(node))
        else:
            add = get_blocks(astor.to_source(node))
            if len(add) > 0:
                blocks.append(add)
    return extract_strings(blocks)

class BlocksVisitor(ast.NodeVisitor):
    def __init__(self):
        self.block_nodes = []
        self.current_block = False
    def visit_TryExcept(self, node):
        if not self.current_block:
            self.block_nodes.append(node)
            self.current_block = True
        self.generic_visit(node)
        self.current_block = False

    def visit_TryFinally(self, node):
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
                    tmp_body = ''
                    for i in range(len(node.body)):
                        tmp_body += astor.to_source(node.body[i])
                    blocks.append(tmp_body.strip())
                    if astor.to_source(node.test).strip().strip('()') == "__name__ == '__main__'" or astor.to_source(node.test).strip().strip('()') == "'__main__' == __name__":
                        end_flag = 1
                    elif len(node.orelse) == 0:
                        tmp.append([])
                        end_flag = 1
                    elif len(node.orelse) > 0 and isinstance(node.orelse[0],ast.If):
                        tree = ast.parse(astor.to_source(node.orelse[0]).strip())
                    else:
                        if not len(node.orelse) == 0:
                            tmp_orelse = ''
                            for i in range(len(node.orelse)):
                                tmp_orelse += astor.to_source(node.orelse[i])
                            tmp.append(tmp_orelse.strip())
                        end_flag = 1
                    break
            if end_flag == 1:
                break
        if len(tmp) > 0:
            blocks.append(tmp[-1])
    else:
        for node in ast.walk(tree):
            if isinstance(node, ast.TryExcept):
                tmp_body = ''
                for i in range(len(node.body)):
                    tmp_body += astor.to_source(node.body[i])
                blocks.append(tmp_body.strip())
                for handler in node.handlers:
                    tmp_handler = ''
                    for i in range(len(handler.body)):
                        tmp_handler += astor.to_source(handler.body[i])
                    blocks.append(tmp_handler.strip())
                if not len(node.orelse) == 0:
                    if not astor.to_source(node.orelse[0]).strip() == '':
                        tmp_orelse = ''
                        for i in range(len(node.orelse)):
                            tmp_orelse += astor.to_source(node.orelse[i])
                        blocks[0] += '\n{}'.format(tmp_orelse.strip())
                break
            elif isinstance(node, ast.TryFinally):
                tmp_body = ''
                for i in range(len(node.body)):
                    tmp_body += astor.to_source(node.body[i])
                blocks.append(tmp_body.strip())
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