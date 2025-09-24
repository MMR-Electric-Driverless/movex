# Movex

## Usage
Movex supports three subcommands:
 - move: moves a ROS2 node from the host to the Kria's micro SD card
 - expand: expands micro SD's root partition taking up all available free space
 - build: cross-compile a ROS2 node on any host for Kria's arm64 architecture

Each subcommand has a different syntax and supports a different set of parameters.
Use `-h` option to retrieve it:
```bash
python3 -m movex {move,expand,build} -h
```

## Installation
### From PyPI (suggested)
Install with `pip` by running:
```bash
pip install movex
```

Make sure `pip` is invoked by, at least, python version 3.12.

### From source
Clone [this repository](https://github.com/MMR-Electric-Driverless/movex).

To install the dependencies, run the following command:
```bash
pip install -r requirements.txt
```

## Docker Container Setup

When we compile a ROS2 node from our machines, the node will be compiled for the architecture of the host PC (e.g. x86, ...), while we want the node to be compiled for arm64 (also named aarch64) to stay consistent with the Kria architecture. **IMPORTANT**: run the docker image at least once before using movex.

### Pull from Docker Hub (suggested)

Download image from Docker Hub:
```bash 
  docker pull doclorenzo/mmr-cross-compilation:1.0
```

### Compose Based Procedure
Clone [mmr-cross-compilation](https://github.com/doclorenzo/mmr-cross-compilation) repository.

Run the docker image from compose file:
```bash
SRC_PATH=<mmr-kria-drive-path> docker compose run --rm mmr-cross-compile-container
```
   
Set `mmr-kria-drive-path` to the absolute path of the `mmr-kria-drive` source code

### Dockerfile Procedure
Clone [mmr-cross-compilation](https://github.com/doclorenzo/mmr-cross-compilation) repository.

If you are not willing to use the compose-based procedure, you can always opt for the manual procedure which involves build and interactive execution of the image.

1. **Build container**
    ```bash
    docker build -t mmr-cross-compile <dockerfile_folder> --platform=linux/arm64/v8
    ```
   - **dockerfile_folder:** path of the folder where it is contained the Dockerfile
 
 2. **Run the docker image:**
    ```bash
    docker run --platform=linux/arm64/v8 --rm -it --volume=<mmr-kria-drive-path>:/home/mmr-kria-drive <image_name> 

    ```
    - **mmr-kria-drive-path**: absolute path of the `mmr-kria-drive` source code
    - **image_name**: name of the contaier (e.g. `mmr-cross-compile`)

> **ATTENTION**: the changes that are made to the container in the `/home` folder will also be made inside the filesystem that launches the container, so in this case, in the <mmr-kria-drive> folder

## Throubleshooting
If you are here, we both know that something went wrong... don't give up and see if one of your problems (because there will be several of them) have a solution in the following list:

1.  **Can't build/run the docker image, giving back this error: `exec /bin/bash: exec format error `**
    
    Let's give a try on this:

    ```bash 
    docker run --privileged --rm tonistiigi/binfmt --install all 
    ```

    for further information, checks the [docker docs](https://docs.docker.com/build/building/multi-platform/)

2. **Docker engine not found. Make sure to have a running Docker engine!** 
   
   Probably the docker engine is not autorizhed to accept commands from your current user, try:
   ```bash
    sudo usermod -aG docker $USER
   ```
   then reboot your system.
