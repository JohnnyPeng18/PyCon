import ast
import re
import json
import xml.sax
from bs4 import BeautifulSoup
import ast
import os
from tqdm import tqdm
import logging
import copy
from check_legal_ver import CLV
import datetime

class My_pypi:
    def __init__(self,pypi):
        with open(pypi,'r') as jf:
            self.data=json.load(jf)
    
    @classmethod
    def instance(cls, *args, **kwargs):
        if not hasattr(My_pypi, "_instance"):
            My_pypi._instance = My_pypi(*args, **kwargs)
        return My_pypi._instance

    def check_name(self,name):
        name=name.replace('.','-')
        if name not in self.data:
            return False
        return True    
    
    def check_namever(self,name,ver):
        name=name.replace('.','-')
        if name not in self.data:
            return False
        if ver not in self.data[name]:
            return False
        return True
    
    @staticmethod
    def stt_check_name(name):
        return My_pypi.instance().check_name(name)
    @staticmethod
    def stt_check_namever(name,ver):
        return My_pypi.instance().check_namever(name,ver)

        
class My_ppkgs:
    def __init__(self,popupath):
        with open(popupath,'r') as jf:
            self.data=json.load(jf)
    
    @classmethod
    def instance(cls, *args, **kwargs):
        if not hasattr(My_ppkgs, "_instance"):
            My_ppkgs._instance = My_ppkgs(*args, **kwargs)
        return My_ppkgs._instance


    def get_time(self,name,ver):
        name=name.replace('.','-')
        return self.data[name][ver]['releasetime']

    @staticmethod
    def stt_get_time(name,ver):
        try:
            return My_ppkgs.instance().get_time(name,ver)
        except KeyError as e:
            return False

class MetaAnalyzer(object):
    def __init__(self):
        pass

    @staticmethod
    def find_meta(l):
        pkgs={}
        # TODO: judge if l['key'] in pypi
        # print(l['key'])
        # if not My_pypi.stt_check_name(l['key']):
        #     return {}
        
        if l["dependencies"] == []:
            pkgs[l['key']]=l['required_version']
            return pkgs
        

        pkgs[l['key']]=l['required_version']
        for obj in l["dependencies"]: 
            pkgs.update(MetaAnalyzer.find_meta(obj))
        return pkgs
    
    @staticmethod
    def analyze_Metadata(filename):
        packages = {}
        try:
            with open(filename) as jf:
                data=json.load(jf)
                if len(data)==0:
                    return {},'d_info_json.txt is empty!'
                
                pkgname=filename.split('/')[-3]
                
                # packages.update(MetaAnalyzer.find_meta(data[0]))
                for d in data:
                    if d["key"].replace("_",".").replace(".",".").replace("-",".")==pkgname.replace("_",".").replace(".",".").replace("-","."):
                        packages.update(MetaAnalyzer.find_meta(d))

        except json.decoder.JSONDecodeError as e:

            return {},'d_info_json.txt isnt jsonfile!'
        return packages,'success'

    @staticmethod
    def find_installed(l):
        pkgs={}  
        
        if l["dependencies"] == []:
            pkgs[l['key']]=l['installed_version']
            return pkgs
     
        pkgs[l['key']]=l['installed_version']
        for obj in l["dependencies"]: 
            pkgs.update(MetaAnalyzer.find_installed(obj))
        return pkgs
    
    @staticmethod
    def analyze_installtext(filename):
        try:
            with open(filename) as jf:
                data=json.load(jf)
                if len(data)==0:
                    return {}
                packages={}
                pkgname=filename.split('/')[-3]
                
                for d in data:
                    if d["key"].replace("_",".").replace(".",".").replace("-",".")==pkgname.replace("_",".").replace(".",".").replace("-","."):\
                        packages.update(MetaAnalyzer.find_installed(d))
                
                # packages.update(MetaAnalyzer.find_installed(data[0]))
                
        except json.decoder.JSONDecodeError as e:
            return {}
        return packages

    @staticmethod
    def analyze_all(egg_path,pypi,popu):
        My_ppkgs._instance(popu)
        My_pypi._instance(pypi)

        repo_path = "/".join(egg_path.split("/")[:-1])
        meta_packages = {}
        installtext = os.path.join(repo_path, "dependency_info_json.txt")
        install_packages = {}
        name=egg_path.split("/")[-3]
        
        dotdata = os.path.join(repo_path, "dependency_info_dot.json")
        status = 'false'
        if os.path.exists(installtext):
            
            meta_packages,notes=MetaAnalyzer.analyze_Metadata(installtext)
            install_packages= MetaAnalyzer.analyze_installtext(installtext)
            if notes!='success':
                return meta_packages,install_packages,"unknown"
        elif os.path.exists(dotdata):
            try:
                with open(dotdata,'r') as jf:
                    dot=json.load(jf)
            except:
                return meta_packages,install_packages,"unknown"
            install_packages=dot['install_dependency']
            meta_packages=dot['meta_dependency']
            for lin in meta_packages:
                reqs=meta_packages[lin]
                reqs_str=''
                for req in reqs:
                    reqs_str=reqs_str+','+req
                meta_packages[lin]=reqs_str

        new_metadict={}
        for key in meta_packages:
            if key in install_packages:
                new_metadict[key]=meta_packages[key]
        meta_packages=new_metadict

        todelete=''
        for x in meta_packages:
            if x.replace("_",".").replace(".",".").replace("-",".") == name.replace("_",".").replace(".",".").replace("-","."):
                todelete=x
        meta_packages.pop(todelete,None)
        install_packages.pop(todelete,None)

        status,notice_all = VersionCompare.VerCompare(meta_packages,install_packages)

        return meta_packages, install_packages, status


class VersionCompare:
    def __init__(self):
        pass
    @staticmethod
    def VerCompare(standard_packages,installed_packages):
        status=False
        forever_status='false'
        notice=''
        for standard in standard_packages:
            status=False
            
            if (standard_packages[standard]=='Any' or 'any' in standard_packages[standard] )and installed_packages[standard]!='?':
                continue
            
            if installed_packages[standard]=='?':
                return 'unknown',standard+' ?'
            if standard_packages[standard].strip()=='>dev':
                return 'unknown',standard+' >dev'
            #>=pyparsing
            
            # if re.match('>=[a-zA-Z]*',standard_packages[standard])!=None:
            #     if re.match('>=[a-zA-Z]*',standard_packages[standard]).span()[1]==len(standard_packages[standard]):
            #         return 'unknown',standard+' '+standard_packages[standard]
            #     if re.match('>[a-zA-Z]*',standard_packages[standard]).span()[1]==len(standard_packages[standard]):
            #         return 'unknown',standard+' '+standard_packages[standard]
            
            if standard_packages[standard]=='git-unknown' or installed_packages[standard]=='git-unknown':
                continue
            conditions,actual=VersionCompare.normalize(standard_packages[standard],installed_packages[standard])
            
            # print(standard+'  '+standard_packages[standard]+'   '+installed_packages[standard])
            # print(conditions,actual)
            try:
                for cond in conditions:
                    status= not(VersionCompare.judge(cond,actual,standard))
                    
                    if status==True:
                        forever_status='true'
                        notice=notice+''+standard+':\n\t'+standard_packages[standard]+'\n\t'+installed_packages[standard]+'\n'
            except:
                return 'unknown','bad results' 

        
        return forever_status,notice
    
    @staticmethod
    def judge_one_in_task4(standard,my_lis,pkgname):
        answer=[]
        if standard=='Any' or standard=='any':
            return my_lis
        for my in my_lis:
            if standard==my or standard=='git-unknown' or my=='git-unknown' or standard=='>dev':
                answer.append(my)
                continue


            conditions,actual=VersionCompare.normalize(standard,my)
            status=False
            forever_status=False
            for cond in conditions:
                status= not(VersionCompare.judge(cond,actual,pkgname))
                # print(status)
                if status==True:
                    forever_status=True
            if not forever_status:
                answer.append(my)
        return answer
        
    @staticmethod
    def judge(cond:str,actu:str,name:str):
        cond=cond.strip()
        actu=actu.strip()
        if cond.startswith('>=') or cond.startswith('<=') or cond.startswith('==') or cond.startswith('!='):
            ct=My_ppkgs.stt_get_time(name,cond[2:])
        elif cond.startswith('>') or cond.startswith('<'):
            ct=My_ppkgs.stt_get_time(name,cond[1:])
        else:
            ct=My_ppkgs.stt_get_time(name,cond)
        at=My_ppkgs.stt_get_time(name,actu)
        if ct==False or at==False or ct==None or at==None:
            cond=VersionCompare.post_strReplace(cond)
            actu=VersionCompare.post_strReplace(actu)
            if cond.startswith('>='):
                try:
                    return VersionCompare.s_compareLargerOrEqual(cond[2:],actu)
                except ValueError as e:
                    return False
            elif cond.startswith('<='):
                try:
                    return VersionCompare.s_compareSmallerOrEqual(cond[2:],actu)
                except ValueError as e:
                    return False
            elif cond.startswith('=='):
                try:
                    return VersionCompare.s_compareEqual(cond[2:],actu)
                except ValueError as e:
                    return False
            elif cond.startswith('!='):
                try:
                    return VersionCompare.s_compareNotEqual(cond[2:],actu)
                except ValueError as e:
                    return False
            elif cond.startswith('>'):
                try:
                    return VersionCompare.s_compareLarger(cond[1:],actu)
                except ValueError as e:
                    return False
            elif cond.startswith('<'):
                try:
                    return VersionCompare.s_compareSmaller(cond[1:],actu)
                except ValueError as e:
                    return False
            else:
                try:
                    return VersionCompare.s_compareEqual(cond,actu)
                except ValueError as e:
                    return False
        
        cond_time=datetime.datetime(int(ct[0:4]),int(ct[5:7]),int(ct[8:10]),int(ct[11:13]),int(ct[14:16]),int(ct[17:19]))
        actu_time=datetime.datetime(int(at[0:4]),int(at[5:7]),int(at[8:10]),int(at[11:13]),int(at[14:16]),int(at[17:19]))
        if cond.startswith('>='):
            return VersionCompare.compareLargerOrEqual(cond_time,actu_time)
        elif cond.startswith('<='):
            return VersionCompare.compareSmallerOrEqual(cond_time,actu_time)
        elif cond.startswith('=='):
            return VersionCompare.compareEqual(cond_time,actu_time)
        elif cond.startswith('!='):
            return VersionCompare.compareNotEqual(cond_time,actu_time)
        elif cond.startswith('>'):
            return VersionCompare.compareLarger(cond_time,actu_time)
        elif cond.startswith('<'):
            return VersionCompare.compareSmaller(cond_time,actu_time)
        else:
            return VersionCompare.compareEqual(cond_time,actu_time)
        
    @staticmethod
    def normalize(standards,actual):
        if standards.startswith(','):
            standards=standards[1:]
        standards=standards.replace('>',',>').replace('<',',<').replace("==",",==").replace("~=",",~=")
        if ',' in standards:
            standards=standards.split(',')
        else:
            standards=[standards]
        new_stnd=[]
        for stn in standards:
            if stn.strip()!='':
                if stn=='any':
                    continue
                stnn=VersionCompare.stringReplace(stn)
                if ',' in stnn:
                    stnn=stnn.split(',')
                    for x in stnn:
                        new_stnd.append(x)
                else:
                    new_stnd.append(stnn)
        actual=VersionCompare.stringReplace(actual)
        return new_stnd,actual
    
    
    
    @staticmethod
    def post_strReplace(strr:str):
        strr=strr.replace('a0','.0').replace('a1','.0').replace('b0','.0').replace('b1','.0')
        strr=strr.replace('dev','.0').replace('rc','.').replace('post','.').replace('-','.')
        newstr=''
        for i in range(0,len(strr)):
            if re.match(r'[a-zA-Z]',strr[i])!=None:
                newstr=newstr+('.'+str(ord(strr[i]))+'.')
            else:
                newstr=newstr+(strr[i])
        strr=newstr
        while strr.endswith('.'):
            strr=strr[:-1]
        if strr.startswith('>=.'):
            strr=strr.replace('>=.','>=')
        if strr.startswith('>.'):
            strr=strr.replace('>.','>')
        if strr.startswith('<=.'):
            strr=strr.replace('<=.','<=')
        if strr.startswith('<.'):
            strr=strr.replace('<.','<')
        while '..' in strr:
            strr=strr.replace('..','.')
        return strr
    
    @staticmethod
    def stringReplace(strr:str):
        # strr=strr.replace('a0','.0').replace('a1','.0').replace('b0','.0').replace('b1','.0')
        # strr=strr.replace('dev','.0').replace('rc','.').replace('post','.').replace('-','.')
        # newstr=''
        # for i in range(0,len(strr)):
        #     if re.match(r'[a-zA-Z]',strr[i])!=None:
        #         
        #         newstr=newstr+('.'+str(ord(strr[i]))+'.')
        #     else:
        #         newstr=newstr+(strr[i])
        # strr=newstr
        # print(strr)
        if '==' in strr and '*' in strr:
            #   ==16.* means >=16.0,<17
            #   ==1.4.* means >=1.4.0,<1.5
            orr=strr[2:-1].split('.')[:-1]
            orr[-1]=str(int(orr[-1])+1)
            neworr=''
            for o in orr:
                neworr=neworr+o+'.'
            neworr=neworr[:-1]
            newstr='>='+strr[2:-1]+'0,<'+neworr
            strr=newstr
        
        if '*' in strr:
            strr=strr.replace('*','')
        
        if '~' in strr:
            #~1.2.3	    >=1.2.3 <1.3.0
            #~1.2	    >=1.2.0 <1.3.0
            #~1	        >=1.0.0 <2.0.0
            if '.' in strr:
                lis=strr[1:].split(".")
                tmp='>'+strr[1:]+',<'
                i=0
                for x in lis:
                    i=i+1
                    if i==2:
                        x_new=''
                        for singl in x:
                            if re.match(r'[a-zA-Z]',singl)==None:
                                x_new+=singl
                        x=x_new
                        tmp=tmp+str(int(x)+1)+'.'
                    else:
                        tmp=tmp+x+'.'
                strr=tmp[:-1]
            else:
                strr='>'+strr[1:]+',<'+str(int(strr[1:])+1)
        while strr.endswith('.'):
            strr=strr[:-1]
        if strr.startswith('>=.'):
            strr=strr.replace('>=.','>=')
        if strr.startswith('>.'):
            strr=strr.replace('>.','>')
        while '..' in strr:
            strr=strr.replace('..','.')
        return strr
        

    @staticmethod
    def totalVersion(str):
        #str==ver？
        if re.match('(\d)+(\.(\d)+)*',str) ==None:
            return False
        return re.match('(\d)+(\.(\d)+)*',str).span()[1]==len(str)
    
    @staticmethod
    def s_compareLarger(b,a):
        #a>b?True:False
        a=a.strip().split('.')
        b=b.strip().split('.')
        for i in range(0,min(len(a),len(b))):
            if int(a[i])>int(b[i]):
                return True
            elif int(a[i])<int(b[i]):
                return False
        # 1.0.1 and 1.0
        if len(a)>len(b):
            if int(a[len(b)])>=0:
                return True
        return False
    @staticmethod
    def s_compareEqual(b,a):
        #a==b?True:False

        a=a.strip().split('.')
        b=b.strip().split('.')
        for i in range(0,min(len(a),len(b))):
            if a[i]!=b[i]:
                return False
        if len(a)<len(b):
            for i in range(len(a),len(b)):
                if int(b[i])!=0:
                    return False
        if len(b)<len(a):
            for i in range(len(b),len(a)):
                if int(a[i])!=0:
                    return False
        return True
    @staticmethod
    def s_compareLargerOrEqual(b,a):
        return VersionCompare.s_compareEqual(b,a) or VersionCompare.s_compareLarger(b,a)
    @staticmethod
    def s_compareSmaller(b,a):
        return not VersionCompare.s_compareLarger(b,a)
    @staticmethod
    def s_compareSmallerOrEqual(b,a):
        return (not VersionCompare.s_compareLarger(b,a)) or VersionCompare.s_compareEqual(b,a)
    @staticmethod
    def s_compareNotEqual(b,a):
        return not VersionCompare.s_compareEqual(b,a)
    @staticmethod
    def compareLarger(b,a):
        #a>b?True:False
        if a>b:
            return True
        else:
            return False
        # a=a.strip().split('.')
        # b=b.strip().split('.')
        # for i in range(0,min(len(a),len(b))):
        #     if int(a[i])>int(b[i]):
        #         return True
        #     elif int(a[i])<int(b[i]):
        #         return False
        # # 1.0.1 and 1.0
        # if len(a)>len(b):
        #     if int(a[len(b)])>=0:
        #         return True
        # return False
    @staticmethod
    def compareEqual(b,a):
        #a==b?True:False
        if a==b:
            return True
        else:
            return False
        # a=a.strip().split('.')
        # b=b.strip().split('.')
        # for i in range(0,min(len(a),len(b))):
        #     if a[i]!=b[i]:
        #         return False
        # if len(a)<len(b):
        #     for i in range(len(a),len(b)):
        #         if int(b[i])!=0:
        #             return False
        # if len(b)<len(a):
        #     for i in range(len(b),len(a)):
        #         if int(a[i])!=0:
        #             return False
        # return True
    @staticmethod
    def compareLargerOrEqual(b,a):
        return VersionCompare.compareEqual(b,a) or VersionCompare.compareLarger(b,a)
    @staticmethod
    def compareSmaller(b,a):
        return not VersionCompare.compareLarger(b,a)
    @staticmethod
    def compareSmallerOrEqual(b,a):
        return (not VersionCompare.compareLarger(b,a)) or VersionCompare.compareEqual(b,a)
    @staticmethod
    def compareNotEqual(b,a):
        return not VersionCompare.compareEqual(b,a)

