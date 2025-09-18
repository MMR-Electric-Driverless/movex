#!/usr/bin/env python3
import os
import re
import shutil
import argparse
import subprocess
from filecmp import dircmp
from simple_term_menu import TerminalMenu
from kria_cross_comp import build
from config import *

# expand:
# IMPORTANT: upgrade e2fsck -> https://askubuntu.com/questions/1497523/feature-c12-e2fsck-get-a-newer-version-of-e2fsck
# growpart -> sudo apt install cloud-guest-utils

#       * launch -> /usr/share/<node_name>/launch/<node_name>_launch.py
#       * yaml   -> /usr/share/<node_name>/config/<node_name>_conf.yaml
#       * bin    -> /usr/lib/<node_name>/

# specifier: 
#           n -> name
#           m -> mountpoints
def choose_device(specifier):
    options = {'n': 0, 'm': 2}
    index = options[specifier]

    output = subprocess.run(['lsblk', '-o', 'NAME,SIZE,MOUNTPOINTS'], stdout=subprocess.PIPE)
    results = output.stdout.decode('utf-8').split('\n') 
    # IMPORTANT: last item mustn't be a '\n'
    results.pop()

    terminal_menu = TerminalMenu(results[1:], title=results[0])
    menu_entry_index = terminal_menu.show()
    device = results[menu_entry_index + 1].split()
    # Keep only the alphanumeric numbers for a clean device name
    device[0] = ''.join(filter(str.isalnum, device[0]))
    device[0] = ''.join(('/dev/', device[0]))

    #print(device)

    print(f"CONFIRM: Do you want to select the partition '{device[0]}'? (y/n)", end=' ', flush=True)
    flag=input().lower()

    if flag != "y" and flag != "Y": exit(2)

    print(f"You have selected the device '{device[0]}'")
    return device[index]


def check_if_path_is_passed(args, specifier):
    path = args.dst_path
    if path is None or not(os.path.exists(path)):
        device = choose_device(specifier)
    elif os.path.exists(path):
        device = path

    return device

def copy_config(src_dir, dst_dir):
    """Copy config file(s). Confirmation is prompted before overwriting.
    """
    config_files_cmp = dircmp(src_dir, dst_dir, shallow=False)
    common_files = config_files_cmp.same_files
    if common_files: print(f"[DEBUG] Found identical files: {common_files}")

    for diff_file in config_files_cmp.diff_files:
        print(f'[ATTENTION] "{diff_file}" differs, Do you want to replace it anyway? (y/n)', end=' ', flush=True)
        flag=input().lower()
        if flag=="y":
            src_file, dst_file = os.path.join(src_dir, diff_file), os.path.join(dst_dir, diff_file)
            shutil.copy(src_file, dst_file)
            print(f"[DEBUG] Overwritten file: {diff_file}")
    
    for left_file in config_files_cmp.left_only:
        src_file, dst_file = os.path.join(src_dir, left_file), os.path.join(dst_dir, left_file)
        shutil.copy(src_file, dst_file)
        print(f"[DEBUG] Copyied src-only files: {left_file}")                        

def expand(args): 
    device = check_if_path_is_passed(args, 'n')

    subprocess.run(['umount', device])
    subprocess.run(['sudo', 'e2fsck', '-f', device])
    subprocess.run(['sudo', 'growpart', device[:-1], device[-1]])
    subprocess.run(['sudo', 'resize2fs', '-f', device])

def move(args):
    package = args.package
    src_path = args.src_path
    
    print(f"Move no longer compiles nodes before moving them... have you compiled {package}...")
    dst = check_if_path_is_passed(args, 'm')
    dst_path = os.path.join(dst, "usr")

    if not os.path.exists(dst_path):
        print(f"ERROR: {dst_path} doesn't exists!")
        exit(-1)

    src_path_config = os.path.join(src_path, "install_arm64", package, "share", package, "config")
    src_path_launch = os.path.join(src_path, "install_arm64", package, "share", package, "launch")
    src_path_bin = os.path.join(src_path, BUILD_BASE, package)

    dst_path_config = os.path.join(dst_path, "share", package, "config")

    dst_path_launch = os.path.join(dst_path, "share", package, "launch")
    dst_path_bin = os.path.join(dst_path, "lib", package)
    
    # For each package in src_path/install_arm64/ look inside the package for files that match the following regexs
    # <package_name>/lib/lib<package_name>__rosidl_typesupport_cpp.so
    # <package_name>/lib/lib<package_name>__rosidl_typesupport_fastrtps_cpp.so
    # <package_name>/lib/lib<package_name>__rosidl_typesupport_introspection_cpp.so
    # these files will be copied on the destination under /usr/lib
    
    interface_files = []
    
    patterns = [
        re.compile(r".*/([^/]+)/lib/lib\1__rosidl_typesupport_cpp\.so$"),
        re.compile(r".*/([^/]+)/lib/lib\1__rosidl_typesupport_fastrtps_cpp\.so$"),
        re.compile(r".*/([^/]+)/lib/lib\1__rosidl_typesupport_introspection_cpp\.so$")
    ]
    
    for current_dir, sub_dirs, files in os.walk(os.path.join(src_path, "install_arm64")):
        for file in files:
            filepath = os.path.join(current_dir, file)
            for pattern in patterns:
                if pattern.match(filepath):
                    interface_files.append(filepath)

    print(src_path_bin)
    print(dst_path_bin)
    print("interface files found:")
    for file in interface_files:
        print(file)


    print(f"DEBUG: Do you want to replace {package} in {dst}? (y/n)", end=' ', flush=True)
    flag = input().lower()
    
    if flag != "y" and flag != "Y":
        print("ERROR: Invalid input")
        exit(2)

    shutil.copytree(src_path_bin, dst_path_bin, dirs_exist_ok=True)

    if os.path.exists(src_path_launch) and os.path.isdir(src_path_launch):
        shutil.copytree(src_path_launch, dst_path_launch, dirs_exist_ok=True)
    
    if os.path.exists(src_path_config) and os.path.isdir(src_path_config):
        copy_config(src_path_config, dst_path_config)
        
    dst_path_lib = os.path.join(dst_path, "lib")

    for src_file in interface_files:
        dst_file = os.path.join(dst_path_lib, os.path.basename(src_file))
        shutil.copy(src_file, dst_file)
        print(f"Copied {src_file} -> {dst_file}")


def invoke_build(args):
    src_path = os.path.abspath(args.src_path)
    
    try:
        build(src_path, args.package)
    except Exception as e:
        print(e, '\n\nDid you run "docker run --privileged --rm tonistiigi/binfmt --install all" before building? huh?')

def invoke_move(args):
    try: move(args)
    except (PermissionError, shutil.Error) as e: print(e, "\n\nMaybe u need to run as superuser. Is your disk mounted in /mnt? Eh?")

def main():
    parser = argparse.ArgumentParser(prog='movex')
    subparsers = parser.add_subparsers(required=True)

    parser_move = subparsers.add_parser('move', help ='Move the ros node to the file system')
    parser_move.add_argument('package', type=str, help='Name of the package to move')
    parser_move.add_argument('src_path', type=str, help='Absolute path of development directory (directory that CONTAINS src)')
    parser_move.add_argument('dst_path', type=str, nargs='?', default=None, help='Path of the target storage (if already known)')
    parser_move.set_defaults(func=invoke_move)

    parser_expand = subparsers.add_parser('expand', help='expand the partition to maximize the device size')
    parser_expand.add_argument('dev_path', nargs='?', default=None)
    parser_expand.set_defaults(func=expand)

    parser_build = subparsers.add_parser('build', help='Cross compile for arm64 target')
    parser_build.add_argument('src_path', type=str, help='Path of development directory (directory that CONTAINS src)')
    parser_build.add_argument('package', type=str, help='Name of the package to move')
    parser_build.set_defaults(func=invoke_build)
    
    args = parser.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
