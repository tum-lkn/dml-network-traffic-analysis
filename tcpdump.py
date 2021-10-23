import paramiko as pmk
import time
import config


def start():
    ips = config.IPS

    index = 0
    for hostname in config.HOSTS:
        s = pmk.SSHClient()
        s.set_missing_host_key_policy(pmk.AutoAddPolicy())
        s.connect(hostname=hostname, port=1701, username='vagrant', password='vagrant')

        command = f"tmux new -d -s tcpdump '$SHELL -c \"sudo tcpdump src {config.IPS[index]} -i eth1 -s 100 -w " \
                  f"/home/vagrant/output/worker-{index}-tcpdump.pcap; exec $SHELL\"'"

        s.exec_command("sudo ip link set eth1 up")
        s.exec_command(f"sudo ip addr add {ips[index]}/24 dev eth1")
        s.exec_command(command)

        index += 1


def stop(model):
    condition = True
    for hostname in config.HOSTS:
        s = pmk.SSHClient()
        s.set_missing_host_key_policy(pmk.AutoAddPolicy())
        s.connect(hostname=hostname, port=1701, username='vagrant', password='vagrant')

        while condition:
            time.sleep(60)
            stdin, stdout, stderr = s.exec_command(f"ps -ef | grep -i {model}")
            if 'python3' not in str(stdout.read()):
                condition = False

        s.exec_command("sudo pkill tcpdump")
        s.exec_command("tmux kill-session -t tcpdump")
        s.exec_command("tmux kill-session -t code")
