#!/bin/bash

# Set hostname and timezone
sudo hostnamectl set-hostname master
sudo timedatectl set-timezone Asia/Seoul

# Reboot
if [ -f /var/run/reboot-required ]; then
    sudo reboot
    exit 0
fi

# Wait for the instance to reboot before running the remaining commands
sleep 60

# Update and install pre-setting
sudo apt-get update
sudo apt-get install net-tools
sudo apt-get install apt-transport-https
sudo apt-get install ca-certificates
sudo apt-get install curl
sudo apt-get install software-properties-common
sudo apt-get install gnupg
sudo apt-get install lsb-release

# Install Docker and Setting
sudo apt-get install docker.io
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu bionic stable"


# Configure modules
sudo tee /etc/modules-load.d/k8s.conf <<EOF
br_netfilter
EOF
sudo modprobe br_netfilter

# Configure sysctl
sudo tee /etc/sysctl.d/k8s.conf <<EOF
net.bridge.bridge-nf-call-ip6tables = 1
net.bridge.bridge-nf-call-iptables = 1
EOF
sudo sysctl --system

# Enable IP forwarding
echo 1 | sudo tee /proc/sys/net/ipv4/ip_forward

# Disable swap
sudo swapoff -a
sudo sed -i '/ swap / s/^\(.*\)$/#\1/g' /etc/fstab

# Disable UFW
sudo ufw status
sudo ufw disable
sudo systemctl status ufw
sudo systemctl stop ufw
sudo systemctl disable ufw

# Install necessary packages for Kubernetes
sudo apt-get update

# Add Kubernetes apt key
sudo curl -fsSLo /usr/share/keyrings/kubernetes-archive-keyring.gpg https://packages.cloud.google.com/apt/doc/apt-key.gpg
curl -s https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key add -

# Add Kubernetes apt repository
echo "deb https://apt.kubernetes.io/ kubernetes-xenial main" | sudo tee /etc/apt/sources.list.d/kubernetes.list

# Update and install Kubernetes packages
sudo apt-get update
sudo apt-cache show kubectl kubeadm kubelet | grep 1.24
sudo apt-get install -y kubelet=1.24.14-00
sudo apt-get install -y kubectl=1.24.14-00
sudo apt-get install -y kubeadm=1.24.14-00

# Hold Kubernetes packages at current version
sudo apt-mark hold kubelet kubeadm kubectl

# Enable IP forwarding
echo 1 | sudo tee /proc/sys/net/ipv4/ip_forward

# For MasterNode Setting
sudo kubeadm init --control-plane-endpoint="master.ec2-k8s..internal" --kubernetes-version=1.24.10
sudo -i
export KUBECONFIG=/etc/kubernetes/admin.conf
exit

mkdir -p $HOME/.kube
sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
sudo chown $(id -u):$(id -g) $HOME/.kube/config

# weave-daemon install
kubectl apply -f https://github.com/weaveworks/weave/releases/download/v2.8.1/weave-daemonset-k8s.yaml

# calico install
kubectl create -f https://raw.githubusercontent.com/projectcalico/calico/v3.19.0/manifests/tigera-operator.yaml
