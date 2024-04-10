import docker
import os
from multiprocessing.dummy import Pool as ThreadPool
import time
from tqdm import tqdm
import json
import subprocess
from source_processor import MetaAnalyzer
import sys


def check_pypi_status(package_dir, jsonfile = None,pypi=None, writefile = False):

    super_big_size=1048576*3000
    super_big_file={}
    
    with open(jsonfile,'r') as jf:
        old_data=json.load(jf)
     
    repos = json.loads(open(jsonfile, 'r', encoding = 'utf-8').read())
    num=0
    unknown_num=0

    for r in tqdm(repos, desc = 'Checking Modules'):
        num=num+1

        for v in repos[r]:

            if r in old_data:
                if v in old_data[r]:
                    temp=old_data[r][v]
                    if temp['install_status']!= 'Not Installed':
                        pass
                    else:
                        continue

                    # temp=old_data[r][v]
                    # if temp['install_status']!= 'Not Installed':
                    #     # if (temp['install_status']!='Missing All Source Code')and(temp['install_status']!='Missing External Source Code')and (temp['install_status']!='Missing Crucial Source Code'):
                    #     #     repos[r][v]=temp
                    #     #     continue

                    #     if 'dependency_conflict' in temp['installed']:
                    #         if temp['installed']['dependency_conflict']!='unknown':         
                    #             repos[r][v]=temp
                    #             continue
                    # # else:
                    # #     repos[r][v]=temp
                    # #     continue
            package_path = os.path.join(package_dir, r, v)
      
            # print(r,v)   
            repos[r][v]['installed'] = {}
            repos[r][v]['install_status'] = 'Not Installed'
            if not os.path.exists(package_path):
                print(r,v,'pkgpath not exists')
                continue

            files = os.listdir(package_path)
            if 'HAVEERROR' in files or 'CANNOTGENERATE' in files:
                print(r,v,'haverr/cantgnrt in files')
                continue


            #too big(>=3GB)
            if 'dependency_info_json.txt' in files:
                jsonfile_path=os.path.join(package_path,'dependency_info_json.txt')
                if os.path.exists(jsonfile_path):
                    if os.path.getsize(jsonfile_path)>=super_big_size:
                        if r in super_big_file:
                            super_big_file[r].append(v)
                        else:
                            super_big_file[r]=[v]
                        print(r,v,'is a super big file')
                        continue
            elif 'dependency_info_dot.json' not in files:
                print(r,v,'neither json nor dot in dir')
                continue
            

            package_name = r.replace("-",".").replace("_", ".")
            if os.path.exists(os.path.join(package_path,'python_version.py')):
                with open(os.path.join(package_path,'python_version.py')) as fff:
                    pyversion=fff.read().strip()
                repos[r][v]['install_python']=pyversion

            files = os.listdir(package_path)
            files_to_chec=files.copy()
            repos[r][v]['installed']['meta_depenedeny'], repos[r][v]['installed']['install_depedency'], repos[r][v]['installed']['dependency_conflict'] = MetaAnalyzer.analyze_all(os.path.join(package_path, 'aaa'),pypi,jsonfile)
            for f in files:
                if f.endswith('-{}.dist-info'.format(v)) or f.endswith('-{}.dist-info'.format(v.replace('-', '_'))):
                    f_name = f.replace('-{}.dist-info'.format(v), '').replace('-{}.dist-info'.format(v.replace('-', '_')), '').replace("-",".").replace("_", ".")
                    if f_name.lower() == package_name.lower():
                        repos[r][v]['installed']['dist-info'] = f
                        repos[r][v]['installed']['top_modules'] = []
                        if os.path.exists(os.path.join(package_path, repos[r][v]['installed']['dist-info'], 'top_level.txt')):
                            top_modules = open(os.path.join(package_path, repos[r][v]['installed']['dist-info'], 'top_level.txt'), 'r', encoding = 'utf-8').read().split('\n')
                            for m in top_modules:
                                if len(m.replace(" ", "")) > 0:
                                    repos[r][v]['installed']['top_modules'].append(m)
                        if os.path.exists(os.path.join(package_path, repos[r][v]['installed']['dist-info'], 'METADATA')):
                            if len(repos[r][v]['installed']['top_modules']) == 0:
                                metadata = open(os.path.join(package_path, repos[r][v]['installed']['dist-info'], 'METADATA')).read().split('\n')
                                for d in metadata:
                                    if d.startswith('Name:'):
                                        repos[r][v]['installed']['top_modules'] = [d.replace('Name:', '').replace(' ', '')]
                        
                        failed = False
                        repos[r][v]['installed']['sources'] = []
                        for m in repos[r][v]['installed']['top_modules']:
                            
                            if os.path.exists(os.path.join(package_path, m)):
                                repos[r][v]['installed']['sources'].append(m)
                            elif os.path.exists(os.path.join(package_path, m + '.py')):
                                repos[r][v]['installed']['sources'].append(m + '.py')
                            elif os.path.exists(os.path.join(package_path, m.replace('-', '.').replace('_', '.').split('.')[0])):
                                repos[r][v]['installed']['sources'].append(m.replace('-', '.').replace('_', '.').split('.')[0])
                            elif os.path.exists(os.path.join(package_path, m.replace('-', '_').replace('.', '_').split('_')[0])):
                                repos[r][v]['installed']['sources'].append(m.replace('-', '_').replace('.', '_').split('_')[0])
                            else:
                                failed = True
                                # break
                        if len(repos[r][v]['installed']['top_modules']) == 0:
                            repos[r][v]['install_status'] = 'Missing Top Module'
                        elif not failed:
                            repos[r][v]['install_status'] = 'Installed'
                        else:
                            if len(repos[r][v]['installed']['sources'])==0:
                                repos[r][v]['install_status'] = 'Missing All Source Code'
                            elif r.replace('.','_').replace('-','_') in repos[r][v]['installed']['sources'] or r.replace('.','_').replace('-','_')+'.py' in repos[r][v]['installed']['sources']:
                                repos[r][v]['install_status'] = 'Missing External Source Code'
                            else:
                                repos[r][v]['install_status'] = 'Missing Crucial Source Code'
                        break
            if 'dist-info' not in repos[r][v]['installed'] and os.path.exists(os.path.join(package_path, 'LOG')):
                log = open(os.path.join(package_path, 'LOG'), 'r', encoding = 'utf-8').read()
                if 'error' in log.lower() or ('requires' in log.lower() and 'but' in log.lower()):
                    repos[r][v]['install_status'] = 'Error'
            if len(files) > 2 and repos[r][v]['install_status'] == 'Not Installed':
                repos[r][v]['install_status'] = 'Unrecognized'
            if repos[r][v]['install_status']!='Not Installed':
                print(r,v,repos[r][v]['install_status'])

                    
    status = {'Not Installed': 0, 'Installed': 0, 'Missing All Source Code': 0,'Missing Crucial Source Code': 0,'Missing External Source Code': 0, 'Error': 0, 'Missing Top Module': 0, 'Unrecognized': 0, 'Dependency_Conflict': 0,'Unknown':0}
    python_version = {}
    num = 0
    for r in repos:
        for v in repos[r]:
            if repos[r][v]['install_status'] not in ['Error', 'Installed'] and 'install_python' in repos[r][v]:
                if repos[r][v]['install_python'] not in python_version:
                    python_version[repos[r][v]['install_python']] = [[r, v]]
                else:
                    python_version[repos[r][v]['install_python']].append([r, v])
                num += 1
            status[repos[r][v]['install_status']] += 1
            if 'installed' in repos[r][v] and 'dependency_conflict' in repos[r][v]['installed'] and repos[r][v]['installed']['dependency_conflict']=='true':
                status['Dependency_Conflict'] += 1
            elif 'installed' in repos[r][v] and 'dependency_conflict' in repos[r][v]['installed'] and repos[r][v]['installed']['dependency_conflict']=='unknown':
                status['Unknown'] += 1
    
    

    if writefile:
        
        with open(jsonfile, 'w', encoding = 'utf-8') as jf:
            jf.write(json.dumps(repos, sort_keys=True, indent=4, separators=(',', ': ')))

        # with open("super_big_file.json", 'w', encoding = 'utf-8') as jf:
        #     jf.write(json.dumps(super_big_file, sort_keys=True, indent=4, separators=(',', ': ')))
    
    
    pyver={}
    for r in repos:
        for v in repos[r]:
            if 'install_python' in repos[r][v]:
                if repos[r][v]['install_python'] not in pyver:
                    pyver[repos[r][v]['install_python']] = 1
                else:
                    pyver[repos[r][v]['install_python']] +=1
            # if repos[r][v]["install_status"]!="Not Installed":
            #     print(repos[r][v])

    
    print(status)
    print('{} packages need to be installed.'.format(num))
    print(pyver)


import argparse
if __name__ == "__main__":
    '''
    The arg 'pypi_packages_path' is the downloading path of task 1.
    The 1st level of 'pypi_packages_path' is packages. The 2nd level of 'pypi_packages_path' is versions.
    
    The arg 'jsonfile' is the path of 'popular_packages.json'.

    The arg 'jsonfile' is the path of 'popular_packages.json'.

    '''
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('-d', '--downloadpath', type=str, help = "Path of downloaded packages")
    arg_parser.add_argument('-p', '--popular-packages', type=str, help = "Path of popular_packages.json")
    arg_parser.add_argument('-s', '--pypi-packages', type=str, help = "Path of pypi_packages.json")
    args = arg_parser.parse_args()
    pypi_packages_path=args.downloadpath
    jsonfile=args.popular-packages
    pypi=args.pypi-packages
    check_pypi_status(pypi_packages_path,jsonfile=jsonfile,pypi=pypi,writefile=True)

