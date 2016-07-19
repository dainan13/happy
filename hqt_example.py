import sys

import eqt
import hqt
import app_example

if __name__ == '__main__' :
    
    app = eqt.QEApplication()
    
    win = hqt.QHDialog()
    win.show()

    win.resize(600,500)
    win.moveScreenCenter()
    
    win.openUrl("app://example.ewsgi/")
    
    sys.exit( app.exec_() )
