import paramiko as pmk
import argparse
import time
import os

import config, deployment, kill_vms, experiment
from frameworks.kungfu.install import load_kungfu

parser = argparse.ArgumentParser()
parser.add_argument("--framework", type=str, required=True)
parser.add_argument("--backend", type=str, required=True)
parser.add_argument("--models", type=str, required=True)
parser.add_argument("--batchsizes", type=str, required=True)
parser.add_argument("--topologies", default="ring", type=str, required=False)
parser.add_argument("--losses", default="0", type=str, required=False)
parser.add_argument("--usebox", default=False, const=True, action="store_const")
args = parser.parse_args()

models = args.models.split(',')
batchsizes = args.batchsizes.split(',')
topologies = args.topologies.split(',')
losses = args.losses.split(',')

# Build and bring up thee VMs
deployment.deploy_vms(framework=args.framework, usebox=args.usebox)

# Check if the building has finished and destroy the corresponding tmux session,
for hostname in config.HOSTS:
    condition = True
    s = pmk.SSHClient()
    s.set_missing_host_key_policy(pmk.AutoAddPolicy())
    s.connect(hostname=hostname, port=22, username='root', password='')

    while condition:
        stdin, stdout, stderr = s.exec_command(f'ps -ef | grep -i ruby')
        if 'vagrant' not in str(stdout.read()):
            time.sleep(10)
            stdin, stdout, stderr = s.exec_command(f'ps -ef | grep -i ruby')
            if 'vagrant' not in str(stdout.read()):
                condition = False
        time.sleep(30)

if args.framework == "kungfu":
    load_kungfu()
    time.sleep(120)

# Start the experiment
experiment.run(models=models, batch_sizes=batchsizes, framework=args.framework, backend=args.backend,
               losses=losses, topologies=topologies)

# Check if the experiment has finished
while True:
    time.sleep(120)
    if "experiment.txt" not in os.listdir(f"{config.DATA_PATH}"):
        break

# Stop the experiment and kill everything
kill_vms.kill(framework=args.framework)
