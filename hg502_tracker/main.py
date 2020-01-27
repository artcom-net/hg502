import sys

from PyQt5 import QtWidgets

from hg502_tracker.app import HG502App
from hg502_tracker.gui import HG502GUI
from hg502_tracker.hg502 import HG502

if sys.platform == 'win32':
    # This is necessary for the correct display of the icon on the taskbar.
    import ctypes

    app_id = 'mycompany.myproduct.subproduct.version'
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)


if __name__ == '__main__':
    qapp = QtWidgets.QApplication(sys.argv)
    app = HG502App(HG502GUI(), HG502(), qapp)
    app.run()
