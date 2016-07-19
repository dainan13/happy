
from PyQt5.QtCore import *
#from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtWebEngineCore import *
from PyQt5.QtWebEngineWidgets import *

import sys
import os
import os.path
import threading

#import yaml

# http://blog.csdn.net/flowingflying/article/details/6153114
# http://blog.csdn.net/qiurisuixiang/article/details/6916603

class QAlignLayout( QLayout ):
    
    def __init__( self, parent ):
        
        super().__init__(parent)
        self.itemlist = []
        
    #在我们存储的数据中加入元素，addItem在实际上是很少调用的，一般都会使用addWidget，它将使用addItem。
    def addItem( self, index ):
        return
    
    #takeAt表示从list中删除index的item，并返回它，而index必须是有效的数值
    def takeAt( self, index ):
        return self.itemlist.pop(index)[0] if index >=0 and index < len(self.itemlist) else None
        
    def itemAt( self, index ):
        return self.itemlist[index][0] if index >=0 and index < len(self.itemlist) else None
        
    def count( self ):
        return len( self.itemlist )
        
    #def addWidget( self, widget, px, py, dx, dy, pw=None, ph=None, dw=None, dh=None ):
    #    self.itemlist.append( (QWidgetItem(widget), (float(px), float(py), dx, dy, pw, ph, dw, dh)) )
    #    return
        
    def addWidget( self, widget, align ):
        self.itemlist.append( (QWidgetItem(widget), align) )
        return
        
    def expandingDirections( self ):
        #print(dir(Qt))
        return Qt.Vertical | Qt.Horizontal
        
    # implemented in subclasses to return the preferred size of this item
    def sizeHint( self ):
        return self.calculateSize( "SizeHint" )
        
    def minimumSize( self ):
        return self.calculateSize( "MinimumSize" )
        
    # 将各item的大小进行统计获得layout的大小
    def calculateSize( self, sizetype ):
        
        return QSize(0,0)
        
    def setGeometry( self, rect ):
        
        ax, ay, aw, ah = rect.getRect()

        for item, align in self.itemlist :
            
            bwh = item.sizeHint()
            wid = item.widget()
            bw, bh = bwh.width(), bwh.height()
            bx, by = wid.x, wid.y
            
            item.setGeometry( align( wid, (ax, ay, aw, ah), (bx, by, bw, bh) ) )
        
        return

def QELa_Align( px, py, dx, dy, pw=None, ph=None, dw=None, dh=None ):
    
    pw = None if pw is None else float(pw) 
    ph = None if ph is None else float(ph)
    dw = dw or 0
    dh = dh or 0
    
    def align( bwidget, a, b ):
        
        ax, ay, aw, ah = a
        bx, by, bw, bh = b
        
        if pw != None :
            bw = int( round(aw*pw) )+dw
        if ph != None :
            bh = int( round(ah*ph) )+dh
        
        bx = ax + int(round( px*(aw-bw) )) + dx
        by = ay + int(round( py*(ah-bh) )) + dy
        
        return QRect( bx, by, bw, bh ) 
    
    return align

#import win32gui
#import win32con

# http://stackoverflow.com/questions/328492/setting-monitor-power-state-in-python

#class QETitleWidget( QWidget ):
#    
#    def __init__( self, parent ):
#        super().__init__( parent )
#        self.mouse_pressed = False
#        return
#    
#    def mousePressEvent( self, event ):
#        
#        # 这里releaseCapture返回值为None，无法进入系统拖拽的通知推送，强行进入则会出现窗口混乱的状况
#        if ( win32gui.ReleaseCapture() ):
#            win32gui.SendMessage( self.parent().winId(), win32con.WM_SYSCOMMAND, win32con.SC_MOVE+win32con.HTCAPTION, 0 )
#            
#        event.ignore()
    
QEDialogFlags_Frame = Qt.Widget if True else QEDialogFlags_Frame

QEDialogFlags_DEFAULT = Qt.WindowMinMaxButtonsHint|Qt.WindowCloseButtonHint|QEDialogFlags_Frame
QEDialogFlags_FIXSIZE = Qt.WindowCloseButtonHint|QEDialogFlags_Frame


class QEDialog(QDialog):
    
    def __init__( self, parent=None, flags=None, modal=None ):
        
        defaultflags = Qt.WindowCloseButtonHint
        defaultflags |= Qt.Widget if modal else Qt.WindowMinMaxButtonsHint
        flags = flags or defaultflags
        
        super().__init__( parent, flags )
        
        if parent :
            if modal is None :
                modal = True
            # 是否模式对话框 是否能切换到别的窗口
            self.setModal(modal)
        
        self.layout = QAlignLayout( self )
    
    def addWidget( self, widget, align ):
        self.layout.addWidget( widget, align )
        return
    
    def align( self, align ):
        
        app = QApplication.instance()
        sx, sy, sw, sh = app.desktop().availableGeometry(-1).getRect()
        bx, by, bw, bh = self.rect().getRect()
        
        #print( bx, by, bw, bh, self.width(), self.height() )
        
        self.setGeometry( align( self, (sx, sy, sw, sh), (bx, by, bw, bh) ) )
        
        return
    
    def moveScreenCenter( self ):
        self.align( QELa_Align( 0.5, 0.5, 0, 0 ) )
        return
        
    def resizeAvailable( self, borders=0 ):
        self.align( QELa_Align( 0.5, 0.5, 0, 0, 1, 1, -borders*2, -borders*2 ) )
        return
        
        
class QEApplication(QApplication):
    
    def __init__( self, argv=None ):
        
        argv = argv or sys.argv
        
        super().__init__( argv )
        
        self.exepth = sys.path[0] if not hasattr(sys, 'frozen') else \
                        os.path.dirname(os.path.realpath(sys.executable))
        
        return
    
    def applicationExePath( self ):
        return self.exepth


# http://blog.csdn.net/jwybobo2007/article/details/7465496
class QEWebView(QWebEngineView):
    
    def __init__( self, parent=None ):
        
        super(QEWebView, self).__init__( parent )

        self.page().settings().setAttribute( QWebEngineSettings.PluginsEnabled, True )
        self.page().settings().setAttribute( QWebEngineSettings.JavascriptCanAccessClipboard, True )
        self.page().settings().setAttribute( QWebEngineSettings.LocalContentCanAccessFileUrls, True )
        self.page().settings().setAttribute( QWebEngineSettings.LocalContentCanAccessRemoteUrls, True )
        

#http://www.cnblogs.com/vcommon/archive/2009/12/09/1620034.html#extending
#https://msdn.microsoft.com/en-us/library/bb688195(VS.85).aspx#extending
#http://blog.sina.com.cn/s/blog_5ca0198e0102v0h8.html

#http://www.lfd.uci.edu/~gohlke/pythonlibs/#pywin32

#http://jjgod.org/docs/slides/TextRenderingWithQt.pdf

if __name__ == '__main__' :
    
    from sip import SIP_VERSION_STR
    
    print( 'PyQT:', PYQT_VERSION_STR )
    print( ' SIP:', SIP_VERSION_STR )
    print( '  QT:', QT_VERSION_STR )
    
    app = QEApplication()
    
    win = QEDialog()
    win.show()
    
    win.resize(400,500)
    #win.resizeAvailable( 60 )
    win.moveScreenCenter()
    
    #win = QtWebEngine
    import PyQt5
    print( dir( PyQt5 ) )
    
    sys.exit(app.exec_())
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    