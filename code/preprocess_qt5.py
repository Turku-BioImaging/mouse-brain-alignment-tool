import sys
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QDialog, QApplication, QFileDialog, QRadioButton
from PyQt5.uic import loadUi
import subprocess

class MainWindow(QDialog):
    def __init__(self):
        super(MainWindow, self).__init__()
        loadUi("C:/Users/zuzka/Desktop/Finland_2022/ARR/code/qt_guis/preprocess.ui", self)
        self.browse.clicked.connect(self.browsefolder)
        self.slidecount()
        self.animalcount()
        self.slides_1.clicked.connect(self.slidecount)
        self.slides_2.clicked.connect(self.slidecount)
        self.animals_1.clicked.connect(self.animalcount)
        self.animals_2.clicked.connect(self.animalcount)
        self.process.clicked.connect(self.run)

    def slidecount(self):
        global nslides
        nslides = "2"
        self.group_animals.setEnabled(True)
        self.animal_names.setEnabled(True)
        if self.slides_1.isChecked() == True:
            nslides = "1"
            self.group_animals.setEnabled(False)
            self.animal_names.setEnabled(False)

    def animalcount(self):
        global nanimals
        nanimals = "2"
        self.animal_names.setEnabled(True)
        if self.animals_1.isChecked() == True:
            nanimals = "1"
            self.animal_names.setEnabled(False)

    def browsefolder(self):
        global fname
        fname = QFileDialog.getExistingDirectory(self, "Select Directory", "C:/Users/zuzka/Desktop/Finland_2022/ARR")
        self.foldername.setText(fname)
        print(fname)

    def run(self):
        nameL, nameR = self.animal_left.text(), self.animal_right.text()        
        if self.animal_names.isEnabled() == True:
            nanimals = "2"
            subprocess.call("python explore_args_Z.py %s %s %s %s %s" %(fname, nslides, nanimals, nameR, nameL), shell=True)
        else:
            nanimals = "1"
            subprocess.call("python explore_args_Z.py %s %s %s" %(fname, nslides, nanimals), shell=True)

app = QApplication(sys.argv)
mainwindow = MainWindow()
widget = QtWidgets.QStackedWidget()
widget.addWidget(mainwindow)
widget.setFixedWidth(700)
widget.setFixedHeight(500)
widget.show()
sys.exit(app.exec_())