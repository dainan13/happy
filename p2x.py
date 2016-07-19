
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
    
    
if False:
    
    import collections
    
    def _namedtuple(typename, field_names, verbose=False, rename=False):
        """Returns a new subclass of tuple with named fields.

        >>> Point = namedtuple('Point', ['x', 'y'])
        >>> Point.__doc__                   # docstring for the new class
        'Point(x, y)'
        >>> p = Point(11, y=22)             # instantiate with positional args or keywords
        >>> p[0] + p[1]                     # indexable like a plain tuple
        33
        >>> x, y = p                        # unpack like a regular tuple
        >>> x, y
        (11, 22)
        >>> p.x + p.y                       # fields also accessable by name
        33
        >>> d = p._asdict()                 # convert to a dictionary
        >>> d['x']
        11
        >>> Point(**d)                      # convert from a dictionary
        Point(x=11, y=22)
        >>> p._replace(x=100)               # _replace() is like str.replace() but targets named fields
        Point(x=100, y=22)

        """

        # Validate the field names.  At the user's option, either generate an error
        # message or automatically replace the field name with a valid name.
        if isinstance(field_names, basestring):
            field_names = field_names.replace(',', ' ').split()
        field_names = map(str, field_names)
        typename = str(typename)
        if rename:
            seen = set()
            for index, name in enumerate(field_names):
                if (not all(c.isalnum() or c=='_' for c in name)
                    or _iskeyword(name)
                    or not name
                    or name[0].isdigit()
                    or name.startswith('_')
                    or name in seen):
                    field_names[index] = '_%d' % index
                seen.add(name)
        for name in [typename] + field_names:
            if type(name) != str:
                raise TypeError('Type names and field names must be strings')
            if not all(c.isalnum() or c=='_' for c in name):
                raise ValueError('Type names and field names can only contain '
                                 'alphanumeric characters and underscores: %r' % name)
            if _iskeyword(name):
                raise ValueError('Type names and field names cannot be a '
                                 'keyword: %r' % name)
            if name[0].isdigit():
                raise ValueError('Type names and field names cannot start with '
                                 'a number: %r' % name)
        seen = set()
        for name in field_names:
            if name.startswith('_') and not rename:
                raise ValueError('Field names cannot start with an underscore: '
                                 '%r' % name)
            if name in seen:
                raise ValueError('Encountered duplicate field name: %r' % name)
            seen.add(name)

        # Fill-in the class template
        class_definition = _class_template.format(
            typename = typename,
            field_names = tuple(field_names),
            num_fields = len(field_names),
            arg_list = repr(tuple(field_names)).replace("'", "")[1:-1],
            repr_fmt = ', '.join(_repr_template.format(name=name)
                                 for name in field_names),
            field_defs = '\n'.join(_field_template.format(index=index, name=name)
                                   for index, name in enumerate(field_names))
        )
        if verbose:
            print(class_definition)

        # Execute the template string in a temporary namespace and support
        # tracing utilities by setting a value for frame.f_globals['__name__']
        namespace = dict(_itemgetter=_itemgetter, __name__='namedtuple_%s' % typename,
                         OrderedDict=OrderedDict, _property=property, _tuple=tuple)
        try:
            exec(class_definition, namespace)
        except SyntaxError as e:
            raise SyntaxError(e.message + ':\n' + class_definition)
        result = namespace[typename]

        # For pickling to work, the __module__ variable needs to be set to the frame
        # where the named tuple is created.  Bypass this step in environments where
        # sys._getframe is not defined (Jython for example) or sys._getframe is not
        # defined for arguments greater than 0 (IronPython).
        try:
            result.__module__ = _sys._getframe(1).f_globals.get('__name__', '__main__')
        except (AttributeError, ValueError):
            pass

        return result
    
    collections.namedtuple = _namedtuple
    