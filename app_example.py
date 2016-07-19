
import hqt
import exml

class SiteExample( hqt.QHSite ):
    
    def __init__( self ):
        super().__init__()
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
                    h.div_( Class="" ).h3_( style="padding: 10px;") << '欢迎使用HAPPY库'
                    h.div_ << 'HAPPY 是一个关于使用Python编写可通用于uwsgi和基于Qt的WebEngine的HTML页面编写库。'
                
        return b"<!DOCTYPE html>\n" + h.bytes()
        
