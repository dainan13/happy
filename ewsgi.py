# -*- coding:utf-8 -*-

import p2x

import urllib

import urllib.parse
import http.cookies
import os
import os.path
import sys
import threading
import json

from collections import namedtuple
from wsgiref.util import FileWrapper

import mimetypes
import cgi

httpcodes = [
("CONTINUE",100),
("SWITCHING_PROTOCOLS",101),
("PROCESSING",102),
("OK",200),
("CREATED",201),
("ACCEPTED",202),
("NON_AUTHORITATIVE_INFORMATION",203),
("NO_CONTENT",204),
("RESET_CONTENT",205),
("PARTIAL_CONTENT",206),
("MULTI_STATUS",207),
("IM_USED",226),
("MULTIPLE_CHOICES",300),
("MOVED_PERMANENTLY",301),
("FOUND",302),
("SEE_OTHER",303),
("NOT_MODIFIED",304),
("USE_PROXY",305),
("TEMPORARY_REDIRECT",307),
("BAD_REQUEST",400),
("UNAUTHORIZED",401),
("PAYMENT_REQUIRED",402),
("FORBIDDEN",403),
("NOT_FOUND",404),
("METHOD_NOT_ALLOWED",405),
("NOT_ACCEPTABLE",406),
("PROXY_AUTHENTICATION_REQUIRED",407),
("REQUEST_TIMEOUT",408),
("CONFLICT",409),
("GONE",410),
("LENGTH_REQUIRED",411),
("PRECONDITION_FAILED",412),
("REQUEST_ENTITY_TOO_LARGE",413),
("REQUEST_URI_TOO_LONG",414),
("UNSUPPORTED_MEDIA_TYPE",415),
("REQUESTED_RANGE_NOT_SATISFIABLE",416),
("EXPECTATION_FAILED",417),
("UNPROCESSABLE_ENTITY",422),
("LOCKED",423),
("FAILED_DEPENDENCY",424),
("UPGRADE_REQUIRED",426),
("PRECONDITION_REQUIRED",428),
("TOO_MANY_REQUESTS",429),
("REQUEST_HEADER_FIELDS_TOO_LARGE",431),
("INTERNAL_SERVER_ERROR",500),
("NOT_IMPLEMENTED",501),
("BAD_GATEWAY",502),
("SERVICE_UNAVAILABLE",503),
("GATEWAY_TIMEOUT",504),
("HTTP_VERSION_NOT_SUPPORTED",505),
("INSUFFICIENT_STORAGE",507),
("NOT_EXTENDED",510),
("NETWORK_AUTHENTICATION_REQUIRED",511),
]

httpcodes_s2i = dict(httpcodes)
httpcodes_i2s = dict([ (i, s) for s, i in httpcodes ])

class HttpResponse(object):
    
    def __init__( self, status, reason, headers, body ):
        
        self.exc_info = None
        
        self.status = status if status else httpcodes_s2i[reason]
        self.reason = reason if reason else httpcodes_i2s[status]
        self.headers = list(headers.items()) if type(headers) == dict else headers
        
        if type(body) == str and sys.version_info[0] >= 3:
            body = body.encode('utf-8')
            
        if body is None :
            body = b''
            
        self.body = body
        
        return
        
    def headstruct( self ):
        return ( '%s %s' % (self.status, self.reason), self.headers, self.exc_info )


class HttpOK(HttpResponse):
    
    def __init__( self, headers=[], body='' ):
        super(HttpOK, self).__init__( 200, None, headers, body )
        return

class HttpBadRequest(HttpResponse):
    
    def __init__( self, headers=[], body='' ):
        super(HttpBadRequest, self).__init__( 400, None, headers, body )
        return

class HttpNotFound(HttpResponse):
    
    def __init__( self, headers=[], body='' ):
        super(HttpNotFound, self).__init__( 404, None, headers, body )
        return

class HttpForbidden(HttpResponse):
    
    def __init__( self, headers=[], body='' ):
        super(HttpForbidden, self).__init__( 403, None, headers, body )
        return

class HttpRedirect(HttpResponse):
    
    def __init__( self, redirect_url ):
        self.redirect_url = redirect_url
        headers = {'Location':redirect_url}
        super(HttpRedirect, self).__init__( 302, None, headers, '' )
        return

class HttpXRedirect(HttpResponse):
    
    def __init__( self, redirect_url ):
        self.redirect_url = redirect_url
        headers = {'X-Accel-Redirect':redirect_url}
        super(HttpXRedirect, self).__init__( 301, None, headers, '' )
        return

class HttpInternalServerError(HttpResponse):
    
    def __init__( self, exc_info=None ):
        self.exc_info = sys.exc_info() if exc_info == None else exc_info
        super(HttpInternalServerError, self).__init__( 500, None, [], '' )
        return


class WsgiStaticServer( object ):
    
    def __init__( self, resp ):
        self.resp = resp
        return
        
    def __call__( self, environ, start_response ):
        start_response( *self.resp.headstruct() )
        return self.resp.body

import yaml

try :
    import uwsgi
except :
    class uwsgi(object):
        opt = {}
    
def readconfig( filename=None ):
    
    filename = (uwsgi.opt.get('ewsgi', b"wsgi").decode('utf-8')+'.yaml') if filename is None else filename
    
    if not os.path.exists( filename ) :
        print('[!] wsgi no load , %s file not found ---------------------------' % filename )
        return {}
    #else :
    #    print('[ ] wsgi %s file loaded.' % filename)
    
    with open( filename, 'r') as fp :
        conf = yaml.load(fp)
        
    if 'handlers' in conf :
        
        conf['handlers']  = [ h for h in conf['handlers'] if type( h.get('url',None) ) == str and type( h.get('static_dir',None) ) == str ]
        
        for h in conf['handlers'] :
            if not h['url'].endswith('/') :
                h['url'] = h['url']+'/'
        
    return conf

def readvars( conf ):
    link_ks, link_vs = tuple( zip(* conf.get('var', {}).items() ) ) or ( [], [] )
    #print( link_ks, link_vs )
    return namedtuple('EWSGIVARS', link_ks)(*link_vs)

class WsgiServer(object):
    
    HttpResponse = HttpResponse
    HttpOK = HttpOK
    HttpBadRequest = HttpBadRequest
    HttpNotFound = HttpNotFound
    HttpRedirect = HttpRedirect
    HttpInternalServerError = HttpInternalServerError
    HttpForbidden = HttpForbidden
    HttpXRedirect = HttpXRedirect
    
    wsgiconf = readconfig()
    var = readvars(wsgiconf)

    def __init__( self ):
        
        self.more_entry = []
        self._local = threading.local()
        
        if 'exml' in sys.modules and 'var' in self.wsgiconf and 'static_url' in self.wsgiconf['var'] :
            print('hook exml static root')
            sys.modules['exml'].RbHTML.s_root = self.wsgiconf['var']['static_url']
        
        self.true_make_session = WsgiServer.make_session
        if sys.version_info[0] < 3 :
            self.true_make_session = self.true_make_session.__func__
        
        return
        
    def __call__( self, environ, start_response ):
        
        resp = self.process(environ)
        start_response( *resp.headstruct() )
        
        if type(resp.body) == bytes :
            return [resp.body]
        
        return resp.body
    
    def process( self, environ ):
        
        w, args = self.http_entry( environ )
        resp = w(*args)
        
        return resp
    
    @property
    def env(self):
        return self._local.env
    
    @env.setter
    def env( self, value ):
        self._local.env = value
    
    @property
    def session(self):
        return self._local.session
    
    @session.setter
    def session( self, value ):
        self._local.env = value
    
    def http_entry( self, environ ):
        
        self._local.env = environ
        self._local.session = None
        
        path = environ['PATH_INFO']
        w = getattr( self, 'url'+path.replace('/','__'), None )
        
        if w :
            
            qs = environ['QUERY_STRING'].split('&')
            qs = [ x.split('=',1) for x in qs if x ]
            qs = [ (k, urllib.parse.unquote_plus(v)) for k, v in qs if k!='_' ]
            qs = dict(qs)
            
            if environ['REQUEST_METHOD'] == 'POST' :
                
                ctype, pdict = cgi.parse_header( environ.get('HTTP_CONTENT_TYPE') )
                
                if ctype.startswith('application/x-www-form-urlencoded') :
                
                    pd = environ['wsgi.input'].read().decode('utf-8')
                    pd = pd.split('&')
                    pd = [ x.split('=',1) for x in pd if x ]
                    pd = [ (k, urllib.parse.unquote_plus(v)) for k, v in pd ]
                    pd = dict(pd)
                
                    qs.update(pd)
                
                elif ctype.startswith('multipart/form-data') :
                    
                    if type(pdict['boundary']) == str :
                        pdict['boundary'] = pdict['boundary'].encode('ascii')
                    
                    pd = cgi.parse_multipart(environ['wsgi.input'], pdict)
                    qs.update(pd)
                    
                elif ctype.startswith('application/json') :
                    
                    pd = environ['wsgi.input'].read().decode('utf-8')
                    
                    qs.update( json.loads( pd ) )
                    
            return ( self.http_cgi, (w, qs) )
            
        else :
            
            for handler in self.wsgiconf.get('handlers',[]):
                
                if path.startswith( handler['url'] ):
                    
                    filepath = os.path.join( handler['static_dir'], path[len(handler['url']):] )
                    
                    if os.path.exists( filepath ) and os.path.isfile( filepath ):
                        
                        return ( self.http_static, (environ.get('wsgi.file_wrapper',FileWrapper), filepath ) )
                    
                    break
        
        return ( self.http_notfound, () )
    
    def make_session( self, work, args, cookie ):
        return
    
    def http_cgi( self, work, args ):
        
        try :
            
            resp = None
            
            if self.make_session.__func__ != self.true_make_session :
                
                if self.environ.get('HTTP_COOKIE') :
                    
                    c = http.cookies.SimpleCookie()
                    c.load( self.environ['HTTP_COOKIE'] )
                    #c = [ (ci.key, urllib.parse.unquote_plus(ci.value)) for ci in c ]
                    c = [ (ci.key.lower(), ci.value) for ci in c.values() ]
                    c = dict(c)
                    
                else :
                    
                    c = {}

                resp = self.make_session( work, args, cookie )
            
            if resp is None :
                resp = work(**args)

        except :
            import traceback
            traceback.print_exc()
            return HttpInternalServerError( sys.exc_info() )
        
        if type(resp) == tuple :
            
            if len( resp ) == 2 :
                resp = HttpResponse( resp[0], None, [], resp[1] )
            elif len( resp ) == 3 :
                resp = HttpResponse( resp[0], None, resp[1], resp[2] )
        
        if not isinstance( resp, HttpResponse ):
            resp = HttpOK( [], resp )
            
        return resp
        
    def http_static( self, file_wrapper, filepath ):
        
        fp = open( filepath, 'rb' )
        
        mtype = None
        headers = []
        
        try :
            mtype = mimetypes.guess_type( filepath )[0]
        except :
            pass
        
        if mtype :
            headers.append( ('Content-Type', mtype) )
        
        return HttpOK( headers, file_wrapper( fp ) )
        
    def http_notfound( self ):
        return HttpNotFound()
    
    
    