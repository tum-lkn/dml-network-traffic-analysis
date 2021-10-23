import paramiko as pmk
import time
import config


def load_kungfu():
    for hostname in config.HOSTS:
        s = pmk.SSHClient()
        s.set_missing_host_key_policy(pmk.AutoAddPolicy())
        s.connect(hostname=hostname, port=1701, username='vagrant', password='vagrant')

        s.exec_command(f"tmux new -d -s kungfu_install '$SHELL -c \"cd /home/vagrant/; "
                       f"git clone https://github.com/lsds/KungFu.git; "
                       f"cd /home/vagrant/KungFu; exec $SHELL\"'")

        time.sleep(1)

        s.exec_command("tmux send-keys -t kungfu_install 'pip3 install --no-index -U --user .' C-m")
