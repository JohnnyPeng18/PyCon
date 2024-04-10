import os
import json
from multiprocessing.dummy import Pool as ThreadPool
import docker
import time
import random

class Check(object):
    def __init__(self, workdir, py_version = '3.9', store_files = False):
        self.workdir = workdir
        self.py_version = py_version
        if float(py_version) < 3:
            self.checkfile = 'test_python2.py'
        else:
            self.checkfile = 'test_python3.py'
        self.store_files = store_files
        self.init_dockerfile()
        self.image_tag = "envdep"
        self.client = docker.from_env()
        self.client.images.build(path=os.path.join(self.workdir, 'checkdata'), tag=self.image_tag, dockerfile="Dockerfile", forcerm=True, network_mode="host")
        print("Docker image built.")

    def init_dockerfile(self):
        with open(os.path.join(self.workdir, "checkdata/Dockerfile"), "w", encoding = "utf-8") as df:
            df.write('FROM python:{}\n'.format(self.py_version))
            df.write(f'COPY {self.checkfile} /root/\n')
    
    def close(self):
        self.client.containers.prune()
        self.client.images.remove(image=self.image_tag)
        self.client.close()

    def check_package(self, args):
        package, version = args
        package_dir = os.path.join(self.workdir, "pypi_packages", package, version)
        if os.path.exists('{}/STATUS4'.format(package_dir)):
            return
        if not os.path.exists('{}/STATUS3'.format(package_dir)) and not os.path.exists('{}/STATUS3_5'.format(package_dir)):
            return
        container_workdir = "/root/envdep"

        uid = os.getuid()
        gid = os.getgid()

        timeout = 10000
        if not os.path.exists(os.path.join(self.workdir, "pypi_packages")):
            os.makedirs(os.path.join(self.workdir, "pypi_packages"))
        if os.path.exists('{}/TASK3_FAIL_RUN'.format(package_dir)):
            os.remove('{}/TASK3_FAIL_RUN'.format(package_dir))
        if os.path.exists('{}/TASK3_FAIL_PIP'.format(package_dir)):
            os.remove('{}/TASK3_FAIL_PIP'.format(package_dir))
        if os.path.exists('{}/fail_run.py'.format(package_dir)):
            os.remove('{}/fail_run.py'.format(package_dir))
        if os.path.exists('{}/STATUS3_5'.format(package_dir)):
            os.remove('{}/STATUS3_5'.format(package_dir))
            os.system('touch {}/STATUS3'.format(package_dir))
        if not os.path.exists(package_dir):
            os.makedirs(package_dir)

        mount = docker.types.Mount(
            target=container_workdir,
            source=package_dir,
            type="bind",
            read_only=False
        )

        commands = [
            f"pip install -r {container_workdir}/requirements.txt || (touch {container_workdir}/TASK3_FAIL_PIP && chown {uid}:{gid} {container_workdir}/TASK3_FAIL_PIP)",
            f"(python /root/{self.checkfile}) || (touch {container_workdir}/TASK3_FAIL_RUN && chown {uid}:{gid} {container_workdir}/TASK3_FAIL_RUN)"
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
            exit_code = container.wait(timeout = timeout + 1000, condition = 'not-running')['StatusCode']
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
                with open(os.path.join(package_dir, 'CHECK_LOG1'), 'w', encoding = 'utf-8') as lf:
                    lf.write(log)
                container.remove(v=True, force = True)
            except Exception as e:
                os.system('echo logerror > {}/ERROR'.format(package_dir))
        print('Excution finished. Exit Code: {},{}-{}'.format(exit_code,package,version))
        
        if (os.path.exists('{}/TASK3_OK'.format(package_dir)) or os.path.exists('{}/TASK3_FAIL'.format(package_dir))) and not (os.path.exists('{}/TASK3_FAIL_PIP'.format(package_dir)) or os.path.exists('{}/TASK3_FAIL_RUN'.format(package_dir))):
            if os.path.exists('{}/STATUS3'.format(package_dir)):
                os.remove('{}/STATUS3'.format(package_dir))
            os.system('touch {}/STATUS4'.format(package_dir))
            if os.path.exists('{}/TASK3_OK'.format(package_dir)):
                print('TASK3_OK-{}-{}'.format(package,version),end="")
            else:
                print('TASK3_FAIL-{}-{}'.format(package,version),end="")
        elif os.path.exists('{}/fail_run.py'.format(package_dir)):
            if os.path.exists('{}/STATUS3'.format(package_dir)):
                os.remove('{}/STATUS3'.format(package_dir))
            os.system('touch {}/STATUS3_5'.format(package_dir))
            print('STATUS3_5-{}-{}'.format(package,version),end="")
        elif os.path.exists('{}/fail_blocks.txt'.format(package_dir)):
            if os.path.exists('{}/STATUS3'.format(package_dir)):
                os.remove('{}/STATUS3'.format(package_dir))
            os.system('touch {}/STATUS3_5'.format(package_dir))
            print('STATUS3_5-{}-{}'.format(package,version),end="")


if __name__ == '__main__':
    pool = ThreadPool(50)
    STATUS3_file_path = 'status_file/STATUS3.json'
    work_dir = '../docker_workdir/pypi_packages'
    data = json.loads(open(STATUS3_file_path, 'r', encoding = 'utf-8').read())
    for selected_py_version in ['2','2.7','3','3.10','3.3','3.4','3.5','3.6','3.7','3.8','3.9']:
        analyzer = Check(work_dir, py_version = selected_py_version, store_files = True)
        packages = data[selected_py_version]
        random.shuffle(packages)
        print('Totally {} packages under python version {}'.format(len(packages), selected_py_version))
        pool.map(analyzer.check_package, packages)
    pool.close()
    print("finish")
    print(time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time())))