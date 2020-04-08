import sys
import os
import imageio
import argparse
import pathlib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import cv2
import datetime
from glob import glob
from pathlib import Path
from tensorboard.backend.event_processing import event_accumulator

from PyQt5.QtWidgets import (QFileDialog, QAbstractItemView, QListView,
                             QTreeView, QApplication, QDialog)

# File directory dialog for selecting multiple directories.
# See usage in plotting functions.

class getExistingDirectories(QFileDialog):
    def __init__(self, *args):
        super(getExistingDirectories, self).__init__(*args)
        self.setOption(self.DontUseNativeDialog, True)
        self.setFileMode(self.Directory)
        self.setOption(self.ShowDirsOnly, True)
        self.findChildren(QListView)[0].setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.findChildren(QTreeView)[0].setSelectionMode(QAbstractItemView.ExtendedSelection)


# Tensorboard image/scalar extraction

def tb_extract(model_path=None, keys=['Loss'], anim=False):

    if model_path is None:
        qapp = QApplication(sys.argv)
        dirs = getExistingDirectories()
        if dirs.exec_() == QDialog.Accepted:
            model_path = dirs.selectedFiles()
            # print(model_path)
    elif 'Pycharm' not in model_path:
        model_path = os.path.join('/home/omar/PycharmProjects/mlmOK_Pytorch/models', model_path)

    for model in model_path:
        event_acc = event_accumulator.EventAccumulator(
            model, size_guidance={'images': 0})
        event_acc.Reload()

        outdir = pathlib.Path(model+'/out')
        outdir.mkdir(exist_ok=True, parents=True)

        for key in keys:
            if key == 'Loss':
                for tag in event_acc.Tags()['scalars']:
                    pd.DataFrame(event_acc.Scalars(tag)).to_csv(model+'/out/'+tag+'.csv')
                    f = plt.figure(figsize=(12, 6))
                    # print(pd.DataFrame(event_acc.Scalars(tag)))
                    plt.plot(pd.DataFrame(event_acc.Scalars(tag)).values[:,1],pd.DataFrame(event_acc.Scalars(tag)).values[:,2])
                    plt.xlabel('Epoch')
                    plt.ylabel(tag)
                    plt.yscale('log')
                    plt.savefig(model+'/out/'+tag+'.png')
            for tag in event_acc.Tags()['images']:

                if key in tag:
                    events = event_acc.Images(tag)

                    tag_name = tag.replace('/', '_')
                    dirpath = outdir / tag_name
                    dirpath.mkdir(exist_ok=True, parents=True)

                    for index, event in enumerate(events):
                        s = np.frombuffer(event.encoded_image_string, dtype=np.uint8)
                        image = cv2.imdecode(s, cv2.IMREAD_COLOR)
                        outpath = dirpath / '{:04}.jpg'.format(index)
                        cv2.imwrite(outpath.as_posix(), image, [int(cv2.IMWRITE_JPEG_QUALITY), 50])

                    if anim:
                        jpg_dir = dirpath
                        images = []
                        for file_name in os.listdir(jpg_dir):
                            if file_name.endswith('.jpg'):
                                file_path = os.path.join(jpg_dir, file_name)
                                images.append(imageio.imread(file_path))
                        imageio.mimsave(os.path.join(jpg_dir, tag_name + '.gif'), images, fps=2)








