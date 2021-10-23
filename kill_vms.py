import paramiko as pmk
import argparse
import config
import time
import os


def kill(framework):
    vm_path = os.path.join(config.PATH, "frameworks", framework)

    for hostname in config.HOSTS:
        s = pmk.SSHClient()
        s.set_missing_host_key_policy(pmk.AutoAddPolicy())
        s.connect(hostname=hostname, port=22, username='root', password='')

        s.exec_command(f"tmux new -d -s kill '$SHELL -c \"cd {vm_path}; vagrant halt; vagrant destroy -f; rm Vagrantfile; exec $SHELL\"'")
        time.sleep(20)
        s.exec_command("tmux kill-session -t kill")
        s.exec_command("tmux kill-session -t vagrant")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--framework", type=str, default=None)
    args = parser.parse_args()

    kill(framework=args.framework)
