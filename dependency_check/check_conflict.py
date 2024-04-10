import os,json
from tqdm import tqdm
import sys,argparse
import rich.progress
from source_processor import VersionCompare as vc

arg_parser = argparse.ArgumentParser()
arg_parser.add_argument('-j', '--popular-packages', type=str, help = "Path of popular_packages.json")
arg_parser.add_argument('-s', '--pypi-packages', type=str, help = "Path of pypi_packages.json")
arg_parser.add_argument('-o', '--output-path', type=str, help = "Path of output (is a directory)")
args = arg_parser.parse_args()
pupular_path=args.popular-packages
pypi_path=args.pypi-packages
outputpath=args.output-path
with rich.progress.open(pupular_path,'r') as jf:
    data=json.load(jf)
with rich.progress.open(pypi_path,'r') as jf:
    dic=json.load(jf)

t4answ={}

for name in tqdm(data,desc='Generating task4'):
    
    t4answ={}    
    for ver in data[name]: 
        if name not in t4answ:
            t4answ[name]={}
        if ver not in t4answ[name]:
            t4answ[name][ver]={}
        
        #only installed
        if not(data[name][ver]['install_status']=='Installed' or data[name][ver]['install_status']=="Missing External Source Code"):
            continue
        if data[name][ver]['installed']['dependency_conflict']!='false':
            continue

        metas=data[name][ver]['installed']['meta_depenedeny']

        if metas=={}:
            continue

        # print("Checking ",name,' ',ver)
        for pkg in metas:
            pkg1=pkg.replace('.','-')
            stndr=metas[pkg]
            if pkg not in dic:
                toput={
                    "require":stndr,
                    "NOTE":'Not in pypi_packages!'
                }
                continue
            
            lis_available=dic[pkg1]
            assert lis_available!=[]
            
            answ=vc.judge_one_in_task4(stndr,lis_available,pkg1)
            toput={
                "require":stndr,
                'legal':answ
            }
            t4answ[name][ver][pkg]=toput

    with open(outputpath+'/'+name+'.json','w')as jf:
        jf.write(json.dumps(t4answ, sort_keys=True, indent=4, separators=(',', ': ')))
    # assert False
        