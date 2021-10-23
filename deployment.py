import paramiko as pmk
import argparse
import subprocess
import config
import os


def deploy_vms(framework, usebox):
    vm_path = os.path.join(config.PATH, "frameworks", framework)
    custombox_path = os.path.join(config.PATH, "custombox")

    for hostname in config.HOSTS:
        s = pmk.SSHClient()
        s.set_missing_host_key_policy(pmk.AutoAddPolicy())
        s.connect(hostname=hostname, port=22, username='root', password='')

        if usebox:
            s.exec_command(f'cp {os.path.join(config.PATH, "Vagrantfile.template")} '
                           f'{os.path.join(vm_path, "Vagrantfile")}')
        else:
            s.exec_command(f'cp {os.path.join(config.PATH, "Vagrantfile_nobox.template")} '
                           f'{os.path.join(vm_path, "Vagrantfile")}')

        s.exec_command(f'sed -i \'s/hostname_here/{hostname}-1/\' {os.path.join(vm_path, "Vagrantfile")}')
        s.exec_command(f'sed -i \'s/datapath_here/{config.DATA_PATH}-1/\' {os.path.join(vm_path, "Vagrantfile")}')

        boxes = str(subprocess.check_output(["vagrant", "box", "list"]))
        if usebox:
            if framework not in boxes:
                # Build the box and bring it up
                s.exec_command(f"tmux new -d -s vagrant '$SHELL -c \"cd {custombox_path};"
                               f" cp {vm_path}/install_dependencies.sh {custombox_path}/install_dependencies.sh;"
                               f" vagrant up --provision;"
                               f" vagrant halt; vagrant package --output {framework}.box;"
                               f" vagrant box add {framework}.box --name measurements/{framework};"
                               f" cd {vm_path};"
                               f" sed -i \'s/ubuntu1804/{framework}/\' {os.path.join(vm_path, 'Vagrantfile')};"
                               f" rm {custombox_path}/install_dependencies.sh;"
                               f" vagrant up; exec $SHELL\"'")
            else:
                # Bring up the existing box
                s.exec_command(f"tmux new -d -s vagrant '$SHELL -c \"cd {vm_path};"
                               f" sed -i \'s/ubuntu1804/{framework}/\' {os.path.join(vm_path, 'Vagrantfile')};"
                               f" vagrant up; exec $SHELL\"'")
        else:
            s.exec_command(f"tmux new -d -s vagrant '$SHELL -c \"cd {vm_path};"
                           f" vagrant up; exec $SHELL\"'")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--framework", type=str, default=None)
    parser.add_argument("--nobox", default=True, const=False, action="store_const")
    args = parser.parse_args()

    deploy_vms(framework=args.framework, usebox=args.nobox)
