import glob
import json

from sklearn.metrics import confusion_matrix, classification_report
from tensorflow import keras

from BertTraining import batch_size, window_width, window_steps, out_shape
from aux_func.data_preprocess import Preprocessor
from matplotlib import pyplot as plt
import seaborn as sn
from BERT import BertModelLayer, SplitterLayer
import numpy as np
from aux_func.confussion_matrix import plot_confusion_matrix
import tensorflow as tf
import os
# print(tf.version)
from aux_func.load_model import load_model

gpus = tf.config.experimental.list_physical_devices('GPU')
if gpus:
    try:
        # Currently, memory growth needs to be the same across GPUs
        for gpu in gpus:
            tf.config.experimental.set_memory_growth(gpu, True)
    except RuntimeError as e:
        # Memory growth must be set before GPUs have been initialized
        print(e)


def test_model(model_path, run, patient, channels, out_shape):
    # out_shape = [window_width, 64]
    model = load_model(model_path)
    runs = ['test', 'train', 'val', 'full']
    patients = ['', 'pre', 'post']

    prepro = Preprocessor(batch_size,
                          window_width,
                          window_steps,
                          prueba=0,
                          limpio=0,
                          paciente=patient,
                          channels=channels,
                          transpose=True,
                          output_shape=out_shape)

    try:
        os.mkdir(model_path + f'\\{runs[run]}_{patients[patient]}' )
        os.mkdir(model_path + f'\\{runs[run]}_{patients[patient]}\\chunks')
        os.mkdir(model_path + f'\\{runs[run]}_{patients[patient]}\\full_eeg')


    except Exception:
        pass
    if run == 0:
        data = prepro.test_set
    if run == 1:
        data = prepro.train_set
    if run == 2:
        data = prepro.val_set
    if run == 3:
        data = prepro.dataset

    y_pred = []
    y_pred_zones = [[] for _ in range(8)]
    for x_data, y_data in zip(data[0], data[1]):
        test_dataset = prepro.tf_from_generator([x_data], [y_data])
        pred = model.predict(test_dataset, verbose=1)
        if len(pred) == 2:
            pred, zone_pred = pred
            for i, zone in enumerate(np.swapaxes(zone_pred, 0, 1)):
                y_pred_zones[i].append(np.argmax(np.asarray(np.mean(zone, axis=0))))
                try:
                    os.mkdir(model_path + f'\\{runs[run]}_{patients[patient]}\\chunks\\zones')
                    os.mkdir(model_path + f'\\{runs[run]}_{patients[patient]}\\full_eeg\\zones')
                except Exception:
                    pass
        y_pred.append(np.mean(pred, axis=0))
    # FULL EEGS FIRST
    y_pred = np.argmax(np.asarray(y_pred), axis=1)

    cf_matrix = confusion_matrix(data[1], y_pred)

    with open(model_path + f'\\{runs[run]}_{patients[patient]}/full_eeg/classification_report.txt', 'w') as f:
        print(classification_report(data[1], y_pred, labels=[0, 1], target_names=["No Parkinson", "Parkinson"]), file=f)
    print(cf_matrix)

    plot_confusion_matrix(cm=cf_matrix,
                          normalize=False,
                          target_names=["No Parkinson", "Parkinson"],
                          title="Matriz de confusión",
                          save=model_path + f'\\{runs[run]}_{patients[patient]}\\full_eeg\\test_eeg.png')

    if y_pred_zones[0]:
        for i, y_pred in enumerate(y_pred_zones):
            cf_matrix = confusion_matrix(data[1], y_pred)
            print(cf_matrix)
            plot_confusion_matrix(cm=cf_matrix,
                                  normalize=False,
                                  target_names=["No Parkinson", "Parkinson"],
                                  title="Matriz de confusión",
                                  save=model_path + f'\\{runs[run]}_{patients[patient]}\\full_eeg\\zones\\test_confussion_zone_{i + 1}_matrix.png')

    # CHUNKS NOW
    full, train, test, val = prepro.classification_generator_dataset()
    dataset, train_dataset, test_dataset, val_dataset = prepro.classification_tensorflow_dataset()
    if run == 0:
        _, y_data = zip(*list(test))
        data_dataset = test_dataset
    if run == 1:
        _, y_data = zip(*list(train))
        data_dataset = train_dataset
    if run == 2:
        _, y_data = zip(*list(val))
        data_dataset = val_dataset
    if run == 3:
        _, y_data = zip(*list(full))
        data_dataset = dataset

    y_data = list(y_data)


    y_pred = model.predict(data_dataset, verbose=1)
    y_pred_zones = []
    if len(y_pred) == 2:
        y_pred, y_pred_zones = y_pred
        y_pred_zones = np.argmax(np.swapaxes(y_pred_zones, 0, 1), axis=2)
    y_pred = np.argmax(y_pred, axis=1)

    cf_matrix = confusion_matrix(y_data, y_pred)

    with open(model_path + f'\\{runs[run]}_{patients[patient]}\\chunks/classification_report.txt', 'w') as f:
        print(classification_report(y_data, y_pred, labels=[0, 1], target_names=["No Parkinson", "Parkinson"]), file=f)
    print(cf_matrix)

    plot_confusion_matrix(cm=cf_matrix,
                          normalize=False,
                          target_names=["No Parkinson", "Parkinson"],
                          title="Matriz de confusión",
                          save=model_path + f'\\{runs[run]}_{patients[patient]}\\chunks\\test_eeg.png')
    if y_pred_zones != []:
        for i, y_pred in enumerate(y_pred_zones):
            cf_matrix = confusion_matrix(y_data, y_pred)
            print(cf_matrix)
            plot_confusion_matrix(cm=cf_matrix,
                                  normalize=False,
                                  target_names=["No Parkinson", "Parkinson"],
                                  title="Matriz de confusión",
                                  save=model_path + f'\\{runs[run]}_{patients[patient]}\\chunks\\zones\\test_confussion_zone_{i + 1}_matrix.png')

if __name__ == "__main__":
    channels = [9, 10, 11, 12, 13, 19, 20, 21, 22, 23, 29, 30, 31, 32, 33, 39, 40, 41, 42, 43, 49, 50, 51, 52, 53]
    out_shape = [window_width, len(channels), 1]
    model_path = "C:\\Users\\Ceiec01\\OneDrive - UFV\\PFG\\Codigo\\checkpoints\\BERT-HigherDropout-Final"
    for run in range(3):
        test_model(model_path, run, 1, channels,out_shape)
    test_model(model_path, 3,  2, channels, out_shape)
    channels = []
    out_shape = [window_width, 64, 1]
    model_path = "C:\\Users\\Ceiec01\\OneDrive - UFV\\PFG\\Codigo\\checkpoints\\BERT-HigherDropout-64"
    for run in range(3):
        test_model(model_path, run, 1, channels, out_shape)
    test_model(model_path, 3, 2, channels, out_shape)

    out_shape = [window_width, 64]
    model_path = "C:\\Users\\Ceiec01\\OneDrive - UFV\\PFG\\Codigo\\checkpoints\\BERT-Zones-Final"
    for run in range(3):
        test_model(model_path, run, 1, channels, out_shape)
    test_model(model_path, 3, 2, channels, out_shape)
