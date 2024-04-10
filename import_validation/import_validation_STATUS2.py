# -*- coding: utf-8 -*-
# This code must run in the context of Python 2.7
import ast
import os
import json
import time
import threading
import import_validation_STATUS2_help as friend
import pickle
from concurrent.futures import ThreadPoolExecutor

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

def process_package(package):
    p = package[0]
    v = package[1]
    file = "{}/{}/{}".format(work_dir, p, v)
    if os.path.exists('{}/STATUS1'.format(file)):
        if os.path.exists("{}/all_python2.txt".format(file)):
            all_paths = []
            all_imports = []
            wrong_code = []
            all_try_if_statements = []
            with open("{}/all_python2.txt".format(file), 'r') as f:
                all_paths = [line.strip() for line in f.readlines()]
            for path in all_paths:
                try:
                    with open(path,'r') as r1:
                        code = r1.read()
                    add = friend.get_import_statements(code)
                    all_imports.extend(add)
                    add1 = friend.get_array(path)
                    if not len(add1) == 0:
                        all_try_if_statements.extend(add1)
                except:
                    wrong_code.append(path)
            if len(wrong_code) > 0:
                print 'Have wrong_code! {}:{}'.format(file,wrong_code)
                if not os.path.exists('{}/wrong_code.txt'.format(file)):
                    os.system('touch {}/wrong_code.txt'.format(file))
                with open('{}/wrong_code.txt'.format(file),'w') as w1:
                    for i in wrong_code:
                        w1.write("{}\n".format(i))
            all_imports = list(set(all_imports))
            with open('{}/all_imports.py'.format(file),'a') as ad:
                for i in all_imports:
                    ad.write("{}\n".format(i))
            if not os.path.exists("{}/all_blocks".format(file)):
                os.system('mkdir {}/all_blocks'.format(file))
            cnt = len(os.listdir('{}/all_blocks'.format(file)))
            for i in range(len(all_try_if_statements)):
                with open('{}/all_blocks/{}.pkl'.format(file,i + cnt), 'wb') as f:
                    pickle.dump(all_try_if_statements[i], f, protocol=2)
        else:
            print "STATUS WRONG:{}".format(file)
        if not os.path.exists('{}/wrong_code.txt'.format(file)):
            os.remove('{}/STATUS1'.format(file))
            os.system('touch {}/STATUS2'.format(file))
            print "Execute OK! {}".format(file)
        else:
            os.remove('{}/STATUS1'.format(file))
            os.system('touch {}/STATUS1_5'.format(file))

if __name__ == '__main__':
    work_dir = '../docker_workdir/pypi_packages'
    STATUS0_file_path = 'status_file/STATUS0.json'
    STATUS1_file_path = 'status_file/STATUS1.json'
    with ThreadPoolExecutor(max_workers=100) as executor:
        futures = []
        content = []
        with open(STATUS0_file_path,'r') as u:
            content0 = json.load(u)
            content = content0['2']
            content.extend(content0['2.7'])
            content.extend(content0['3'])
            content.extend(content0['3.3'])
            content.extend(content0['3.4'])
            content.extend(content0['3.5'])
            content.extend(content0['3.6'])
            content.extend(content0['3.7'])
            content.extend(content0['3.8'])
            content.extend(content0['3.9'])
            content.extend(content0['3.10'])
            content.extend(content0['unknown'])
        with open(STATUS1_file_path,'r') as u1:
            content1 = json.load(u1)
            content.extend(content1['2'])
            content.extend(content1['2.7'])
            content.extend(content1['3'])
            content.extend(content1['3.3'])
            content.extend(content1['3.4'])
            content.extend(content1['3.5'])
            content.extend(content1['3.6'])
            content.extend(content1['3.7'])
            content.extend(content1['3.8'])
            content.extend(content1['3.9'])
            content.extend(content1['3.10'])
            content.extend(content1['unknown'])
        for con in content:
            futures.append(executor.submit(process_package,con))
        for future in futures:
            future.result()
    print "finish!"
    print time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))