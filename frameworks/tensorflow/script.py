import os
import sys
import json

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

# Keras outputs warnings using `print` to stderr so let's direct that to devnull temporarily
stderr = sys.stderr
sys.stderr = open(os.devnull, 'w')

import time
import argparse
import tensorflow as tf
from tensorflow.keras.applications.resnet import ResNet50
from tensorflow.keras.applications.resnet import ResNet101
from tensorflow.keras.applications.mobilenet_v2 import MobileNetV2
from tensorflow.keras.applications.densenet import DenseNet201
from tensorflow.python.distribute import cross_device_ops as cross_device_ops_lib

parser = argparse.ArgumentParser()
parser.add_argument("--worker_addrs", type=str, required=True,
                    help="ip:port of workers")
parser.add_argument("--task_index", type=int, required=True,
                    help="Index of task within the job")
parser.add_argument("--model", type=str, default="")
parser.add_argument("--batchsize", type=str, default="64")
args = parser.parse_args()

workers = args.worker_addrs.split(',')
num_workers = len(workers)

cluster_dict = {}
cluster_dict['cluster'] = {}
cluster_dict['cluster']['worker'] = workers
cluster_dict['task'] = {}
cluster_dict['task']['type'] = "worker"
cluster_dict['task']['index'] = str(args.task_index)

os.environ['TF_CONFIG'] = json.dumps(cluster_dict)

tf_config = json.loads(os.environ['TF_CONFIG'])

strategy = tf.distribute.experimental.MultiWorkerMirroredStrategy(
    communication=cross_device_ops_lib.CollectiveCommunication.RING)

epochs = 20
num_classes = 10
input_shape = (32, 32, 3)
per_worker_batch_size = int(args.batchsize)
global_batch_size = per_worker_batch_size * num_workers


def get_cifar10_dataset():
    (x_train, y_train), (x_test, y_test) = tf.keras.datasets.cifar10.load_data()

    y_train = tf.keras.utils.to_categorical(y_train, num_classes)

    if args.model == 'resnet50' or 'resnet101':
        x_train = tf.keras.applications.resnet50.preprocess_input(x_train)
    elif args.model == 'mobilenetv2':
        x_train = tf.keras.applications.mobilenet_v2.preprocess_input(x_train)
    elif args.model == 'densenet201':
        x_train = tf.keras.applications.densenet.preprocess_input(x_train)
    else:
        raise RuntimeError("Model does not exist!")

    return x_train, y_train


x_t, y_t = get_cifar10_dataset()


with strategy.scope():
    if args.model == 'resnet50':
        model = ResNet50(input_shape=input_shape, weights=None, classes=num_classes)
    elif args.model == 'mobilenetv2':
        model = MobileNetV2(input_shape=input_shape, weights=None, classes=num_classes)
    elif args.model == 'resnet101':
        model = ResNet101(input_shape=input_shape, weights=None, classes=num_classes)
    elif args.model == 'densenet201':
        model = DenseNet201(input_shape=input_shape, weights=None, classes=num_classes)
    else:
        raise RuntimeError("Model does not exist!")

    model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=0.001*num_workers),
                  loss='categorical_crossentropy', metrics=['acc'])

sys.stderr = stderr

tf.print("Type,ID,Timestamp,Loss,Accuracy")


class PrintOutCallBack(tf.keras.callbacks.Callback):
    def on_train_batch_end(self, batch, logs=None):
        print(f"Batch,{batch},{time.time()},{logs['loss']},{logs['acc']}")

    def on_epoch_end(self, epoch, logs=None):
        print(f"Epoch,{epoch},{time.time()},{logs['loss']},{logs['acc']}")


history = model.fit(x_t, y_t, batch_size=global_batch_size,
                    epochs=epochs, callbacks=[PrintOutCallBack()], verbose=0)
