# kria-movex README

## Installation
To install the packages, run the following command:
```bash
pip install -r requirements.txt
```

## Docker Configuration

When we compile a ROS2 node from our machines, this node will be compiled for the architecture of the pc used (e.g. x86, ...), while we want the node to be compiled for arm64 (or aarch64) to stay consistent with the Kria architecture. **IMPORTANT**: run the docker image before using movex.

### Compose-based procedure (suggested)

1. **Download docker image from docker hub:** 
    ```bash 
      docker pull doclorenzo/mmr-cross-compilation:1.0
    ```
2. **Run the docker image:** 
   ```bash
    SRC_PATH=<mmr-kria-drive-path> docker compose run --rm mmr-cross-compile-container
   ```
   
    Set `mmr-kria-drive-path` to the absolute path of the `mmr-kria-drive` source code

### Manual procedure
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
    - **mmr-kria-drive-path:** absolute path of the `mmr-kria-drive` source code
    - **image_name:** name of the contaier (e.g. `mmr-cross-compile`)

> **ATTENTION**: the changes that are made to the container in the `/home` folder will also be made inside the filesystem that launches the container, so in this case in the mmr-kria-drive folder
>

### Understand Dockerfile

The Dockerfile contains in the first line the starting image, that is ubuntu 22.04 for arm64, and then executes (via “RUN”) all the shell commands needed to install ROS2, which can be found on the official documentation of ROS2 humble, with some differences.

**Important choices**
- ``DEBIAN_FRONTEND=noninteractive``: When installing the ros-dev-tools package, you are prompted to enter the timezone. This variable allows you to bypass this deadlock
- ``rosdep install && COPY``: Before launching rosdep install, which will install all the dependencies of the libraries used inside our ros nodes, we need to give it the workspace from which to find these dependencies. The ``COPY`` brings this workspace inside the image, so we need to put as the first argument of the ``COPY`` the folder in which the ros nodes are contained whose dependencies we want to resolve.
- ``ros-humble-``: All ros-humble- packages are the libraries used inside ros2 nodes, specifically in “canbus_bridge” and “canopen_bridge” at the time of writing this documentation.

```docker
FROM arm64v8/ubuntu:22.04
RUN apt update && apt install -y locales
RUN locale-gen en_US en_US.UTF-8
RUN update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
RUN export LANG=en_US.UTF-8
RUN apt install -y software-properties-common
RUN add-apt-repository universe
RUN apt update && apt install curl -y
RUN curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key -o /usr/share/keyrings/ros-archive-keyring.gpg
RUN echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" | tee /etc/apt/sources.list.d/ros2.list > /dev/null
RUN apt update
RUN apt install -y python3-flake8-docstrings 
RUN apt install -y python3-pip 
RUN apt install -y python3-pytest-cov 
RUN DEBIAN_FRONTEND=noninteractive apt install -y ros-dev-tools
RUN apt install -y ros-humble-ament-cmake
RUN apt install -y ros-humble-rclcpp
RUN apt install -y ros-humble-geometry-msgs
RUN apt install -y ros-humble-std-msgs
RUN apt install -y ros-humble-can-msgs
RUN rosdep init
RUN rosdep update --rosdistro humble
COPY mmr-kria-drive/ /home
RUN rosdep install --from-paths /home/src --rosdistro humble --ignore-src -y --skip-keys "fastcdr rti-connext-dds-6.0.1 urdfdom_headers"
RUN apt install ros-humble-sensor-msgs
```

## Usage


## Throubleshooting
If you are here, we both know that something went wrong...don't give up and see if one of your problems (because there will be several of them) have a solution in the following list:

### Docker configuration

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
