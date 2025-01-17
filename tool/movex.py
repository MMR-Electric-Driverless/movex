#!/usr/bin/env python3
import sys
import os
import shutil

# the command has a sub instruction (move or expand)
# move <executable file> ... --> it takes the name/s of the ros nodes' executable file/s to replace in the file system
# move -i --> do not ask for confirmation

# expand:

if len(sys.argv) < 3:
    print("ERROR: wrong number of parameters")
    exit(1)

if sys.argv[1] == "move":
    try:
        # -i flag
        if sys.argv[2]=="-i":
            for node_ex in sys.argv[3:]:
                print(f"DEBUG: the compiled node '{node_ex}' is going to replace the '/dev/sda/cazzi/{node_ex}'")
                if os.path.exists(f"/home/lorenzo/{node_ex}"):
                    os.replace(node_ex, f"/home/lorenzo/{node_ex}")
                else:
                    print("CONFIRM: the destination compiled node does not exists, do you want to add it anyway? (y/n)")
                    flag=input()
                    if flag=="y":
                        os.replace(node_ex, f"/home/lorenzo/{node_ex}")
                    elif flag!="n":
                        print("ERROR: Invalid input")
                        exit(2)

        # std command
        else:
            for node_ex in sys.argv[2:]:
                print(f"CONFIRM: the compiled node '{node_ex}' is going to replace the '/dev/sda/cazzi/{node_ex}' (y/n)")
                flag=input()
                if flag=="y":
                    if os.path.exists(f"/home/lorenzo/{node_ex}"):
                        os.replace(node_ex, f"/home/lorenzo/{node_ex}")
                    else:
                        print("CONFIRM: the destination compiled node does not exists, do you want to add it anyway? (y/n)")
                        flag=input()
                        if flag=="y":
                            os.replace(node_ex, f"/home/lorenzo/{node_ex}")
                        elif flag!="n":
                            print("ERROR: Invalid input")
                            exit(2)
                elif flag!="n":
                    print("ERROR: Invalid input")
                    exit(2)
    except FileNotFoundError:
        print("ERROR: The file doesnt't exist!")
        exit(-1)
                

elif sys.argv[1] == "expand":
    print(sys.argv[1])
    
else:
    print("ERROR: first parameter must be either 'move' or 'expand'")
    exit(2)