#!/usr/bin/env python3
import os
import shutil
import argparse
import subprocess
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

    print(f"CONFIRM: Do you want to select the partition '{device[0]}'? (y/n)")
    flag=input().lower()
    if flag=="y":
        print(f"You have selected the device '{device[0]}'")
        return device[index]
    elif flag!="n":
        exit(2)


def check_if_argument_is_passed(path, specifier, args):
    path = args.dst_path
    if path is None or not(os.path.exists(path)):
        device = choose_device(specifier)
    else:
        if os.path.exists(path):
            device = path

    return device

def keep_latest_config_files(src_dir, dst_dir):
    with os.scandir(src_dir) as src_entry, os.scandir(dst_dir) as dst_entry:
        for src_item in src_entry:
            if not src_item.name.startswith('.') and src_item.is_file():
                for dst_item in dst_entry:
                    if dst_item.is_file() and src_item.name == dst_item.name:
                        diff = subprocess.run(['diff', '-c', src_item.path, dst_item.path], stdout=subprocess.PIPE)
                        if diff.returncode == 0:
                            print(f"The src {src_item.name} is equal to the dst")
                        else:
                            print(f"ATTENTION: the dst {dst_item.name} is different from the src, you are going to lose data!!!")
                            print(diff.stdout.decode('utf-8'))
                            print(f"DEBUG: Do you want to replace it anyway? (y/n)")
                            flag=input().lower()
                            if flag=="y":
                                shutil.copy(src_item.path, dst_item.path)
                        

def expand(args): 
    device = check_if_argument_is_passed('dev_path', 'n', args)

    subprocess.run(['umount', device])
    subprocess.run(['sudo', 'e2fsck', '-f', device])
    subprocess.run(['sudo', 'growpart', device[:-1], device[-1]])
    subprocess.run(['sudo', 'resize2fs', '-f', device])

def move(args):
    package = args.package
    src_path = args.src_path
    force = args.f

    print(f"Move no longer compiles nodes before moving them... have you compiled {package}...")
    dst = check_if_argument_is_passed('dst_path', 'm', args)
    dst_path = os.path.join(dst, "usr")

    if (os.path.exists(dst_path)):
        output = subprocess.run(['find',  src_path,  '-name', package], stdout=subprocess.PIPE)
        results = output.stdout.decode('utf-8').split('\n')
        
        src_path_config = os.path.join(src_path, "install_arm64", package, "share", package, "config")
        src_path_launch = os.path.join(src_path, "install_arm64", package, "share", package, "launch")
        src_path_bin = os.path.join(src_path, BUILD_BASE, package)

        dst_path_config = os.path.join(dst_path, "share", package, "config")

        dst_path_launch = os.path.join(dst_path, "share", package, "launch")
        dst_path_bin = os.path.join(dst_path, "lib", package)

        print(src_path_bin)
        print(dst_path_bin)

        if not force:
            print(f"DEBUG: Do you want that {package} is going to replace the {dst}? (y/n)")
            flag = input().lower()
            if flag=="y":
                shutil.copytree(src_path_bin, dst_path_bin, dirs_exist_ok=True)
                shutil.copytree(src_path_launch, dst_path_launch, dirs_exist_ok=True)
                keep_latest_config_files(src_path_config, dst_path_config)
            elif flag!="y":
                print("ERROR: Invalid input")
                exit(2)
        else:
            shutil.copytree(src_path_bin, dst_path_bin, dirs_exist_ok=True)
            shutil.copytree(src_path_launch, dst_path_launch, dirs_exist_ok=True)
            keep_latest_config_files(src_path_config, dst_path_config)
    else:
        print(f"ERROR: {dst_path} doesn't exists!")
        exit(-1)

def invoke_build(args):
    try:
        build(args.src_path, args.package)
    except ... as e:
        print(e)
        print('Did you run "docker run --privileged --rm tonistiigi/binfmt --install all" before building? huh?')

def main():
    parser = argparse.ArgumentParser(prog='movex')
    subparsers = parser.add_subparsers(required=True)

    parser_move = subparsers.add_parser('move', help ='Move the ros node to the file system')
    parser_move.add_argument("-f", help='Do not ask for confirmation', action='store_true')
    parser_move.add_argument('package', type=str, help='Name of the package to move')
    parser_move.add_argument('src_path', type=str, help='Absolute path of development directory (directory that CONTAINS src)')
    parser_move.add_argument('dst_path', type=str, nargs='?', default=None, help='Path of the target storage (if already known)')
    parser_move.set_defaults(func=move)

    parser_expand = subparsers.add_parser('expand', help='expand the partition to maximize the device size')
    parser_expand.add_argument('dev_path', nargs='?', default=None)
    parser_expand.set_defaults(func=expand)

    parser_build = subparsers.add_parser('build', help='Cross compile for arm64 target')
    parser_build.add_argument('src_path', type=str, help='Path of development directory (directory that CONTAINS src)')
    parser_build.add_argument('package', type=str, help='Name of the package to move')
    parser_build.set_defaults(func=invoke_build)
    
    
    args = parser.parse_args()
    #print(args)
    args.func(args)


if __name__ == '__main__':
    main()
