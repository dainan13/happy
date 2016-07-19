
import os
import os.path
import yaml
import time
import itertools

from collections import defaultdict

import pymysql
import pymysql.cursors

from collections import OrderedDict
pymysql.cursors.DictCursorMixin.dict_type = OrderedDict

class PerspectiveMatrix( object ):
    
    def __init__( self, fields, rows ):
        
        st = time.time()
        self.fields = [ f.lower() for f in fields ]
        
        self.pmatrix = defaultdict(dict)
        self.kmatrix = defaultdict(set)
        
        self.parser_fields()
        self.usedtime = time.time() - st
        self.addrows( rows )
        
    def same_fields( self, fields ):
        return bool( self.fields == [ f.lower() for f in fields ] )
    
    def parser_fields( self ):
        
        self.kpos = []
        self.vpos = []
        
        self.kcols = {}
        self.vcols = {}
        
        for i, f in enumerate(self.fields):
            
            vfunc = self.is_valuecol( f.lower() )
            
            if vfunc is None :
                self.kcols[f] = i
                self.kpos.append(i)
            else :
                self.vcols[f] = vfunc
                self.vpos.append( ( i, f, vfunc ) )
        
        return
        
    def addrow( self, row ):
        
        kc = [ tuple(sorted(comb)) for cr in range(len(self.kpos)+1) for comb in itertools.combinations(self.kpos, cr) ]
        
        for comb in kc :
            k = tuple( [ (ki, row[ki]) for ki in comb ] )
            #print(k)
            self.makeup( self.pmatrix[k], row )

        for ki in self.kpos :
            self.kmatrix[self.fields[ki]].add(row[ki])
        
        return
    
    def addrows( self, rows ):
        
        st = time.time()
        
        for row in rows :
            self.addrow( row )
        
        self.usedtime += (time.time()-st)
        
        return
        
    def makeup( self, a, b ):
        
        if a == {} :
            for vi, fn, vfunc in self.vpos :
                a[fn] = b[vi]
            return
        
        for vi, fn, vfunc in self.vpos :
            
            #a = vdict.get( fn )
            #if a is None :
            #    vdict[fn] = b
            #    continue
            
            a[fn] = vfunc( [a[fn], b[vi]] )
            
        return
        
    def is_valuecol( self, ki ):
        
        if ki.startswith( 'max(' ) and ki.endswith( ')' ):
            return max
        if ki.startswith( 'min(' ) and ki.endswith( ')' ):
            return min
        if ki.startswith( 'sum(' ) and ki.endswith( ')' ):
            return sum
            
        return None
    
    def __getitem__( self, conds ):
        return self.get( conds )
    
    def get( self, conds, defaultvalue=None ):
        
        conds = tuple( sorted([ (self.kcols[k], v) for k, v in conds.items() ]) )
        defaultvalue = {} if defaultvalue is None else defaultvalue
        
        return self.pmatrix.get( conds, defaultvalue )
    
    def get_keys( self, k ):
        return sorted(list(self.kmatrix[k]))
    



class PerspectiveMatrixCursorMixin(object):
    
    def _do_get_result(self):
        super(PerspectiveMatrixCursorMixin, self)._do_get_result()
        fields = []
        if self.description:
            for f in self._result.fields:
                name = f.name
                if name in fields:
                    name = f.table_name + '.' + name
                fields.append(name)
            self._fields = fields
    
    def fetchall( self, pm = None ):
        ''' Fetch all the rows '''
        self._check_executed()
        if self._rows is None:
            return ()
        if self.rownumber:
            result = self._rows[self.rownumber:]
        else:
            result = self._rows
        self.rownumber = len(self._rows)
        if pm == None :
            return PerspectiveMatrix( self._fields, result )
        if pm.same_fields( self._fields ) :
            pm.addrows( result )
            return pm
        raise Exception('fields not equals')
        
class PerspectiveMatrixCursor(PerspectiveMatrixCursorMixin, pymysql.cursors.Cursor):
    """A cursor which returns results as PerspectiveMatrix"""
    

class Database(object):
    
    conf = {}
    self.default_dbargs = {
        'charset' : 'utf8mb4',
        'cursorclass' : pymysql.cursors.DictCursor,
        'connect_timeout' : 3.0,
        'autocommit' : True
    }
    
    @classmethod
    def loadconfig( cls, filename="database.yaml" ):
        
        if not os.path.exists( filename ) :
            return {}
        
        with open( filename, 'r') as fp :
            conf = yaml.load(fp)
        
        cls.conf = conf
        
        return
        
    def __init__( self, database, **kwargs ):
        
        dbargs = self.default_dbargs.copy()
        dbargs.update( self.conf[self._database] )
        dbargs.update( kwargs )
        
        self._dbargs = dbargs
        self.makeconn()
        
        return
        
    def makeconn( self ):
        self.conn = pymysql.connect(**self._dbargs)
        return
        
    def __call__( self, sql, args=() ):
        return self.execute( sql, args )
        
    def tuple( self, sql, args=() ):
        return self.execute( sql, args, cursor=pymysql.cursors.Cursor )
        
    def matrix( self, sql, args=(), pm=None ):
        return self.execute( sql, args, cursor=PerspectiveMatrixCursor, pm=pm )
        
    def execute( self, sql, args, cursor=None, pm=None ):
        
        ee = None
        oe_retry = ( 2006, )
        
        fetch_kwargs = {} if pm is None else {'pm':pm}
        
        for i in range(int(self.conf['connection']['retrys'])):
            
            #st = time.time()
            
            try:
                
                with self.conn.cursor( cursor ) as cursor:
                    cursor.execute( sql, args )
                    if pymysql.cursors.RE_INSERT_VALUES.match( sql ):
                        return cursor.lastrowid
                    return cursor.fetchall( **fetch_kwargs )
            
            except pymysql.err.OperationalError as e :
                
                ee = e
                if e.args[0] in oe_retry :
                    self.makeconn()
            
            finally :
                pass
                #usedtime = time.time() - st
                #print( 'SQL used time:', usedtime )
            
        raise ee
        
Database.loadconfig()
