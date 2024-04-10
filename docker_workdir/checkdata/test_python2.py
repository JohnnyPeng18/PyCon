# -*- coding: utf-8 -*-
from __future__ import print_function
import sys
import traceback

if sys.version_info[0] < 3:
    def print(*args):
        sep = ' '
        end = '\n'
        file = sys.stdout
        if args and isinstance(args[-1], file.__class__):
            file = args[-1]
            args = args[:-1]
        if args and isinstance(args[-1], str):
            end = ''
        output = sep.join(map(str, args)) + end
        file.write(output)

import os
import json

def is_final(part):
    all_self_names = []
    all_self_names1 = []
    with open('/root/envdep/all_rela.txt','r') as r1:
        all_self_names = [line.strip() for line in r1.readlines()]
        for item in all_self_names:
            all_self_names1 += item.split('.')
            all_self_names1 = list(set(all_self_names1))
    dlt = []
    if part[:6] == 'from  ':
        dlt.append(part)
        return False
    if part[:4] == 'from':
        p = part.split()
        p = [i.split('.') for i in p]
        p = [j for i in p for j in i]
        if "import" in p:
            index = p.index("import")
            del p[index]
            for p1 in p:
                if p1 in all_self_names1:
                    return False
            return True
        else:
            print('WRONG INPUT1:{}'.format(part)) 
            return False
    elif part[:6] == 'import':
        p = part.split()
        p = [i.split('.') for i in p]
        p = [j for i in p for j in i]
        for p1 in p:
            if p1 in all_self_names1:
                return False
        return True
    else:
        print('WRONG INPUT2:{}'.format(part)) 
        return False

def test1(l,tp):
    if len(l) == 0:
        return True
    if isinstance(l[0],unicode) or isinstance(l[0],str):
        pass_flag = 1
        for i in l:
            try:
                if is_final(i):
                    exec(i)
            except:
                pass_flag = 0
                break
        if pass_flag == 1:
            return True
        else:
            return False
    else:
        if tp == 'or':
            ret = False
            for i in l:
                ret = ret or test1(i,'and')
                if ret == True:
                    break
            if ret == True:
                return True
            else:
                return False
        else:
            ret = True
            for i in l:
                ret = ret and test1(i,'or')
                if ret == False:
                    break
            if ret == True:
                return True
            else:
                return False

fail_list = []
with open('/root/envdep/all_imports_final.py','r') as r1:
    lines = [line.strip() for line in r1.readlines()]

fail_reason = {}
for i in lines:
    try:
        exec(i)
    except Exception as e:
        fail_list.append(i)
        error_message = traceback.format_exc()
        fail_reason['{}'.format(i)] = ['{}'.format(type(e).__name__),'{}'.format(e),'{}'.format(error_message)]

fail_blocks = []
blocks = []
all_json = os.listdir('/root/envdep/all_blocks_json')

if not len(all_json) == 0:
    for i in range(len(all_json)):
        path1 = '/root/envdep/all_blocks_json/{}.json'.format(i)
        with open(path1,'r') as r1:
            blocks.append(json.load(r1))

if not len(all_json) == 0:
    for i in range(len(blocks)):
        flag = test1(blocks[i],'or')
        print(blocks[i])
        print(flag)
        if not flag:
            fail_blocks.append(i)

if os.path.exists('/root/envdep/fail_run.py'):
    os.remove('/root/envdep/fail_run.py')
if os.path.exists('/root/envdep/fail_blocks.txt'):
    os.remove('/root/envdep/fail_blocks.txt')
if os.path.exists('/root/envdep/fail_reason.json'):
    os.remove('/root/envdep/fail_reason.json')
if os.path.exists('/root/envdep/TASK3_FAIL_PIP'):
    os.remove('/root/envdep/TASK3_FAIL_PIP')
if os.path.exists('/root/envdep/TASK3_FAIL_RUN'):
    os.remove('/root/envdep/TASK3_FAIL_RUN')


uid = os.getuid()
gid = os.getgid()


if not len(fail_list) == 0:
    if not os.path.exists('/root/envdep/fail_run.py'):
        os.system('touch /root/envdep/fail_run.py')
        os.system('chown {}:{} /root/envdep/fail_run.py'.format(uid,gid))
    with open('/root/envdep/fail_run.py','w') as w1:
        for i in fail_list:
            w1.write("{}\n".format(i))
    
    if not os.path.exists('/root/envdep/fail_reason.json'):
        os.system('touch /root/envdep/fail_reason.json')
        os.system('chown {}:{} /root/envdep/fail_reason.json'.format(uid,gid))
    with open('/root/envdep/fail_reason.json','w') as w2:
        json.dump(fail_reason, w2, indent=4, sort_keys=True)

if not len(fail_blocks) == 0:
    if not os.path.exists('/root/envdep/fail_blocks.txt'):
        os.system('touch /root/envdep/fail_blocks.txt')
        os.system('chown {}:{} /root/envdep/fail_blocks.txt'.format(uid,gid))
    with open('/root/envdep/fail_blocks.txt','w') as w2:
        for i in range(len(fail_blocks)):
            w2.write('{}\n'.format(fail_blocks[i]))

if not os.path.exists('/root/envdep/fail_run.py') and not os.path.exists('/root/envdep/fail_blocks.txt'):
    os.system('touch /root/envdep/TASK3_OK')
    os.system('chown {}:{} /root/envdep/TASK3_OK'.format(uid,gid))