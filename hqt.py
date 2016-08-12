
from eqt import *

from PyQt5.QtWebChannel import *

import json

import ewsgi
import urllib.parse


class QHSiteManager( object ):
    
    _instance = None
    
    def __init__( self ):
        
        if self._instance != None :
            raise Exception('QHSiteManager is Singleton Class')
            
        self.appCls = {}
        self.appObjects = {}
        self.appWebviews = {}
        
        return
    
    @classmethod
    def instance( cls ):
        return cls._instance
    
    def regist( self, sitename, cls ):
        print( '[QH] ewsgi site load:', sitename )
        self.appCls[sitename] = cls
        return
    
    def newSiteObject( self, sitename ):
        print( '[QH] ewsgi site new:', sitename )
        sitecls = self.appCls[sitename]
        siteobj = sitecls()
        siteid = id(siteobj)
        self.appObjects[ siteid ] = siteobj
        return siteid
    
    def getSiteObject( self, siteobj_id ):
        return self.appObjects[ int(siteobj_id) ]
    
QHSiteManager._instance = QHSiteManager()

class QHSiteMeta( type ):
    
    def __new__( cls, name, bases, dct ):
        return type.__new__(cls, name, bases, dct) 
        
    def __init__( cls, name, bases, dct ):
        
        lowername = name.lower()
        sitename = None
        
        if getattr( cls, 'sitename', '' ) != '' :
            sitename = cls.sitename
        elif lowername.startswith('site'):
            sitename = lowername[4:]
            
        if sitename != None :
            QHSiteManager.instance().regist( sitename, cls )
            cls.sitename = sitename
            cls.name = getattr( cls, 'name', sitename )
            
        super().__init__( name, bases, dct )
        
class QHSite( ewsgi.WsgiServer, metaclass=QHSiteMeta ):
    
    visible = True
    singleton = False
    threadlocal = threading.local()
    
    def exit( self ):
        #http://stackoverflow.com/questions/11772624/pyqt-dialog-how-to-make-it-quit-after-pressing-a-button
        QCoreApplication.instance().quit()
        
class AppUrlSchemeHandler(QWebEngineUrlSchemeHandler):
    
    def __init__( self, parent=None ):
        
        return super(AppUrlSchemeHandler, self).__init__( parent )
    
    def requestStarted( self, request ):
        
        print( '[QH] >', request.requestUrl().url() )
        
        netloc = request.requestUrl().host().lower().split('.')
        
# Constant	Value	Description
# NoError	0	The request was successful.
# UrlNotFound	1	The requested URL was not found.
# UrlInvalid	2	The requested URL is invalid.
# RequestAborted	3	The request was canceled.
# RequestDenied	4	The request was denied.
# RequestFailed	5	The request failed.
        
        if netloc[-1] != 'ewsgi' :
            request.fail( request.UrlInvalid )
            return
        
        if len(netloc) not in (2,3)  :
            request.fail( request.UrlInvalid )
            return
            
        if len(netloc) == 3 :
            siteid, sitecls, _postfix = netloc
        else :
            siteid = 'new'
            sitecls, _postfix = netloc
    
        if siteid == 'new' :
            siteid = QHSiteManager.instance().newSiteObject( sitecls )
            url = request.requestUrl()
            url.setHost('%s.%s.ewsgi' % (siteid, sitecls) )
            self.parent().setUrl( url )
            #request.redirect( url ) #redirect会使page的URL不发生变更。
            return
        
        siteobj = QHSiteManager.instance().getSiteObject( siteid )
        
        self.buffer = QBuffer()
        request.destroyed.connect( self.buffer.deleteLater )
        
        if request.requestUrl().path() == '/_js_return' :
            
            r = self.parent().result
            
            contentType = b"json/application"
            
            self.buffer.open(QIODevice.WriteOnly)
            self.buffer.write( r.encode('utf-8') )
            self.buffer.close()
        
            request.reply( contentType, self.buffer )
            
        else :
            resp = siteobj.process( self.wsgiParams( request ) )
            print( '[QH] <', resp.status )
            self.wsgiReponseProcess( request, resp )

        return
    
    def wsgiParams( self, request ):
        
        url = request.requestUrl()
        
        params = {}
        params['PATH_INFO'] = url.path()
        params['QUERY_STRING'] = url.query()
        params['REQUEST_METHOD'] = request.requestMethod()
        
        params['wsgi.file_wrapper'] = self.wsgiFileWrapper
        
        return params
    
    def wsgiFileWrapper( self, fp ):
        
        # QFile当前有些问题
        #qfile = QFile()
        #qfile.open( fp.fileno(), QIODevice.ReadOnly )
        #return qfile
        
        return fp.read()
        
    def wsgiReponseProcess( self, request, resp ):
        
        if resp.status >= 500 :
            request.fail( request.RequestFailed )
            return
        
        if resp.status >= 400 :
            if resp.status == 403 :
                request.fail( request.RequestDenied )
            else :
                request.fail( request.UrlNotFound )
            return
            
        if resp.status >= 300 :
            # redirect
            return
        
        if resp.status < 200 :
            # 这种情况UrlSchemeHandler处理不了
            request.fail( request.RequestAborted )
            return
        
        contentType = [ hv for h, hv in resp.headers if h == 'Content-Type' ]
        contentType = b"text/html" if len(contentType) == 0 else contentType[0]
        
        if type(contentType) == str :
            contentType = contentType.encode('utf-8')
        
        if type( resp.body ) == bytes :
            
            self.buffer.open(QIODevice.WriteOnly)
            self.buffer.write( resp.body )
            self.buffer.close()
        
            request.reply( contentType, self.buffer )
        
        else :
            
            self.localfile = resp.body
            
            request.reply( contentType, self.localfile )
        
        return
    
# http://python.6.x6.nabble.com/Qt-WebChannel-JavaScript-API-td5170173.html

class QHWebEnginePage(QWebEnginePage): 
    
    APP_SCHEMA_HANDLER = b'app'
    
    def loadQWebChannelJS():
        
        qwebchannel_js = QFile(':/qtwebchannel/qwebchannel.js')
        
        if not qwebchannel_js.open(QIODevice.ReadOnly):
            raise SystemExit( 
                'Failed to load qwebchannel.js with error: %s' % 
                qwebchannel_js.errorString())
        
        return bytes(qwebchannel_js.readAll()).decode('utf-8')
    
    QWEBCHANNEL_JS = loadQWebChannelJS()
    loadQWebChannelJS = staticmethod(loadQWebChannelJS)
    
    INIT_JS = '''
new QWebChannel(qt.webChannelTransport, function(channel) {

    channel.objects.bridge.returnValue.connect(function(message) {
        alert("Got signal: " + message);
    });
    
    channel.objects.bridge.sitemethod("test", "[1,2]", function(ret) {
        alert("Got return value: " + ret);
    });
    
    var request = new XMLHttpRequest();
    request.open('GET', '/_js_return', false); 
    request.send(null);
    alert(request.responseText);
    
    channel.objects.bridge.print('Hello world!');
    
    
    window.site = channel.objects.bridge;
    
    alert('HAHA');
});
'''

    def __init__( self ):
        
        super().__init__()
        
        self.app_url_scheme_handler = AppUrlSchemeHandler( self )
        
        self.profile().installUrlSchemeHandler( self.APP_SCHEMA_HANDLER, self.app_url_scheme_handler )
        self.profile().scripts().insert( self.make_script() ) 
        
        self.webchannel = QWebChannel(self) 
        self.setWebChannel(self.webchannel)
        
        self.webchannel.registerObject( 'bridge', self )
        
        self.result = None
        
        return
    
    def make_script( self ):
        script = QWebEngineScript()
        script.setSourceCode(self.QWEBCHANNEL_JS + self.INIT_JS) 
        script.setName('HQChannel') 
        script.setWorldId(QWebEngineScript.MainWorld) 
        script.setInjectionPoint(QWebEngineScript.DocumentReady) 
        script.setRunsOnSubFrames(True) 
        return script 
        
    def javaScriptConsoleMessage(self, level, msg, linenumber, source_id):
        
        try:
            print('%s:%s: %s' % (source_id, linenumber, msg)) 
        except OSError:
            pass

    @pyqtSlot(str) 
    def print(self, text):
        print( 'From JS:', text )
    
    @pyqtSlot(str, str, result=str)
    def sitemethod(self, methodname, args):
        siteid = self.requestedUrl().host().split('.')[0]
        siteobj = QHSiteManager.instance().getSiteObject( siteid )
        method = getattr( siteobj, 'js_'+methodname )
        import time
        for i in range(2):
            time.sleep(1)
            print('.')
        r = json.dumps( method( *json.loads(args) ) )
        self.runJavaScript('alert("aaa")')
        #self.returnValue.emit( r )
        self.result = r
        return r
    
    returnValue = pyqtSignal(str)

#http://blog.csdn.net/liuyez123/article/details/50532091
#http://download.csdn.net/download/liuyez123/9402132
#https://www.kdab.com/qt-webchannel-bridging-gap-cqml-web/
# http://stackoverflow.com/questions/33704128/undefined-properties-and-return-types-when-using-qwebchannel
# http://stackoverflow.com/questions/38071731/print-out-all-the-requested-urls-during-loading-a-web-page
# http://stackoverflow.com/questions/37658772/pyqt5-6-interceptrequest-doesnt-work
# http://stackoverflow.com/questions/33933958/qt-5-6-alpha-qtwebengine-how-work-with-qwebengineurlrequestjob
class QHDialog(QEDialog):
    
    # APP_SCHEMA_HANDLER = b'app'
    # app_url_scheme_handler = AppUrlSchemeHandler()
    
    def __init__( self, parent=None, flags=None, modal=None ):

        super().__init__( parent, flags, modal )
        
        # profile = QWebEngineProfile.defaultProfile()
        # installed = profile.urlSchemeHandler( self.APP_SCHEMA_HANDLER )
        # if not installed :
        #     profile.installUrlSchemeHandler( self.APP_SCHEMA_HANDLER, self.app_url_scheme_handler )
        
        self.page = QHWebEnginePage()
        
        self.webview = QEWebView( self )
        self.webview.lower() # 在最底层显示
        
        self.webview.setPage( self.page )
        
        self.addWidget( self.webview, QELa_Align(0, 0, 0, 0, 1, 1, 0, 0) )
        
    @pyqtSlot( str )
    def openUrl( self, url, **kwargs ):

        self.webview.setUrl(QUrl(url))

        return

if __name__ == '__main__' :
    
    #--remote-debugging-port=8888
    
    app = QEApplication()
    
    win = QHDialog()
    win.show()

    win.resize(400,500)
    win.moveScreenCenter()
    
    win.openUrl(QUrl("http://www.baidu.com/"))
    #win.openUrl(QUrl("app://example.ewsgi/"))
    
    sys.exit( app.exec_() )
