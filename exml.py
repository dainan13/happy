# -*- coding: utf-8 -*-

import lxml.etree
import lxml.html
import weakref

import traceback



class RbElementMixin( object ):
        
    def __enter__( self ):
        self.tree()._push( self )
        return self
    
    def __exit__( self, exc_type, exc_value, tb  ):
        if exc_type :
            print('[Rb]', ''.join( traceback.format_tb(tb) ) )
            print('[Rb]', exc_type)
            print('[Rb]', exc_value)
        self.tree()._pop()
        return self
    
    def __lshift__( self, v ):
        
        children = self.getchildren()
        if len(children) == 0:
            self.text = v
        else :
            children[-1].tail = v
        
        return self
    
    def passdata( self, d ):
        self._passdata = d
        return self
    
    def elem( self, tag, nsmap=None ):
        
        if tag == 'comments' :
            child = self.tree().comment( '', self.tree() )
        else :
            child = self.tree().element( tag, self.tree(), nsmap=nsmap )
            
        self.append( child )
        
        return child
    
    def __getattr__( self, key ):
        
        #if key == 'comments_' :
        #    child = self.tree().comment( '', self.tree() )
        #    return
        
        if key.endswith('_') :
            return self.elem( key[:-1] )
            
        extm = self.tree().extmethod.get(key, None)
        if extm is not None :
            return lambda *args, **kwargs : extm( self, *args, **kwargs )
        
        raise AttributeError( "<RbElementMixin> object has no attribute '%s'" % key )
    
    def __call__( self, **attrib ):
        return self % attrib
    
    def __mod__( self, attrib ):
        
        attrib = [ self.parse_attrib(k, v) for k, v in attrib.items() ]
        attrib = [ (k,v) for k, v in attrib if v ]
        attrib = dict(attrib)
        
        self.attrib.update(attrib)
        
        return self

    def parse_attrib( self, k, v ):
        
        if type(v) == list :
            v = ' '.join(v)
        if type(v) == dict :
            v = ';'.join( ' '.join(v.items()) )
        
        k = self.parse_key(k)
        
        if k.startswith('_'):
            k = k.lstrip('_')
            if k in self.attrib :
                if v is None :
                    return (None, None)
                v = (self.attrib[k]+' '+v)
        elif v is None :
            try :
                del self.attrib[k]
            except :
                pass
            return (None,None)
            
        return ( k, v )
    
    def comment( self, s ):
        self.e.append( self.ec.Comment(s) )
        return self
        
    def get_passdata( self ):
        
        node = self
        
        while( node is not None ):
            pd = getattr( node, '_passdata', None )
            
            if pd is not None:
                return pd
            
            node = node.getparent()
            
        return
    
    def asroot( self ):
        
        if self.tree().root is self :
            self.tree()._push( self )
        else :
            raise Exception('Cant root')
        
        return
    
class CommentElement( lxml.etree.CommentBase, RbElementMixin ):
    
    def __init__( self, t, rb ):
        self.tree = weakref.ref(rb)
        super(CommentElement, self).__init__( t )
        return

class XMLElement( lxml.etree.ElementBase, RbElementMixin ):
    
    def __init__( self, tag, rb, nsmap=None ):
        self.tree = weakref.ref(rb)
        super(XMLElement, self).__init__( nsmap=nsmap )
        self.tag = tag
        return
    
    def parse_key( self, k ):
        return k
    
class HTMLCommentElement( lxml.html.HtmlComment, RbElementMixin ):
    
    def __init__( self, t, rb ):
        self.tree = weakref.ref(rb)
        super(HTMLCommentElement, self).__init__( t )
        return

class HTMLElement( lxml.html.HtmlElement, RbElementMixin ):
    
    def __init__( self, tag, rb, nsmap=None ):
        self.tree = weakref.ref(rb)
        super(HTMLElement, self).__init__()
        self.tag = tag
        return

    def parse_key( self, k ):
        return k.lower()
    
class Data( object ):
    pass


class NSElementPrefix( object ):
    
    def __init__( self, e, namespace ):
        
        self.e = e
        self.namespace = e.nsmap[namespace]
        
        return
    
    def __getattr__( self, key ):
        
        if key == '_' :
            return self.e
        
        if key.endswith('_') :
            return self.e.elem( '{%s}%s' % (self.namespace,key[:-1]) )
        
        raise AttributeError( "<RbXML> object has no attribute '%s'" % key )
    
class RbXML( object ):
    
    element = XMLElement
    comment = CommentElement
    format_method = 'xml'
    
    known_c14n_algorithms = {
        "http://www.w3.org/TR/2001/REC-xml-c14n-20010315",
        "http://www.w3.org/TR/2001/REC-xml-c14n-20010315#WithComments",
        "http://www.w3.org/2001/10/xml-exc-c14n#",
        "http://www.w3.org/2001/10/xml-exc-c14n#WithComments",
        "http://www.w3.org/2006/12/xml-c14n11",
        "http://www.w3.org/2006/12/xml-c14n11#WithComments"
    }
    
    c14n_algorithm = "http://www.w3.org/2006/12/xml-c14n11"
    inclusive_ns_prefixes = None
    
    def __init__( self, *exts ):
        
        self.root = None
        self.rootstack = []
        self.cur = None
        self.last = None
        
        self.stack = []

        self.exts = exts
        self.extmethod = [ ( m, getattr(e,m) ) for e in self.exts for m in dir(e) if not m.startswith('_') ]
        self.extmethod = dict( self.extmethod )
        
        self.js = []
        self.css = []
        
        for ext in exts :
            
            for ijs in getattr(ext,'_js', []) :
                if ijs not in self.js :
                    self.js.append(ijs)
            
            for ics in getattr(ext,'_css', []) :
                if ics not in self.css :
                    self.css.append(ics)
                
        return
    
    def tree( self ):
        return self
    
    def __lshift__( self, v ):
        
        children = self.cur.getchildren()
        if len(children) == 0:
            self.cur.text = v
        else :
            children[-1].tail = v
        
        return self
    
    def __call__( self, **attrib ):
        return self.cur(**attrib)
    
    def __mod__( self, attrib ):
        return self.cur % attrib
    
    def stackempty( self ):
        return len(self.stack) == 0
    
    def _push( self, node ):
        self.stack.append( ( self.cur, self.last ) )
        self.last = self.cur = node
        
        return
        
    def _pop( self ):
        
        self.cur, self.last = self.stack.pop( -1 )
        
        return
    
    def elem( self, tag, nsmap=None ):
        
        if self.cur is not None:
            n = self.cur.elem( tag, nsmap=nsmap )
            self.last = n
            return n
            
        if self.root is not None:
            self.rootstack.append( self.root )
            
        self.root = self.element( tag, self, nsmap=nsmap )
        self.last = self.root
        return self.root
    
    def __getattr__( self, key ):
        
        if key == '_' :
            return self.cur
        
        if key.endswith('_') :
            return self.elem( key[:-1] )
        
        extm = self.extmethod.get(key, None)
        if extm is not None:
            obj = self.cur if self.cur is not None else self
            return lambda *args, **kwargs : extm( obj, *args, **kwargs )
            
        raise AttributeError( "<RbXML> object has no attribute '%s'" % key )
        
    def append( self, another ):
        for r in another.rootstack:
            self.cur.append( r )
        return self.cur.append( another.root )
    
    def _bytes( self, root ):
        return lxml.etree.tostring( root, pretty_print=True, encoding='utf-8', method=self.format_method )
    
    def _string( self, root ):
        return lxml.etree.tounicode( root, pretty_print=True, method=self.format_method )
    
    def bytes( self ):
        
        if self.rootstack != [] :
            return b''.join( [ self._bytes(r) for r in self.rootstack+[self.root] ] )
            
        return self._bytes( self.root )
    
    def bytes_std( self ):
        return lxml.etree.tostring( self.root )
    
    def string( self ):
        
        if self.rootstack != [] :
            return ''.join( [ self._string(r) for r in self.rootstack+[self.root] ] )
            
        return self._string( self.root )
    
    def c14n( self ):
        
        exclusive, with_comments = False, False

        if self.c14n_algorithm.startswith("http://www.w3.org/2001/10/xml-exc-c14n#"):
            exclusive = True
        if self.c14n_algorithm.endswith("#WithComments"):
            with_comments = True

        c14n = lxml.etree.tostring( self.cur, method="c14n", exclusive=exclusive, with_comments=with_comments,
                              inclusive_ns_prefixes=self.inclusive_ns_prefixes)
        if exclusive is False:
            # TODO: there must be a nicer way to do this. See also:
            # http://www.w3.org/TR/xml-c14n, "namespace axis"
            # http://www.w3.org/TR/xml-c14n2/#sec-Namespace-Processing
            c14n = c14n.replace(b' xmlns=""', b'')
        
        return c14n
    
    def __getitem__( self, key ):
        
        return NSElementPrefix( self.cur, key )

class RbHTML(RbXML) :
    
    element = HTMLElement
    comment = HTMLCommentElement
    format_method = 'html'
    
    s_root = ''
    
    def res( self, res ):
        return self.s_root+res
    
    def loadres( self, *ress ):
        
        for res in ress :
            
            if res.endswith('.css'):
                self.link_( rel="stylesheet", type="text/css", href=self.s_root+res)
            elif res.endswith('.js'):
                self.script_( src=self.s_root+res )
                
        return
    
    def stdhead( self ):
        
        self.meta_( charset='utf-8' )
        
        for js in self.js :
            self.loadres( js )
        for css in self.css :
            self.loadres( css )
    
    def html( self ):
        self._push( self.html_ )
        return self
    
class JQuery( object ):
    
    _js = [
        '/js/jquery-2.2.3.min.js'
    ]
    
class Lo( object ):
    
    _css = [
        '/css/lo.css'
    ]
    
    def lo( self, top=None, right=None, bottom=None, left=None, max=None, min=None, **attrib ):
        
        cls = []
        
        if top != None :
            cls.extend( ['lo', 'lo_top', 'h%s'%top, ] )
        elif bottom != None :
            cls.extend( ['lo', 'lo_bottom', 'h%s'%bottom, ] )
        elif left != None :
            cls.extend( ['lo', 'lo_left', 'w%s'%left, ] )
        elif right != None :
            cls.extend( ['lo', 'lo_right', 'w%s'%right, ] )
        else :
            cls.extend( ['lo'] )
            
        cls = ' '.join(cls)
        
        return self.div_(**attrib)( _class=cls )
        
    def cnt( self, **attrib ):
        return self.div_(**attrib)( _class="cnt" )

    
class LoMobile( Lo ):
    
    _css = [
        '/css/lo_mobile.css'
    ]
    
class PureIo( object ):
    
    _css = [
        '/css/pure.css'
    ]
    
    def form( self, **attrib ):
        return html.div_(**attrib)( _class="pure-form" )
    
    def input( self, name, **attrib ):
        #html.input_( id="username", placeholder="Username", )
        return html.div_(**attrib)( type="text", _class="pure-input-1", placeholder="username" )
    
    def password( self, **attrib ):
        return 
    
    def btn():
        return

class Bootstrap( object ):
    
    _css = [
        '/css/bootstrap.css',
    ]
    
    _js = [
        '/js/jquery-2.1.3.min.js',
        '/js/bootstrap.js',
    ]
    
    def _form( self, tag="form", formtype=None, left=None, right=None, **attrib ):
        
        d = Data()
        d.form = formtype
        d.form_label = None
        d.form_div = None
        d.form_offset = None
        
        if formtype is None :
            
            formcls = None
            
        elif formtype == 'inline' :
            
            formcls = 'form-inline'
            
        elif formtype == 'nolabel-inline':
            
            formcls = 'form-inline'
            d.form_label = 'sr-only'
            
        elif formtype == 'horizontal':
            
            left = 2 if left is None else left
            right = 10 if right is None else right
            
            formcls = 'form-horizontal'
            
            d.form_offset = 'col-sm-offset-%s' % left
            d.form_label = 'col-sm-%s' % left
            d.form_div = 'col-sm-%s' % right
        
        return self.elem(tag)(**attrib)( _class=formcls ).passdata(d)
    
    def form( self, *args, **kwargs ):
        return Bootstrap._form( self, "form", *args, **kwargs )
        
    def formdiv( self, *args, **kwargs ):
        return Bootstrap._form( self, "div", *args, **kwargs )
        
    def input( self, label, name=None, id=None, eg=None, opts=None, opt_column=None, opt_minwidth=160, opt_style=None, val=None, **attrib ):
        
        id = id or name or label
        placeholder = eg or label
        
        d = self.get_passdata()
        h = self.tree()
        
        if d == None :
            return h.input_( type="text", _class="form-control", id=id, placeholder=placeholder, value=val )
        
        with h.div_(**attrib)( _class="form-group" ):
            h.label_( For=id, Class="control-label" )(_class=d.form_label) << label
            with h.div_( _class=d.form_div ):
                
                if opts :
                    with h.div_( _class="input-group" ):
                        r = h.input_( type="text", _class="form-control", name=name, id=id, placeholder=eg, value=val )
                        with h.div_( _class="input-group-btn" ):
                            with h.button_( type="button", Class="btn btn-default dropdown-toggle", style="height:34px;" ):
                                h % {'data-toggle':"dropdown", 'aria-haspopup':"true", 'aria-expanded':"false"}
                                h.span_( Class="caret" )
                            with h.ul_( _class="dropdown-menu dropdown-menu-right" ):
                                if opt_column :
                                    h( style='-webkit-column-count:%s; min-width:%spx' % (opt_column,opt_column*opt_minwidth) )
                                for opt in opts :
                                    
                                    if type(opt) == tuple and len(opt) == 2 :
                                        optn, optv = opt
                                    else :
                                        optn, optv = opt, opt
                                    
                                    with h.li_.a_( href="#", onclick="$(this).parent().parent().parent().prev().val('%s').trigger('change')" % (optn or '') ):
                                        h << ( optv or '(空白)' )
                                        h( _style=opt_style )
                                        if optv == val :
                                            h(_style="font-weight: 900")
                else :
                    r = h.input_( type="text", _class="form-control", name=name, id=id, placeholder=eg, value=val, defualtvalue=val )
        
        return r
        
    def checkbox( self, label, name=None, id=None, **attrib ):
        
        id = id or name or label
        
        d = self.get_passdata()
        h = self.tree()
        
        with h.div_(**attrib)( _class="form-group" ):
            with h.div_( _class=d.form_offset )( _class=d.form_div ):
                with h.div_ ( Class="checkbox" ):
                    with h.label_:
                        r = h.input_( type="checkbox", name=name, id=id )
                        h << label
        
        return r
        
    def submit( self, label, name=None, **attrib ):
        
        d = self.get_passdata()
        h = self.tree()
        
        if d.form == 'horizontal':
            
            with h.div_(**attrib)( _class="form-group" ):
                with h.div_( _class=d.form_offset )( _class=d.form_div ):
                    r = h.button_( type="submit", _class="btn btn-default" ) << label
                    
            return r
        
        return self.button_(**attrib)( type="submit", _class="btn btn-default" ) << label
        
    def select( self, label, name=None, id=None, options=[], **attrib ):
        
        id = id or name or label
        
        d = self.get_passdata()
        h = self.tree()
        
        if d is None :
            r = h.select_(**attrib)( _class="form-control", name=name, id=id )
            with r :
                for val, opt in options :
                    h.option_( value=str(val) ) << opt
            return r
    
        with h.div_(**attrib)( _class="form-group" ):
            h.label_( For=id, Class="control-label" )(_class=d.form_label) << label
            with h.elem( 'span' if d.form == 'inline' else 'div' )( _class=d.form_div ):
                r = h.select_( _class="form-control", name=name, id=id )
                with r :
                    for val in options :
                        
                        if type(val) == tuple and len(val) == 2:
                            val, opt = val
                        else :
                            opt = val
                        
                        h.option_( value=str(val) ) << opt
                        
        return r
        
    def btn( self, label, type=None, **attrib ):
        
        if type not in {'default', 'primary', 'success', 'info', 'warning', 'danger', 'link'}:
            type = 'default'
        
        btntype = 'btn-%s' % type
        
        d = self.get_passdata()
        h = self.tree()
        
        if d and d.form == 'horizontal':
            
            with h.div_(**attrib)( _class="form-group" ):
                with h.div_( _class=d.form_offset )( _class=d.form_div ):
                    r = h.button_( type="button", _class="btn" )(_class=btntype) << label
                    
            return r
        
        return self.button_(**attrib)( type="button", _class="btn" )(_class=btntype) << label
        
    def abtn( self, label, type=None, **attrib ):
        
        if type not in {'default', 'primary', 'success', 'info', 'warning', 'danger', 'link'}:
            type = 'default'
        
        btntype = 'btn-%s' % type
        
        return self.a_(**attrib)( role="button", _class="btn" )(_class=btntype) << label
        


class Chosen( object ):
    
    _css = [
        '/css/chosen.css',
    ]
    
    _js = [
        #'/js/jquery-2.1.3.min.js',
        #'/js/bootstrap.js',
        '/js/chosen.jquery.js',
    ]
    

def xml( *args ):
    return RbXML( *args )
    
def html( *args ):
    return RbHTML( *args ) 
    
def HTML( *args ):
    return RbHTML( *args ).html()
    
def HTML5( *args ):
    h = RbHTML( *args )
    h.comment('DOCTYPE html')
    return h.html()



if __name__ == '__main__' :
        
    def test1():
        h = HTML(Bootstrap)
        
        with h.head_():
            h.stdhead()
        
        with h.body_:
            
            #h.div_ << 'abc'
            #with h.div_( Class="lo" ).div_( Class="cnt" ) :
            #    h._ << 'aaa'
            #    h.br_
            #    h._ << '&bbb'
            #    h.span_ << '&ccc'
            #    h.last( Class='c' )
            #    h._ << '&ddd'
            #
            #    for i in range(1):
            #        with h.a_( href="javascript:app.onsomething(%s)" % i ):
            #            with h.div_( Class="li", id='cinema_%s' % i ):
            #                with h.div_ :
            #                    h << 'cinema %s' % i
            #                
            with h.form():
                h.input('username')
                
        h.bytes()
        print( h.string() )
        #print( h.bytes() )
        
        
        
        
        #print( HTMLElement('html', h) )
    
    def test2() :
        h = html(Bootstrap)
        
        h.div_(Class="a")
        h.div_(Class="b")
        
        print( h.string() )
        
    test2()
    
    
    
    
    
    
    