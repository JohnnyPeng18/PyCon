import os
import time
from multiprocessing.dummy import Pool as ThreadPool
from concurrent.futures import ThreadPoolExecutor
import pickle
import json

def tuple_if_list(lst):
    if isinstance(lst, list):
        return tuple(sorted(map(tuple_if_list, lst), key=str))
    else:
        return lst

def remove_duplicates(lst):
    seen = set()
    result = []
    for item in lst:
        item_tuple = tuple_if_list(item)
        if item_tuple not in seen:
            seen.add(item_tuple)
            result.append(item)
    return result

def process_package(package):
    p = package[0]
    v = package[1]
    file = '{}/{}/{}'.format(work_dir,p,v)
    if os.path.exists('{}/STATUS2'.format(file)):
        all_self_names = []
        all_self_names1 = []
        if os.path.exists("{}/all_rela.txt".format(file)):
            with open("{}/all_rela.txt".format(file), 'r') as f1:
                all_self_names = [line.strip() for line in f1.readlines()]
            for item in all_self_names:
                all_self_names1 += item.split('.')
            all_self_names1 = list(set(all_self_names1))
        else:
            print("STATUS WRONG1:{}".format(file))
            return
        all_imports = []
        if os.path.exists("{}/all_imports.py".format(file)):
            with open("{}/all_imports.py".format(file),'r') as f2:
                all_imports = [line.strip() for line in f2.readlines()]
        else:
            print("STATUS WRONG2:{}".format(file))
            return
        all_imports = list(set(all_imports))
        if not os.path.exists('{}/all_blocks_json'.format(file)):
            os.system('mkdir {}/all_blocks_json'.format(file))
        tmp = []    
        for i in range(len(os.listdir("{}/all_blocks".format(file)))):
            with open('{}/all_blocks/{}.pkl'.format(file,i),'rb') as r1:
                tmp.append(pickle.load(r1))
        result = remove_duplicates(tmp)
        for i in range(len(result)):
            with open('{}/all_blocks_json/{}.json'.format(file,i), 'w') as f:
                json.dump(result[i], f)
        dlt = []
        for part in all_imports:
            if part[:6] == 'from  ':
                dlt.append(part)
                continue
            if part[:4] == 'from':
                p = part.split()
                p = [i.split('.') for i in p]
                p = [j for i in p for j in i]
                if "import" in p:
                    index = p.index("import") 
                    del p[index]
                    for p1 in p:
                        if p1 in all_self_names1:
                            dlt.append(part)
                            break
                else:
                    print('WRONG INPUT1:{}-{}'.format(file,part)) 
            elif part[:6] == 'import':
                p = part.split()
                p = [i.split('.') for i in p]
                p = [j for i in p for j in i]
                for p1 in p:
                    if p1 in all_self_names1:
                        dlt.append(part)
                        break
            else:
                print('WRONG INPUT2:{}-{}'.format(file,part)) 
            
        all_imports = list(set(all_imports) - set(dlt))
        if not os.path.exists("{}/all_imports_final.py".format(file)):
            os.system("touch {}/all_imports_final.py".format(file))
        with open("{}/all_imports_final.py".format(file),'w') as alp:
            for i in all_imports:
                alp.write("{}\n".format(i))
        os.remove('{}/STATUS2'.format(file))
        os.system('touch {}/STATUS3'.format(file))
        print('Execute OK:{}'.format(file))

if __name__ == '__main__':
    work_dir = '../docker_workdir/pypi_packages'
    STATUS0_file_path = 'status_file/STATUS0.json'
    STATUS1_file_path = 'status_file/STATUS1.json'
    STATUS2_file_path = 'status_file/STATUS2.json'
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
        with open(STATUS2_file_path,'r') as u2:
            content2 = json.load(u2)
            content.extend(content2['2'])
            content.extend(content2['2.7'])
            content.extend(content2['3'])
            content.extend(content2['3.3'])
            content.extend(content2['3.4'])
            content.extend(content2['3.5'])
            content.extend(content2['3.6'])
            content.extend(content2['3.7'])
            content.extend(content2['3.8'])
            content.extend(content2['3.9'])
            content.extend(content2['3.10'])
            content.extend(content2['unknown'])
        for con in content:
            futures.append(executor.submit(process_package,con))
        for future in futures:
            future.result()
    print("finish!")
    print(time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time())))