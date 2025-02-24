#!/usr/bin/env python3
import os
import shutil
import argparse
import subprocess
from simple_term_menu import TerminalMenu

# the command has a sub instruction (move or expand)
# move <executable file> ... --> it takes the name/s of the ros nodes' executable file/s to replace in the file system
# move -f --> do not ask for confirmation

# expand:
# IMPORTANT: upgrade e2fsck -> https://askubuntu.com/questions/1497523/feature-c12-e2fsck-get-a-newer-version-of-e2fsck
# growpart -> sudo apt install cloud-guest-utils

# specifier: 
#           n -> name
#           m -> mountpoints
def chooseDevice(specifier):
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


def checkIfArgumentIsPassed(path, specifier, args):
    dict = getArgumentsAsDict(args)
    if (dict[path] is None or not(os.path.exists(dict[path]))):
        device = chooseDevice(specifier)
    else:
        if (os.path.exists(dict[path])):
            device = dict[path]

    return device


def getArgumentsAsDict(args):
    return vars(args)


def expand(args):
    device = checkIfArgumentIsPassed('dev_path', 'n', args)

    subprocess.run(['umount', device])
    subprocess.run(['sudo', 'e2fsck', '-f', device])
    subprocess.run(['sudo', 'growpart', device[:-1], device[-1]])
    subprocess.run(['sudo', 'resize2fs', '-f', device])
    

#TO-DO:
#   - understand the right destination inside the repository:
#       * launch -> /usr/share/<node_name>/launch/<node_name>_launch.py
#       * yaml   -> /usr/share/<node_name>/config/<node_name>_conf.yaml
#       * bin    -> /usr/lib/<node_name>/

def move(args):
    dict = getArgumentsAsDict(args)
    print(dict)
    src = dict['src_path']

    dst = checkIfArgumentIsPassed('dst_path', 'm', args)
    dst_path = os.path.join(dst, "usr")
    
    if (os.path.exists(dst_path)):
        output = subprocess.run(['find',  '..',  '-name', src], stdout=subprocess.PIPE)
        results = output.stdout.decode('utf-8').split('\n')
        
        #print(results[0])
        src_path = results[0]
        src_path_config = os.path.join(src_path, "config")
        src_path_launch = os.path.join(src_path, "launch")
        src_path_bin = os.path.join("..", "build", src)

        dst_path_config = os.path.join(dst_path, "share", src, "config")
        dst_path_launch = os.path.join(dst_path, "share", src, "launch")
        dst_path_bin = os.path.join(dst_path, "lib", src)
        
        if (dict['f'] is True) :
            print(f"DEBUG: Do you want that {src} is going to replace the {dst}? (y/n)")
            flag=input().lower()
            if flag=="y":
                #shutil.rmtree(dst)
                shutil.copytree(src_path_config, dst_path_config, dirs_exist_ok=True)
                shutil.copytree(src_path_launch, dst_path_launch, dirs_exist_ok=True)
                shutil.copytree(src_path_bin, dst_path_bin, dirs_exist_ok=True)
            elif flag!="n":
                print("ERROR: Invalid input")
                exit(2)
        else:
            #shutil.rmtree(dst)
            shutil.copytree(src_path_config, dst_path_config, dirs_exist_ok=True)
            shutil.copytree(src_path_launch, dst_path_launch, dirs_exist_ok=True)
            shutil.copytree(src_path_bin, dst_path_bin, dirs_exist_ok=True)
    else:
        print(f"ERROR: {dict['src_path']} doesn't exists!")
        exit(-1)

def main():
    parser = argparse.ArgumentParser(prog='movex')
    subparsers = parser.add_subparsers(required=True)

    parser_move = subparsers.add_parser('move', help ='move the ros node to the file system')
    parser_move.add_argument("-f", help='do not ask for confirmation', action="store_true")
    parser_move.add_argument('src_path', type=str)
    parser_move.add_argument('dst_path', type=str, nargs='?', default=None)
    parser_move.set_defaults(func=move)

    parser_expand = subparsers.add_parser('expand', help='expand the partition to maximize the device size')
    parser_expand.add_argument('dev_path', nargs='?', default=None)
    parser_expand.set_defaults(func=expand)
    
    args = parser.parse_args()
    #print(args)
    args.func(args)


if __name__ == '__main__':
    main()