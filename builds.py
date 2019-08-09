
# -*- coding: utf-8 -*-

import sys
import os
import getopt

from xml.dom.minidom import parse
import xml.dom.minidom


cwd = None

dist_dir =""
lib_dir = ""
obj_dir ="" 

cc = ""
include_list = []
warn_tag = ""
debug_tag= ""
std_tag = "" 
macro_list = [] 

def linux_cmd(cmd):
    return os.system(cmd)

def windows_cmd():
    pass

def dir_make(base_dir,sub_dir):
    target_dir = os.path.join(base_dir,sub_dir)
    exists = os.path.exists(target_dir)
    if exists:
        return
    else:
        os.mkdir(target_dir)
    pass

def detect(prop_config):
    global cc
    cc=prop_config["cc"]
    ret_val = linux_cmd("which %s" % cc)
    if ret_val is not 0:
        print("CC: %s not found" % cc)
        return 

    global dist_dir
    dist_dir = prop_config["dist-dir"]
    dir_make(cwd,dist_dir)

    global lib_dir
    lib_dir = prop_config["lib-dir"]
    dir_make(cwd,lib_dir)

    global obj_dir
    obj_dir = prop_config["obj-dir"]
    dir_make(cwd,obj_dir)

def config():
    pass

def make_executable(obj_list,target_name,lib_list,lib_dir_list):
    objects_tag = " ".join(obj_list)

    libs_tag = " ".join(["-l%s" % l for l in lib_list])

    lib_dirs_tag = " ".join(["-L%s" % d for d in lib_dir_list])

    link_cmd="%s -o %s/%s %s %s %s" % (cc,dist_dir,target_name,objects_tag,lib_dirs_tag,libs_tag)
    linux_cmd(link_cmd)
    pass

def make_static_lib(obj_list,target_name):
    objects_tag = " ".join(obj_list)

    ar_cmd="ar cr %s/lib%s.a %s" % (lib_dir,target_name,objects_tag)
    print(ar_cmd)    
    linux_cmd(ar_cmd)
    pass
def make_share_lib(obj_list,target_name):
    objects_tag = " ".join(obj_list)
    share_cmd="%s -shared -fPCI -o %s/lib%s.so %s" % (cc,lib_dir,target_name,objects_tag)
    print(share_cmd)    
    linux_cmd(share_cmd)
    pass

def dir_recursion(dir_path,file_handle_func):
    files=os.listdir(dir_path)

    subdirs = []
    for f in files:
        is_dir = os.path.isdir(f)
        if is_dir:
            subdirs.append(f)
        else:
            file_handle_func(f)
    for subdir in subdirs:
        dir_recursion(subdir,file_handle_func)
    pass

def config_phase(config_ele):
    var_list = config_ele.getElementsByTagName("var")
    config_file_list = config_ele.getElementsByTagName("file")
    # TODO
    pass
def target_execute_recursion(target_executing,targets):
    target_name = target_executing.getAttribute("name")
    print("\nexecuting target %s " % target_name)

    children_ele=target_executing.getchildren()
    for child_ele in children_ele:
        ele_tag = child_ele.tagName
        # TODO 做一个函数字典，自动执行 
        if ele_tag == "config":


    make_ele = target_executing.getElementsByTagName("make")[0]
    dependences = make_ele.getAttribute("dependences")
    print("found dependence %s" % dependences)
    dependence_list = [] if dependences is None or len(dependences.strip())==0 else dependences.split(",")
    for dependence in dependence_list:
        if targets.get(dependence) is None:
            continue

        static_lib =os.path.join(lib_dir,"lib%s.a" % dependence)
        share_lib =os.path.join(lib_dir,"lib%s.so" % dependence)
        print("detecting dependence lib %s or %s" %(static_lib,share_lib))
        if os.path.exists(static_lib) or os.path.exists(share_lib):
            print("detecting dependence lib %s or %s,at least one existed" %(static_lib,share_lib))
            continue
        target_execute_recursion(targets[dependence],targets)

    object_list = []
    def compile_and_collect_objects(src_file,src_dir):
        compile_phase(src_file,src_dir)
        object_list.append("%s/%s.obj" %(obj_dir,src_file))

    compile_ele=target_executing.getElementsByTagName("compile")[0]
    src_dir=compile_ele.getAttribute("src-dir")
    src_files = compile_ele.getAttribute("src-files")
    src_files = [] if len(src_files.strip())==0 else src_files.split(",")

    if len(src_files) ==1 and src_files[0].startswith("*"):
        src_list=filter(lambda ele: os.path.isfile(ele),[ os.path.join(src_dir,ele) for ele in os.listdir(src_dir)])
    else:
        src_list=src_files
    for src_file in src_list:
        compile_and_collect_objects(src_file,src_dir)

    sub_dirs = compile_ele.getAttribute("sub-dirs")
    sub_dirs = [] if len(sub_dirs.strip())==0 else sub_dirs.split(",")
    if len(sub_dirs) ==1 and sub_dirs[0].startswith("*"):
        sub_dirs=filter(lambda ele: os.path.isdir(ele),os.listdir(src_dir))
    for sub_dir in sub_dirs:
        dir_recursion(sub_dir,compile_and_collect_objects)

    make_type = make_ele.getAttribute("type")
    make_name = make_ele.getAttribute("name")
    make_phase(object_list,make_name,make_type,dependence_list)


def compile_phase(src_file,src_dir):
    includes_tag = " ".join(include_list)
    macros_tag="  ".join(macro_list)

    compile_dir = os.path.join(obj_dir,src_dir)
    if not  os.path.exists(compile_dir):
        dir_make(obj_dir,src_dir)

    compile_cmd="%s %s %s %s %s %s -c %s -o %s/%s.obj" % (cc,includes_tag,warn_tag,debug_tag,macros_tag,std_tag,src_file,obj_dir,src_file)
    print(compile_cmd)
    linux_cmd(compile_cmd)

def make_phase(objects,target_name,target_type,target_dependences):
    if target_type not in ["exe","static","share"]:
        print("target must be any of [exe,static,share]")
        return 
    if target_type == "exe":
        make_executable(objects,target_name,target_dependences,[lib_dir])
    elif target_type == "static":
        make_static_lib(objects,target_name)
    else:
        make_share_lib(objects,target_name)
    pass

if __name__ == "__main__":
    cwd = os.getcwd()

    DOMTree = xml.dom.minidom.parse("build.xml")
    build_context = DOMTree.documentElement

    properties = build_context.getElementsByTagName("property")

    prop_config = dict()
    for prop in properties:
        prop_config[prop.getAttribute("name")] = prop.getAttribute("value")
    detect(prop_config)

    include_dirs = prop_config["includes"]
    include_list=["-I%s" % i for i in include_dirs.split(",")]
    warn_tag = prop_config["warn"]
    debug_tag= prop_config["debug"]
    std_tag = prop_config["lang-std"]
    macros = prop_config["macros"]
    if len(macros.strip()) == 0:
        macros=[]
    else:
        macros=macros.split(",")
    macro_list=["-D%s" % m for m in macros]

    target_dict = dict()
    targets = build_context.getElementsByTagName("target")
    for target in targets:
        target_dict[target.getAttribute("name")]=target
    target_execute_recursion(target_dict["all"],target_dict)
    pass

