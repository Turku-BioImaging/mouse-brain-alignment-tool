import sys
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QDialog, QApplication, QFileDialog
from PyQt5.uic import loadUi
import subprocess

class MainWindow(QDialog):
    def __init__(self):
        super(MainWindow, self).__init__()
        loadUi("C:/Users/zuzka/Desktop/Finland_2022/ARR/code/qt_guis/analyze.ui", self)
        self.browse.clicked.connect(self.browsefolder)
        self.start.clicked.connect(self.run)

    def browsefolder(self):
        global fname
        fname = QFileDialog.getExistingDirectory(self, "Select Directory", "C:/Users/zuzka/Desktop/Finland_2022/ARR")
        self.foldername.setText(fname)
        print(fname)

    def run(self):
        #exec(open("C:/Users/zuzka/Desktop/Finland_2022/ARR/code/explore_args_Z.py").read())
        #process = subprocess.Popen("conda run -n idt-allen-brain-map-reg python test.py %s" %(fname).split(), stdout=subprocess.PIPE)
        #output, error = process.communicate() 
        #print(process)       
        subprocess.call("python interactive_rois.py %s" %(fname), shell=True)

app = QApplication(sys.argv)
mainwindow = MainWindow()
widget = QtWidgets.QStackedWidget()
widget.addWidget(mainwindow)
widget.setFixedWidth(500)
widget.setFixedHeight(400)
widget.show()
sys.exit(app.exec_())
