
from eqt import *

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
        print( cls._instance, id(cls._instance) )
        return cls._instance
    
    def regist( self, sitename, cls ):
        print( '[QH] ewsgi site load:', sitename, id(self) )
        self.appCls[sitename] = cls
        return
    
    def newSiteObject( self, sitename ):
        print( '[QH] ewsgi site new:', sitename, id(self) )
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
        
        self.buffers = {}
        
        return super(AppUrlSchemeHandler, self).__init__( parent )
    
    def requestStarted( self, request ):
        
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
            siteobj, sitecls, _postfix = netloc
        else :
            siteobj = 'new'
            sitecls, _postfix = netloc
    
        if siteobj == 'new' :
            siteobj = QHSiteManager.instance().newSiteObject( sitecls )
            url = request.requestUrl()
            url.setHost('%s.%s.ewsgi' % (siteobj, sitecls) )
            request.redirect( url )
            return
        
        site = QHSiteManager.instance().getSiteObject( siteobj )
        
        self.buffer = QBuffer()
        request.destroyed.connect( self.buffer.deleteLater )
        
        resp = site.process( self.wsgiParams( request ) )
        print( resp.status )
        self.wsgiReponseProcess( request, resp )

        return
    
    def wsgiParams( self, request ):
        
        url = request.requestUrl()
        
        params = {}
        params['PATH_INFO'] = url.path()
        params['QUERY_STRING'] = url.query()
        params['REQUEST_METHOD'] = request.requestMethod()
        
        return params
    
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
            contentType.encode('utf-8')
        
        self.buffer.open(QIODevice.WriteOnly)
        self.buffer.write( resp.body )
        self.buffer.close()
        
        request.reply( contentType, self.buffer )
        
        return
    
    
# http://stackoverflow.com/questions/38071731/print-out-all-the-requested-urls-during-loading-a-web-page
# http://stackoverflow.com/questions/37658772/pyqt5-6-interceptrequest-doesnt-work
# http://stackoverflow.com/questions/33933958/qt-5-6-alpha-qtwebengine-how-work-with-qwebengineurlrequestjob
class QHDialog(QEDialog):
    
    APP_SCHEMA_HANDLER = b'app'
    app_url_scheme_handler = AppUrlSchemeHandler()
    
    def __init__( self, parent=None, flags=None, modal=None ):

        super().__init__( parent, flags, modal )
        
        profile = QWebEngineProfile.defaultProfile()
        installed = profile.urlSchemeHandler( self.APP_SCHEMA_HANDLER )
        if not installed :
            profile.installUrlSchemeHandler( self.APP_SCHEMA_HANDLER, self.app_url_scheme_handler )
        
        self.webview = QEWebView( self )
        self.webview.lower() # 在最底层显示
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
