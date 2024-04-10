import os
from multiprocessing.pool import ThreadPool

def remove_files(file):
    if not (os.path.exists(f'{file}/STATUS0') or os.path.exists(f'{file}/STATUS1') or os.path.exists(f'{file}/STATUS2') \
            or os.path.exists(f'{file}/STATUS3') or os.path.exists(f'{file}/STATUS4') or os.path.exists(f'{file}/STATUS1_5') \
            or os.path.exists(f'{file}/STATUS3_5')):
        return
    if os.path.exists(f'{file}/STATUS1'):
        os.remove(f'{file}/STATUS1')
    if os.path.exists(f'{file}/STATUS1_5'):
        os.remove(f'{file}/STATUS1_5')
    if os.path.exists(f'{file}/STATUS2'):
        os.remove(f'{file}/STATUS2')
    if os.path.exists(f'{file}/STATUS3'):
        os.remove(f'{file}/STATUS3')
    if os.path.exists(f'{file}/STATUS3_5'):
        os.remove(f'{file}/STATUS3_5')
    if os.path.exists(f'{file}/STATUS4'):
        os.remove(f'{file}/STATUS4')
    if os.path.exists(f'{file}/all_blocks'):
        os.system(f'rm -rf {file}/all_blocks')
    if os.path.exists(f'{file}/all_imports.py'):
        os.remove(f'{file}/all_imports.py')
    if os.path.exists(f'{file}/all_imports_final.py'):
        os.remove(f'{file}/all_imports_final.py')
    if os.path.exists(f'{file}/all_python2.txt'):
        os.remove(f'{file}/all_python2.txt')
    if os.path.exists(f'{file}/all_rela.txt'):
        os.remove(f'{file}/all_rela.txt')
    if os.path.exists(f'{file}/fail_run.py'):
        os.remove(f'{file}/fail_run.py')
    if os.path.exists(f'{file}/TASK3_FAIL'):
        os.remove(f'{file}/TASK3_FAIL')
    if os.path.exists(f'{file}/TASK3_FAIL_RUN'):
        os.remove(f'{file}/TASK3_FAIL_RUN')
    if os.path.exists(f'{file}/TASK3_FAIL_PIP'):
        os.remove(f'{file}/TASK3_FAIL_PIP')
    if os.path.exists(f'{file}/TASK3_OK'):
        os.remove(f'{file}/TASK3_OK')
    if os.path.exists(f'{file}/fail_run_final.py'):
        os.remove(f'{file}/fail_run_final.py')
    if os.path.exists(f'{file}/fail_blocks.txt'):
        os.remove(f'{file}/fail_blocks.txt')
    if os.path.exists(f'{file}/fail_blocks_final.txt'):
        os.remove(f'{file}/fail_blocks_final.txt')
    os.system(f'touch {file}/STATUS0')
    print(f'Execute OK:{file}')

if __name__ == '__main__':
    workdir = '../docker_workdir/pypi_packages'
    packages = os.listdir(workdir)
    pool = ThreadPool(80)
    for p in packages:
        package = os.path.join(workdir,p)
        versions = os.listdir(package)
        for v in versions:
            file = os.path.join(workdir,p,v)
            pool.apply_async(remove_files, args=(file,))
    pool.close()
    pool.join()