import paramiko as pmk
import config


def add_loss(loss):
    for hostname in config.HOSTS:
        s = pmk.SSHClient()
        s.set_missing_host_key_policy(pmk.AutoAddPolicy())
        s.connect(hostname=hostname, port=1701, username='vagrant', password='vagrant')

        s.exec_command(f"sudo tc qdisc add dev eth1 root netem loss {loss}%")


def remove_loss():
    for hostname in config.HOSTS:
        s = pmk.SSHClient()
        s.set_missing_host_key_policy(pmk.AutoAddPolicy())
        s.connect(hostname=hostname, port=1701, username='vagrant', password='vagrant')

        s.exec_command("sudo tc qdisc del dev eth1 root netem")
