import paramiko as pmk
import time
import os

import tcpdump
import config
import netem


def start_code_horovod(model, b_size):
    hosts = config.HOSTS

    s = pmk.SSHClient()
    s.set_missing_host_key_policy(pmk.AutoAddPolicy())
    s.connect(hostname=hosts[0], port=1701, username='vagrant', password='vagrant')

    cmd = f"horovodrun -np 4 -H 192.168.17.50:1,192.168.17.51:1,192.168.17.52:1,192.168.17.53:1 " \
          f"--start-timeout 60 python3 /home/vagrant/script.py --model {model} --batchsize {b_size} &> " \
          f"/home/vagrant/output/train_history.log"

    command = f"tmux new -d -s code '$SHELL -c \"{cmd}; exec $SHELL\"'"

    s.exec_command(command)


def start_code_kungfu(model, b_size, topology):
    """

    :param model:
    :param b_size:
    :param topology: one of the available topologies: BINARY_TREE_STAR, CLIQUE, STAR, TREE
    :return:
    """
    index = 0
    for hostname in config.HOSTS:
        s = pmk.SSHClient()
        s.set_missing_host_key_policy(pmk.AutoAddPolicy())
        s.connect(hostname=hostname, port=1701, username='vagrant', password='vagrant')

        if index == 0:
            cmd = f"/home/vagrant/.local/bin/kungfu-run -np 4" \
                  f" -H 192.168.17.50:1,192.168.17.51:1,192.168.17.52:1,192.168.17.53:1" \
                  f" -nic eth1" \
                  f" -strategy {topology}" \
                  f" python3 /home/vagrant/script.py --model {model} --batchsize {b_size} --optimizer ssgd &>" \
                  f" /home/vagrant/output/train_history.log"
        else:
            cmd = f"/home/vagrant/.local/bin/kungfu-run -np 4" \
                  f" -H 192.168.17.50:1,192.168.17.51:1,192.168.17.52:1,192.168.17.53:1" \
                  f" -nic eth1" \
                  f" -strategy {topology}" \
                  f" python3 /home/vagrant/script.py --model {model} --batchsize {b_size} --optimizer ssgd"

        command = f"tmux new -d -s code '$SHELL -c \"{cmd}; exec $SHELL\"'"

        s.exec_command(command)

        index += 1


def start_code_tensorflow(model, b_size):
    index = 0
    for hostname in config.HOSTS:
        s = pmk.SSHClient()
        s.set_missing_host_key_policy(pmk.AutoAddPolicy())
        s.connect(hostname=hostname, port=1701, username='vagrant', password='vagrant')

        if index == 0:
            cmd = f"python3 /home/vagrant/script.py --worker_addrs 192.168.17.50:2222,192.168.17.51:2222,192.168.17.52:2222," \
                  f"192.168.17.53:2222" \
                  f" --task_index {index} --model {model} --batchsize {b_size}" \
                  f"&> /home/vagrant/output/train_history.log"
        else:
            cmd = f"python3 /home/vagrant/script.py --worker_addrs 192.168.17.50:2222,192.168.17.51:2222,192.168.17.52:2222," \
                  f"192.168.17.53:2222" \
                  f" --task_index {index} --model {model} --batchsize {b_size}"

        command = f"tmux new -d -s code '$SHELL -c \"{cmd}; exec $SHELL\"'"

        s.exec_command(command)

        index += 1


def run(models, batch_sizes, framework, backend, losses, topologies):
    for model in models:
        for b_size in batch_sizes:
            for topology in topologies:
                for loss in losses:
                    exp_name = f"{framework}-{model}-adam-{b_size}-{backend}-{loss}-{topology}"

                    if exp_name in os.listdir(f"{config.DATA_PATH}"):
                        print("Experiment already exists. Skipping this run.")

                    os.system(f"touch {config.DATA_PATH}experiment.txt")

                    tcpdump.start()

                    if int(loss) > 0:
                        netem.add_loss(loss)

                    time.sleep(10)

                    if framework == "tensorflow":
                        start_code_tensorflow(model=model, b_size=b_size)
                    elif framework == "horovod":
                        start_code_horovod(model=model, b_size=b_size)
                    elif framework == "kungfu":
                        start_code_kungfu(model=model, b_size=b_size, topology=topology)
                    else:
                        print("Unknown framework.")
                        continue

                    time.sleep(60)

                    tcpdump.stop(model=model)

                    if int(loss) > 0:
                        netem.remove_loss()

                    time.sleep(10)

                    # Clean-up and organize
                    os.system(f"mkdir {config.DATA_PATH}{exp_name}")
                    os.system(f"mv {config.DATA_PATH}*.pcap {config.DATA_PATH}{exp_name}/")
                    os.system(f"mv {config.DATA_PATH}*.log {config.DATA_PATH}{exp_name}/")
                    os.system(f"rm {config.DATA_PATH}experiment.txt")
