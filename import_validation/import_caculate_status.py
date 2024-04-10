import os
import json
from tqdm import tqdm

def fill_json(status, py_version, p, v):
    with open('{}/{}.json'.format(status_dir,status), 'r+') as u:
        content1 = json.loads(u.read())
        tmp = content1.get(py_version, [])
        tmp.append([p, v])
        content1[py_version] = tmp
        u.seek(0)
        u.write(json.dumps(content1, sort_keys=True, indent=4, separators=(',', ':')))
        u.truncate()


work_dir = '../docker_workdir/pypi_packages'
status_dir = './status_file'
packages = os.listdir(work_dir)
total_packages = len(packages)

with tqdm(total=total_packages, ncols=80) as pbar:
    for p in packages:
        versions = os.listdir("{}/{}".format(work_dir, p))
        for v in versions:
            file = "{}/{}/{}".format(work_dir, p, v)
            if not os.path.exists('{}/python_version.py'.format(file)):
                py_version = 'unknown'
            else:
                with open('{}/python_version.py'.format(file)) as r1:
                    py_version = r1.read().strip()
                    if py_version.strip() == '':
                        py_version = 'unknown'
            try:
                if os.path.exists('{}/STATUS0'.format(file)):
                    fill_json('STATUS0', py_version, p, v)
                elif os.path.exists('{}/STATUS1'.format(file)):
                    fill_json('STATUS1', py_version, p, v)
                elif os.path.exists('{}/STATUS1_5'.format(file)):
                    fill_json('STATUS1_5', py_version, p, v)
                elif os.path.exists('{}/STATUS2'.format(file)):
                    fill_json('STATUS2', py_version, p, v)
                elif os.path.exists('{}/STATUS3'.format(file)):
                    fill_json('STATUS3', py_version, p, v)
                elif os.path.exists('{}/STATUS3_5'.format(file)):
                    fill_json('STATUS3_5', py_version, p, v)
                elif os.path.exists('{}/STATUS4'.format(file)):
                    fill_json('STATUS4', py_version, p, v)
                else:
                    fill_json('OTHERS', py_version, p, v)
            except:
                print('HAVE ERROR:{}-{}'.format(p, v))
                fill_json('OTHERS', 'unknown', p, v)

        pbar.update(1)