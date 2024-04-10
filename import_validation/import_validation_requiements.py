import os
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

workdir = '../docker_workdir/pypi_packages'
# input the paht of popular_packages.json
popular_packages_file_path = ''
repos = json.loads(open(popular_packages_file_path, 'r', encoding='utf-8').read())

def write_requirements_txt(p, v):
    dependency_list = []
    if repos[p][v]['install_status'] == 'Installed':
        if os.path.exists('{}/{}/{}/requirements.txt'.format(workdir,p,v)):
            os.remove('{}/{}/{}/requirements.txt'.format(workdir,p,v))
        if not os.path.exists('{}/{}/{}/requirements.txt'.format(workdir,p,v)):
            os.system('touch {}/{}/{}/requirements.txt'.format(workdir,p,v))
        dependency_list = [f"{key}=={value}" for key, value in repos[p][v]['installed']['install_depedency'].items()]
        with open('{}/{}/{}/requirements.txt'.format(workdir,p,v),'w') as r1:
            for d in dependency_list:
                r1.write('{}\n'.format(d.replace('-','.').replace('_','.')))
            print('Generated OK:{}/{}'.format(p,v))

with ThreadPoolExecutor(max_workers=120) as executor:
    futures = [executor.submit(write_requirements_txt, p, v) for p in repos for v in repos[p]]
    for future in as_completed(futures):
        try:
            result = future.result()
        except Exception as exc:
            print(f'Generated an exception: {exc}')