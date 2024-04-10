# PyConf
This is the artifact released in the ICSE'24 paper "[Less is More? An Empirical Study on Configuration Issues in Python PyPI Ecosystem](https://arxiv.org/abs/2310.12598)".

## docker_workdir
All the data are stored here and docker images are built in this folder.
### metadata
The docker images are built here to download the packages in Task1.
It contains a file `Dockerfile`.
### pypi_packages
All packages are downloaded to this folder.
### checkdata
The docker images are built here to validate the import statements.
It also contains a dockerfile `Dockerfile` and two python files `test_python2.py` and `test_python3.py`.
`test_python2.py` and `test_python3.py` are used to perform validation in Docker for Python 2 and Python 3, respectively.

For more details, please access the `docker_workdir` directory.

If you want to use **PyCon**, please follow the steps below:
## Installation check
To start the Task1 to download the packages, you are required to input the path of `pypi_packages.json` and `popular_packages.json` to the python file `installation_check.py`.
```python
python installation_check.py
```

If you finish downloading the packages and finish the `dependency_check` to collect the dependencies of the releases, you should comment out the line
```python
install(install_file_path,workdir)
```
and uncomment the line
```python
delete(workdir, popular_packages_file_path)
```
and run the code again.
For more details, please access the `installation check` directory.

## Dependency check
To collect the dependencies of each release, use the command:

    usage: collect_dependency.py [-h] [-d DOWNLOADPATH] [-p POPULAR_PACKAGES] 
                    [-s PYPI_PACKAGES]
    
    optional arguments:
    -h, --help            show this help message and exit
    -d DOWNLOADPATH, --downloadpath DOWNLOADPATH
                            Path of downloaded packages
    -p POPULAR_PACKAGES, --popular-packages POPULAR_PACKAGES
                            Path of popular_packages.json
    -s PYPI_PACKAGES, --pypi-packages PYPI_PACKAGES
                            Path of pypi_packages.json
    
    It will read pypi_packages.json as a catalog, analyze the packages and versions in the DOWNLOADPATH, 
    and finally update popular_packages.json with the details of packages (install status, required dependencies,
    installed dependencies, etc).
    
    An example of running it:
    python collect_dependency.py -d docker_workdir/pypi_packages -p popular_packages.json -s pypi_packages.json

To check the conflict of dependencies, use the command:

    usage: check_conflict.py [-h] [-j POPULAR_PACKAGES] [-s PYPI_PACKAGES]
                    [-o OUTPUT_PATH]
    
    optional arguments:
    -h, --help            show this help message and exit
    -j POPULAR_PACKAGES, --popular-packages POPULAR_PACKAGES
                            Path of popular_packages.json
    -s PYPI_PACKAGES, --pypi-packages PYPI_PACKAGES
                            Path of pypi_packages.json
    -o OUTPUT_PATH, --output-path OUTPUT_PATH
                            Path of output (is a directory)
    
    It will give a collection of all the versions that meet the requirements (only analyze packages with the status of
    'installed' or 'Missing External Source Code'), using pypi_packages.json as a catalog.
    
    An example of running it:
    python check_conflict.py -j popular_packages.json -s pypi_packages.json -o task4_output_dir


For more details, please access the `dependency check` directory.

## Import validation
If you finish above tasks, then you can run the code.

First, you should run `import_validation_requirements.py` to get the `requirements.txt` file of each release.
you are required to input the path of `popular_packages.json` to the python file `import_validation_requirements.py`.
```python
python import_validation_requirements.py
```

Then, run code `import_validation_STATUS0`:
```python
python import_validation_STATUS0.py
```

For each of the following steps, you are required to run the code `import_caculate_status.py` to refresh the status of each package.

```python
python import_caculate_status.py
```

Then, run the codes `import_validation_STATUS1`, `import_validation_STATUS2`, `import_validation_STATUS3` and `import_validation_STATUS4` in turn:
```python
python import_validation_STATUS1.py
python import_validation_STATUS2.py
python import_validation_STATUS3.py
python import_validation_STATUS4.py
```
Note the file `import_validation_STATUS2.py` needs to run in a python2 environment.



## VLibs

For the metadata of verfied third-party libraries on PyPI, please check the `vlibs/` folder.

For the JSON file, `install_status: True` indicates that the library release passes the dependency check of PyCon. `validated: True` indicates that the library release passes all checks of PyCon.



## Cite Us

If you use PyConf in your work, please cite us:

```
@misc{peng2024more,
      title={Less is More? An Empirical Study on Configuration Issues in Python PyPI Ecosystem}, 
      author={Yun Peng and Ruida Hu and Ruoke Wang and Cuiyun Gao and Shuqing Li and Michael R. Lyu},
      year={2024},
      eprint={2310.12598},
      archivePrefix={arXiv},
      primaryClass={cs.SE}
}
```

