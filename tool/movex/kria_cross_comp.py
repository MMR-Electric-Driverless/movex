from __future__ import annotations
import docker
from docker import DockerClient, APIClient
from docker.models.containers import Container
from docker.errors import DockerException
from docker.types import Mount
import sys
from config import *

class DisposableContainer:
  def __init__(self, image_name: str):
    self._image_name: str = image_name
    self._client: DockerClient | None = None
    self._container: Container | None = None
  
  def __enter__(self) -> DisposableContainer:
    try:
      self._client = docker.from_env()
    except DockerException:
      print('Docker engine not found. Make sure to have a running Docker engine!')
      exit(1)

    return self
  
  def __exit__(self, type, value, tb) -> None:
    assert self._container, "Invalid container"
    self._container.stop(timeout=1)
    self._container.remove()
  
  def run_async(self, cmd: str) -> int:
    if not self._container: raise RuntimeError("Container not initialized")

    print(f"Running \"{cmd}\"...")
    client = APIClient()
    exec_handle = client.exec_create(self._container.id, cmd)
    stream = client.exec_start(exec_handle, stream=True)

    print(*[line.decode('utf-8') for line in stream], sep='')

    return client.exec_inspect(exec_handle['Id']).get('ExitCode')

class BuildDisposableContainer(DisposableContainer):
  SRC_DIR: str = '/home/mmr-kria-drive'

  def __init__(self, folder: str):
    super().__init__(IMAGE)
    self.__folder = folder
  
  def __enter__(self) -> DisposableContainer:
    super().__enter__()
    assert self._client, "Invalid client"

    try:
      self._client.images.get(IMAGE)
    except docker.errors.ImageNotFound:
      print(f'Downloading container {IMAGE}')
      self._client.api.pull(IMAGE, stream=False)
      print('Done!')
    
    src_folder = Mount(self.SRC_DIR, self.__folder, type='bind')
    self._container = self._client.containers.run(
      self._image_name,
      detach = True,
      stdin_open = True,  # To keep the container alive
      mounts = [src_folder],
      working_dir = BuildDisposableContainer.SRC_DIR
    )

    return self


def build(src_folder, package):
  with BuildDisposableContainer(src_folder) as container:
    cmd = "/bin/bash -c \"source /opt/ros/humble/setup.bash && {command}\""
    cmd0 = cmd.format(command="sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key -o /usr/share/keyrings/ros-archive-keyring.gpg")
    cmd1 = cmd.format(command="rosdep install --from-paths src --rosdistro humble --ignore-src -y --skip-keys 'fastcdr rti-connext-dds-6.0.1 urdfdom_headers' -r")
    cmd2 = cmd.format(command=f"colcon build --continue-on-error --build-base build_arm64 --install-base install_arm64 --parallel-workers 8 --packages-up-to {package}")
    
    container.run_async(cmd0)
    container.run_async("apt update")
    container.run_async(cmd1)
    container.run_async(cmd2)


def main():
  if len(sys.argv) < 2: raise RuntimeError("Missing source directory as first argument")
  build(sys.argv[1])

if __name__ == "__main__":
  main()
