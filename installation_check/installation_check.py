import docker
import os
from multiprocessing.dummy import Pool as ThreadPool
import time
from tqdm import tqdm
import json
import subprocess
import gc
import subprocess
import concurrent.futures
import pydotplus

class EnvAnalyzer(object):
    def __init__(self, workdir, py_version = '3.7', store_files = False):
        self.workdir = workdir
        self.py_version = py_version
        self.store_files = store_files
        self.init_dockerfile()
        self.image_tag = "envdep"
        self.client = docker.from_env()
        self.client.images.build(path=os.path.join(self.workdir, 'metadata'), tag=self.image_tag, dockerfile="Dockerfile", forcerm=True,network_mode="host")
        self.bigVersion = '2.2'
        print("Docker image built.")


    def init_dockerfile(self):
        with open(os.path.join(self.workdir, "metadata/Dockerfile"), "w", encoding = "utf-8") as df:
            df.write('FROM python:{}\n'.format(self.py_version))
            df.write('RUN pip install --no-cache-dir pipdeptree\n')
            df.write('RUN pip install --no-cache-dir graphviz\n')
            df.write('RUN sed -i \'s/jessie/buster/g\' /etc/apt/sources.list\n')
            df.write('RUN apt update\n')
            df.write('RUN apt install --force-yes -y jq\n')
    
    def close(self):
        self.client.containers.prune()
        self.client.images.remove(image=self.image_tag)
        self.client.close()

    def install_package(self, args):
        package, version = args
        package_dir = os.path.join(self.workdir, "pypi_packages", package, version)
        package_name = package.replace("-", ".").replace("_", ".")
        container_workdir = "/root/envdep"
        uid = os.getuid()
        gid = os.getgid()
        timeout = 1000
        if not os.path.exists(os.path.join(self.workdir, "pypi_packages")):
            os.makedirs(os.path.join(self.workdir, "pypi_packages"))

        if not os.path.exists(package_dir):
            os.makedirs(package_dir)

        mount = docker.types.Mount(
            target=container_workdir,
            source=package_dir,
            type="bind",
            read_only=False
        )

        buf_prefix = "stdbuf -i0 -o0 -e0"
        timeout_prefix = f"timeout {timeout}"
        timeout_prefix1 = "timeout 100"
        pip_command0 = f"python -W ignore:DEPRECATION -m pip install --no-compile {package_name}=={version} --disable-pip-version-check"
        pip_command = f"python -W ignore:DEPRECATION -m pip install --target={container_workdir} --no-compile {package_name}=={version} --disable-pip-version-check"
        path_command = 'export PYTHONPATH=/root/envdep:$PYTHONPATH'
        info_command1 = f"pipdeptree -p $(pip show {package_name} | grep ^Name | cut -d ' ' -f 2) --graph-output dot > {os.path.join(container_workdir, 'dependency_info_dot.dot')}"
        info_command = f"pipdeptree -p $(pip show {package_name} | grep ^Name | cut -d ' ' -f 2) --json-tree  > {os.path.join(container_workdir, 'dependency_info_json.txt')}"
        commands = [
            f"rm -rf {container_workdir}/*",
            f"{buf_prefix} {timeout_prefix} {pip_command0}|| touch {container_workdir}/HAVEERROR",
            f"{buf_prefix} {timeout_prefix} {pip_command}|| touch {container_workdir}/HAVEERROR",
            f'{buf_prefix} {timeout_prefix1} {info_command} || touch {container_workdir}/CANNOTGENERATE',
            f'{buf_prefix} {timeout_prefix1} {info_command1} || touch {container_workdir}/CANNOTGENERATE',
            f"chown -R {uid}:{gid} {container_workdir}"
        ]

        command = " && ".join(commands)
        try:
            container = self.client.containers.run(
                image=self.image_tag,
                command=["/bin/bash", "-c", command],
                detach=True,
                network_mode="host",
                mounts=[mount]
            )
        except Exception as e:
            print("Container running failed, reason1: {}".format(e))
            os.system('echo runningerror > {}/ERROR'.format(package_dir))
            exit_code = -1
            return package_dir, exit_code
        try:
            exit_code = container.wait(timeout = timeout + 100, condition = 'not-running')['StatusCode']
        except Exception as e:
            print('Container time out, killed.')
            try:
                if container.status == 'running':
                    container.kill()
            except Exception as e:
                os.system('echo timeout > {}/ERROR'.format(package_dir))
            exit_code = -1
        
        finally:
            try:
                log = container.logs(stdout = True, stderr = True).decode(encoding = 'utf-8', errors = 'ignore').strip()
                with open(os.path.join(package_dir, 'CHECK_LOG'), 'w', encoding = 'utf-8') as lf:
                    lf.write(log)
                container.remove(v=True, force = True)
            except Exception as e:
                os.system('echo logerror > {}/ERROR'.format(package_dir))
        print('Excution finished. Exit Code: {},{}-{}'.format(exit_code,package,version))
        gc.collect()
        with open("{}/python_version.py".format(package_dir),'w') as pv:
            pv.write(self.py_version)
        
        if os.path.exists("{}/dependency_info_json.txt".format(package_dir)):
            with open("{}/dependency_info_json.txt".format(package_dir),"r") as rep:
                content = rep.read().strip()
            if content == '' or content == '[]':
                os.remove("{}/dependency_info_json.txt".format(package_dir))
        if os.path.exists("{}/dependency_info_dot.dot".format(package_dir)):
            with open("{}/dependency_info_dot.dot".format(package_dir),'r') as rep1:
                content1 = rep1.read().strip()
            if content1 == '':
                os.remove('{}/dependency_info_dot.dot'.format(package_dir))

        if os.path.exists(os.path.join(package_dir,'dependency_info_json.txt')) or os.path.exists(os.path.join(package_dir,'dependency_info_dot.dot')):
            if os.path.exists(os.path.join(package_dir,'CANNOTGENERATE')):
                os.remove(os.path.join(package_dir,'CANNOTGENERATE'))
            if os.path.exists(os.path.join(package_dir,'HAVEERROR')):
                os.remove(os.path.join(package_dir,'HAVEERROR'))
        
        if os.path.exists(os.path.join(package_dir,'dependency_info_json.txt')) and os.path.exists(os.path.join(package_dir,'dependency_info_dot.dot')):
            if os.path.getsize(os.path.join(package_dir,'dependency_info_json.txt')) > 1073741824:
                os.remove(os.path.join(package_dir,'dependency_info_json.txt'))

        if os.path.exists(os.path.join(package_dir,'dependency_info_json.txt')) and os.path.exists(os.path.join(package_dir,'dependency_info_dot.dot')):
            try:
                with open(os.path.join(package_dir,'dependency_info_json.txt'),'r') as r1:
                    json.load(r1)
                os.remove(os.path.join(package_dir,'dependency_info_dot.dot'))
            except:
                os.remove(os.path.join(package_dir,'dependency_info_json.txt'))
            
            try:
                if os.path.exists(os.path.join(package_dir,'dependency_info_dot.dot')):
                    pydotplus.graph_from_dot_file(os.path.join(package_dir,'dependency_info_dot.dot'))
            except:
                os.system(f'touch {package_dir}/HAVEERROR')
        
        if len(os.listdir(package_dir)) <= 3:
            s = os.listdir(package_dir)
            for s1 in s:
                if not (s1 == 'CHECK_LOG' or s1 == 'python_version.py'):
                    os.remove(os.path.join(package_dir,s1))
            os.system(f'touch {package_dir}/HAVEERROR')
        
        file = package_dir
        if os.path.exists('{}/dependency_info_dot.dot'.format(file)) and not os.path.exists('{}/dependency_info_dot.json'.format(file)):
            try:
                graph = pydotplus.graph_from_dot_file("{}/dependency_info_dot.dot".format(file))
            except:
                os.remove("{}/dependency_info_dot.dot".format(file))
            install_dependency = {}
            meta_dependency = {}

            try:
                for node in graph.get_nodes():
                    name = node.get_name().strip('"')
                    label = node.get_label()
                    version = label.split("\\n")[-1][:-1]
                    install_dependency[name] = version
                    for edge in graph.get_edges():
                        source_name = edge.get_source().strip('"')
                        target_name = edge.get_destination().strip('"')
                        if target_name == name:
                            if target_name not in meta_dependency:
                                meta_dependency[target_name] = [edge.get_label().strip('"')]
                            else:
                                if not edge.get_label().strip('"') in meta_dependency[target_name]:
                                    meta_dependency[target_name].append(edge.get_label().strip('"'))
            except:
                if os.path.exists('{}/dependency_info_dot.dot'.format(file)):
                    os.remove('{}/dependency_info_dot.dot'.format(file))

            if os.path.exists('{}/dependency_info_dot.dot'.format(file)):
                with open('{}/dependency_info_dot.json'.format(file),'w') as dj:
                    dj.write('{\n"install_dependency": {\n')
                    for i,(name,version) in enumerate(install_dependency.items()):
                        if not i == len(install_dependency.items()) - 1:
                            dj.write('    "{}":"{}",\n'.format(name,version))
                        else:
                            dj.write('    "{}":"{}"\n'.format(name,version))
                    dj.write('},\n"meta_dependency":{\n')
                    for i,(name,meta) in enumerate(meta_dependency.items()):
                        if not i == len(meta_dependency.items()) - 1:
                            dj.write('    "{}":{},\n'.format(name,meta).replace('\'','"'))
                        else:
                            dj.write('    "{}":{}\n'.format(name,meta).replace('\'','"'))
                    dj.write('}\n}')

        if os.path.exists(os.path.join(package_dir,'dependency_info_json.txt')) or os.path.exists(os.path.join(package_dir,'dependency_info_dot.json')):
            print("Generate OK!{}".format(package_dir),end="")

def install(jsonfile,workdir):
    data = json.loads(open(jsonfile, "r", encoding = 'utf-8').read())
    pool = ThreadPool(50)
    for v in data:
        if v in ["2.2", "2.3", "2.4", "2.5", "2.6"]:
            version = "2.7"
        elif v in ["3.0", "3.1", "3.2", "3.11", "3.12"]:
            version = "3"
        else:
            version = v
        analyzer = EnvAnalyzer(workdir, py_version = version, store_files = True)
        analyzer.changBigVersion("{}".format(v))
        packages = data[v]
        print('Totally {} packages under python version {}'.format(len(packages), v))
        pool.map(analyzer.install_package, packages)
    pool.close()


def delete(package_dir, jsonfile):
    repos = json.loads(open(jsonfile, 'r', encoding='utf-8').read())
    with concurrent.futures.ThreadPoolExecutor(max_workers=120) as executor:
        for r in repos:
            executor.submit(clean_up_package, package_dir, r, repos[r])
    

def clean_up_package(package_dir, r, versions):
    for v in versions:
        if not os.path.exists("{}/{}/{}".format(package_dir,r,v)):
            continue
        if os.path.exists("{}/{}/{}/STATUS1".format(package_dir,r,v)) or os.path.exists("{}/{}/{}/STATUS2".format(package_dir,r,v)) or \
            os.path.exists("{}/{}/{}/STATUS3".format(package_dir,r,v)) or os.path.exists("{}/{}/{}/STATUS3_5".format(package_dir,r,v)) or \
            os.path.exists("{}/{}/{}/STATUS4".format(package_dir,r,v)):
            continue
        if versions[v]["install_status"] == "Installed" or versions[v]["install_status"] == "Not Installed":
            print('{}-{}'.format(r,v))
            usefulfiles = []
            if versions[v]["install_status"] == "Installed":
                for i in versions[v]["installed"]["top_modules"]:
                    usefulfiles += i.split("/")[0]
                usefulfiles = versions[v]["installed"]["top_modules"] + [versions[v]["installed"]["dist-info"],\
                            'CHECK_LOG', 'dependency_info_json.txt','HAVEERROR','all_blocks',\
                            'python_version.py','CANNOTGENERATE',\
                            'STATUS0','STATUS1','STATUS2','STATUS3','STATUS4',\
                            'all_imports.py','all_rela.txt','all_python2.txt','requirements.txt','all_imports_final.py',\
                            'TASK3_OK','TASK3_FAIL','TASK3_FAIL_PIP','dependency_info_dot.dot','CHECK_LOG1','fail_run.py','TASK3_FAIL_RUN',\
                            'dependency_info_dot.json','fail_blocks.txt']
                for i in versions[v]["installed"]["sources"]:
                    if(i not in usefulfiles):
                        usefulfiles.append(i)
            else:
                if os.path.exists("{}/{}/{}/dependency_info_json.txt".format(package_dir,r,v)):
                    print("-----------------------{}/{}-----------------------------".format(r,v))
                    continue
                usefulfiles = ['CHECK_LOG', 'dependency_info_json.txt','HAVEERROR','python_version.py','CANNOTGENERATE']
            path = os.path.join(package_dir, r, v)
            files = os.listdir(path)
            for f in files:
                if f not in usefulfiles:
                    try:
                        print('Deleted {} in {}/{}'.format(f, r, v))
                        os.system('rm -rf {}'.format(os.path.join(path, f)))
                    except Exception as e:
                        print(e)
            images = bytes.decode(subprocess.check_output(["find", f"{path}", "-name", "\"*.so\""])).split("\n")
            for i in images:
                if len(i) > 0 and os.path.isfile(i):
                    try:
                        print('Deleted {} in {}/{}'.format(i, r, v))
                        os.system('rm -rf {}'.format(i))
                    except Exception as e:
                        print(e)
            if versions[v]["install_status"] == "Installed":
                if not(os.path.exists('{}/{}/{}/STATUS0'.format(package_dir,r,v)) or \
                    os.path.exists('{}/{}/{}/STATUS1'.format(package_dir,r,v)) or \
                    os.path.exists('{}/{}/{}/STATUS2'.format(package_dir,r,v)) or \
                    os.path.exists('{}/{}/{}/STATUS3'.format(package_dir,r,v)) or \
                    os.path.exists('{}/{}/{}/STATUS4'.format(package_dir,r,v)) or \
                    os.path.exists('{}/{}/{}/STATUS3_5'.format(package_dir,r,v)) or \
                    os.path.exists('{}/{}/{}/STATUS1_5'.format(package_dir,r,v))):
                    os.system('touch {}/{}/{}/STATUS0'.format(package_dir,r,v))
                    print('touch {}/{}/{}/STATUS0'.format(package_dir,r,v))
                if (os.path.exists('{}/{}/{}/STATUS1'.format(package_dir,r,v)) or \
                    os.path.exists('{}/{}/{}/STATUS2'.format(package_dir,r,v)) or \
                    os.path.exists('{}/{}/{}/STATUS3'.format(package_dir,r,v)) or \
                    os.path.exists('{}/{}/{}/STATUS4'.format(package_dir,r,v)) or \
                    os.path.exists('{}/{}/{}/STATUS3_5'.format(package_dir,r,v)) or \
                    os.path.exists('{}/{}/{}/STATUS1_5'.format(package_dir,r,v))):
                    os.system('rm -rf {}/{}/{}/STATUS0'.format(package_dir,r,v))   


if __name__ == "__main__":
    # input the path of pypi_packages.json
    install_file_path = ''
    # input the path of popular_packages.json
    popular_packages_file_path = ''
    workdir = '../docker_workdir/pypi_packages'
    install(install_file_path,workdir)
    # delete(workdir, popular_packages_file_path)
    print("finish")
    print(time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time())))
    