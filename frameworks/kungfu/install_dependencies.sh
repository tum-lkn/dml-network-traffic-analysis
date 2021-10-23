function install_tf {
	pip3 install tensorflow==2.3.0
}

function install_open_mpi {
  sudo apt-get update
  sudo apt install -y cmake
	sudo apt-get -y install openmpi-bin openmpi-common openssh-client openssh-server libopenmpi-dev g++-4.8 gcc python3.6 python3-pip
	pip3 install --upgrade pip
}

function install_cuda {
  sudo add-apt-repository ppa:graphics-drivers/ppa
  sudo apt-get update
  sudo apt-get install nvidia-driver-440

  wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu1804/x86_64/cuda-ubuntu1804.pin
  sudo mv cuda-ubuntu1804.pin /etc/apt/preferences.d/cuda-repository-pin-600
  wget http://developer.download.nvidia.com/compute/cuda/10.1/Prod/local_installers/cuda-repo-ubuntu1804-10-1-local-10.1.243-418.87.00_1.0-1_amd64.deb
  sudo dpkg -i cuda-repo-ubuntu1804-10-1-local-10.1.243-418.87.00_1.0-1_amd64.deb
  sudo apt-key add /var/cuda-repo-10-1-local-10.1.243-418.87.00/7fa2af80.pub
  sudo apt-get update
  sudo apt-get -y install cuda

  sudo dpkg -i /home/vagrant/dependencies/cuda-files/libcudnn7_7.6.5.32-1+cuda10.1_amd64.deb
  sudo dpkg -i /home/vagrant/dependencies/cuda-files/libcudnn7-dev_7.6.5.32-1+cuda10.1_amd64.deb
  sudo dpkg -i /home/vagrant/dependencies/cuda-files/libcudnn7-doc_7.6.5.32-1+cuda10.1_amd64.deb

  sudo cp -P /home/vagrant/dependencies/cuda-files/cuda/include/cudnn.h /usr/local/cuda-10.1/include
  sudo cp -P /home/vagrant/dependencies/cuda-files/cuda/lib64/libcudnn* /usr/local/cuda-10.1/lib64/
  sudo chmod a+r /usr/local/cuda-10.1/lib64/libcudnn*

  echo 'export PATH=/usr/local/cuda-10.1/bin:$PATH' >> ~/.bashrc
  echo 'export LD_LIBRARY_PATH=/usr/local/cuda-10.1/lib64:$LD_LIBRARY_PATH' >> ~/.bashrc
  echo 'export PATH=/usr/local/cuda-10.1/bin:$PATH' >> /home/vagrant/.bashrc
  echo 'export LD_LIBRARY_PATH=/usr/local/cuda-10.1/lib64:$LD_LIBRARY_PATH' >> /home/vagrant/.bashrc
  source ~/.bashrc
  sudo ldconfig

}

function install_libs {
	pip3 install paramiko
}

function install_golang {
  sudo cp /home/vagrant/dependencies/golang/go1.16.3.linux-amd64.tar.gz /home/vagrant/go1.16.3.linux-amd64.tar.gz
	sudo rm -rf /usr/local/go
	sudo tar -C /usr/local -xzf /home/vagrant/go1.16.3.linux-amd64.tar.gz
	echo 'export PATH=$PATH:/usr/local/go/bin' >> /home/vagrant/.bashrc
	source /home/vagrant/.bashrc
}

install_open_mpi
install_libs
install_cuda
install_tf
install_golang
