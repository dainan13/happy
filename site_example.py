# -*- coding:utf-8 -*-

import sys

import ewsgi
import exml

class SiteExample( ewsgi.WsgiServer ):
    
    def __init__( self ):
        
        super(SiteExample, self).__init__()
        
        return
        
    def url__( self ):
        
        h = exml.HTML()
        
        with h.head_ :
            
            h.title_ << u'欢迎使用Happy库'
            
            h.meta_( **{"http-equiv":"Content-Type", "content":"text/html; charset=utf-8"} )
            h.meta_( name="viewport", content="width=device-width, initial-scale=1.0, minimum-scale=1.0, maximum-scale=1.0, user-scalable=no" )
            
            h.loadres( '/css/ewbase.css' )
            h.loadres( '/css/lo.css' )
            
            h.style_ << """
.header { background-color: #eee; border-bottom: 1px solid #aaa; }
.footer { background-color: #eee; border-top: 1px solid #aaa; }
.row { max-width: 500px; margin: 0 auto; }
            """
            
        with h.body_ :
            
            with h.div_( Class='lo lo_top h50' ).div_( Class="cnt header" ):
                
                with h.div_( Class="row" ):
                    h.a_( href= "" ) << 'HAPPY'
            
            with h.div_( Class='lo lo_bottom h50' ).div_( Class="cnt footer" ):
                
                with h.div_( Class="row" ):
                    h.div_() << '3-BSD License'
            
            with h.div_( Class='lo' ).div_( Class="cnt" ):
                
                with h.div_( Class="row" ):
                    h.div_( Class="" ).h3_( style="padding: 10px;") << u'欢迎使用HAPPY库'
                    h.div_ << u'HAPPY 是一个关于使用Python编写可通用于uwsgi和基于Qt的WebEngine的HTML页面编写库。'
        
        if sys.version_info[0] < 3 :
            return "<!DOCTYPE html>\n" + h.bytes()
        
        return b"<!DOCTYPE html>\n" + h.bytes()
        
    def url__test403( self ):
        return 403, "<head><title>Page Forbidden</title></head><body>Opps, You're lost. Access to this page is forbidden. Back to Home</body>"
        
    def url__test301( self ):
        return 301, [("Location","/")], '<head><title>Document Moved</title></head><body><h1>Object Moved</h1></body>'
    
    def url__test302( self ):
        return ewsgi.HttpRedirect( "/" )
    
    def url__test500( self ):
        return self.HttpInternalServerError()
    
    
    
    
if __name__.startswith('uwsgi_file_'):
    
    application = SiteExample()

elif __name__ == '__main__' :
    
    application = SiteExample()
    
    from wsgiref.simple_server import make_server
    server = make_server( "127.0.0.1",18080, application)
    server.serve_forever()
    