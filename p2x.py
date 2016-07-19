
import sys

if sys.version_info[0] < 3 :
    
    class Foo(object):
        pass
        
    import urllib
    import urllib2
    sys.modules['urllib.parse'] = Foo()
    sys.modules['urllib.request'] = Foo()
    #import urllib.parse
    urllib.parse = Foo()
    urllib.parse.quote_plus = urllib.quote_plus
    urllib.parse.unquote_plus = urllib.unquote_plus
    urllib.request = Foo()
    urllib.request.Request = urllib2.Request
    urllib.request.urlopen = urllib2.urlopen
    
    import Cookie
    sys.modules['http'] = Foo()
    sys.modules['http.cookies'] = Foo()
    import http
    http.cookies = Cookie
    
    #sys.modules['collections'] = Foo()
    
    
    
    