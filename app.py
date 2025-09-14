import logging
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

import sys
from time import sleep
from pymeasure.log import console_log
from pymeasure.display.Qt import QtWidgets
from pymeasure.display.windows import ManagedWindow

from tc290_procedure import TC290Procedure


class MainWindow(ManagedWindow):

    def __init__(self):
        super().__init__(
            procedure_class=TC290Procedure,
            inputs=['temperatures', 'address'],
            displays=['temperatures'],
            x_axis='Time',
            y_axis='Temperature'
        )
        self.setWindowTitle('GUI Example')


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
