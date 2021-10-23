# DML Network Traffic Measurements

This repository includes the source code for the measurements and the analysis scripts used for "Network Traffic
Characteristics of Machine Learning Frameworks Under the Microscope" by Johannes Zerwas, Kaan Aykurt, Stefan Schmid 
and Andreas Blenk (2021).

The collected traces are available at [https://mediatum.ub.tum.de/1632489]().

Folders:
- `analysis/`: parsing, aggregation and evaluation scripts
- `custombox`: Vagrant VM files
- `frameworks/`: Python automation of experiments. Scripts to run the DML trainings are in the sub-folders
  corresponding to each framework.

The remaining scripts and modules are shared for all the frameworks.

## Requirements

### On orchestrator/controller
- Install necessary python packages on the orchestrator/controller machine:
```bash
pip install paramiko pandas numpy seaborn sklearn matplotlib statsmodels
```
- Update `config.py`

### On the worker machines:
- Orchestrator must be able to SSH as root into worker nodes
- Worker nodes' root user must have a keypair for SSH
- Prepare the folder `/root/dependencies` with downloaded files under the following folder structre:
  - cuda-files (can be downloaded from NVIDIA Developer Program)
    - libcudnn7_7.6.5.32-1+cuda10.1_amd64.deb
    - libcudnn7-dev_7.6.5.32-1+cuda10.1_amd64.deb
    - libcudnn7-doc_7.6.5.32-1+cuda10.1_amd64.deb
  - golang (can be downladed from https://golang.org/)
    - go1.16.3.linux-amd64.tar.gz
- Update `custombox/custombox_ssh_install.sh` with the SSH pub-key of the orchestrator/controller node

## Running an Experiment
`run_experiment.py` script controls the whole VM creation and experiment running process. The script is run with following
parameters:
  - `framework`: name of the framework
  - `backend`: name of the communication backend (only for naming convention, desired backend 
    should be specified manually in custom box creation scripts)
  - `models`: models to be run, separated with commas
  - `batchsizes`: batch sizes of interest, separated with commas
  - `topologies`: topologies of interest, separated with commas (defaults to ring)
  - `losses`: losses of interest, separated with commas (defaults to 0)
  - `usebox`: flag to set intermediary custom box usage (currently only TensorFlow supports this, defaults to False)


Example: 
```bash
python3 run_experiment.py --framework kungfu --backend kungfu --models mobilenetv2,densenet201 --batchsizes 64
--topologies BINARY_TREE_STAR,TREE,CLIQUE --losses 0,0.05,0.1
```

Notes:
- Cuda and Golang dependencies should be in a file which should be passed through to the VM. 
- All VMs should be mounted a folder which the results are written into.
- In case the nodes have different internet connection speeds, a dummy experiment has to be run so that each worker
has a copy of the training dataset and no hanging occurs in the beginning.

### Settings to run

| Framework     | Backend                        | Models                                        | Batch Sizes   | Topologies                           | Losses                       | 
| ------------- | ------------------------------ | --------------------------------------------- | ------------- | ------------------------------------ | ---------------------------- |
| TensorFlow    | grpc, grpc_nccl                | mobilenetv2, densenet201, resnet50, resnet101 | 64, 128, 512  | ring                                 | 0, 0.05, 0.1, 0.2, 0.5, 1, 2 |
| Horovod       | mpi, mpi_nccl, gloo, gloo_nccl | mobilenetv2, densenet201, resnet50, resnet101 | 64, 128, 512  | ring                                 | 0                            |
| KungFu        | kungfu                         | mobilenetv2, densenet201, resnet50, resnet101 | 64            | BINARY_TREE_STAR, CLIQUE, STAR, TREE | 0                            |


### Evaluating the Results
Raw traces are first parsed via `parsing_script.py` and then aggregated via `aggregate.py` under `analysis/` folder.
A Jupyter Notebook (`analysis.ipynb`) is used for the evaluation and visualization of the results.
Folder names designate the experiment configuration in format `framework-model-optimizer-batchsize-backend-delay-(topology)`.

- Run parsing:
```bash
python parsing_script.py --path /path/to/datafoler
```
- Run aggregation:
```bash
python aggregate.py --path /path/to/datafoler
```