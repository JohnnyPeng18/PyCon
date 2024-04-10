import os
import time
import import_validation_STATUS1_help as friend
from concurrent.futures import ThreadPoolExecutor
import pickle
import json

def get_all_pyfiles(path,appedix=".py",retlist = None):
    if retlist is None:
        retlist = []
    for file in os.listdir(path):
        full_file_path = os.path.join(path, file)

        if os.path.isdir(full_file_path):
            get_all_pyfiles(full_file_path,appedix,retlist)

        if not os.path.isdir(full_file_path):
            if full_file_path.endswith(appedix):
                retlist.append(full_file_path)

    return retlist

def get_all_self_names(root_folder):
    results = []
    for dirpath, dirnames, filenames in os.walk(root_folder):
        if '__init__.py' in filenames:
            results.append(os.path.basename(dirpath))
    return results
    
def process_package(p):
    package = p[0]
    version = p[1]
    if not os.path.exists("{}/{}/{}/STATUS0".format(work_dir,package,version)):
        if not (os.path.exists("{}/{}/{}/dependency_info_json.txt".format(work_dir,package,version)) or os.path.exists("{}/{}/{}/dependency_info_dot.json".format(work_dir,package,version))):
            print("Not Installed:{}/{}".format(package,version))
        return
    file = "{}/{}/{}".format(work_dir,package,version)
    all_self_names = []
    all_imports_3 = []
    all_python2_paths = []
    all_try_if_statements = []
    retlist = get_all_pyfiles(file,".py",None)
    if os.path.exists('{}/python_version.py'.format(file)):
        retlist.remove("{}/python_version.py".format(file))
    if os.path.exists('{}/all_imports_final.py'.format(file)):
        retlist.remove("{}/all_imports_final.py".format(file))
    if os.path.exists('{}/all_imports.py'.format(file)):
        retlist.remove("{}/all_imports.py".format(file))
    for ret in retlist:
        add = os.path.splitext(os.path.basename(ret))[0]
        all_self_names.append(add)
    add1 = get_all_self_names(file)
    all_self_names.extend(add1)
    add_tmp = []
    add_tmp.extend(get_all_pyfiles(file,".so",None))
    add_tmp.extend(get_all_pyfiles(file,".zip",None))
    add_tmp.extend(get_all_pyfiles(file,".pyc",None))
    add_tmp.extend(get_all_pyfiles(file,".egg",None))
    add_tmp.extend(get_all_pyfiles(file,".dll",None))
    add_tmp.extend(get_all_pyfiles(file,".whl",None))
    add_tmp.extend(get_all_pyfiles(file,".pyd",None))
    for i in add_tmp:
        all_self_names.append(os.path.splitext(os.path.basename(i))[0])
    all_self_names = list(set(all_self_names))
    all_self_names = [x for x in all_self_names if x != '']
    if not os.path.exists("{}/all_rela.txt".format(file)):
        os.system('touch {}/all_rela.txt'.format(file))
    with open('{}/all_rela.txt'.format(file),'w') as rela:
        for i in all_self_names:
            rela.write('{}\n'.format(i))
    for ret in retlist:
        try:
            with open(ret,'r') as r1:
                code = r1.read()
            add = friend.get_import_statements(code)
            all_imports_3.extend(add)
            add1 = friend.get_array(ret)
            if not len(add1) == 0:
                all_try_if_statements.extend(add1)
        except:
            all_python2_paths.append(ret)
    all_imports_3 = list(set(all_imports_3))
    if not os.path.exists('{}/all_imports.py'.format(file)):
        os.system('touch {}/all_imports.py'.format(file))
    with open('{}/all_imports.py'.format(file),'w') as al:
        for i in all_imports_3:
            al.write("{}\n".format(i))
    if not os.path.exists("{}/all_blocks".format(file)):
        os.system('mkdir {}/all_blocks'.format(file))
    for i in range(len(all_try_if_statements)):
        with open('{}/all_blocks/{}.pkl'.format(file,i), 'wb') as f:
            pickle.dump(all_try_if_statements[i], f, protocol=2)
    if not os.path.exists('{}/all_python2.txt'.format(file)):
        os.system('touch {}/all_python2.txt'.format(file))
    with open('{}/all_python2.txt'.format(file),'w') as p2:
        for i in all_python2_paths:
            p2.write("{}\n".format(i))
    os.remove('{}/STATUS0'.format(file))
    os.system('touch {}/STATUS1'.format(file))
    print("Execute OK:{}/{}".format(package,version))
        


if __name__ == '__main__':
    work_dir = '../docker_workdir/pypi_packages'
    STATUS0_file_path = 'status_file/STATUS0.json'
    with ThreadPoolExecutor(max_workers=100) as executor:
        futures = []
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
        for con in content:
            futures.append(executor.submit(process_package,con))
        for future in futures:
            future.result()
    print("finish!")
    print(time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time())))

print(content)