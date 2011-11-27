"""
py2oct_test - Test value passing between python and Octave.

Known limitations
-----------------
* Nested lists with strings in them cannot be sent to Octave. This applies to
Numpy arrays of rank > 1 that are string or unicode as well.  Also, lists
cannot contain mixed type (strings and sublists for example).
I will try and figure this out for future releases.

* The following Numpy array types cannot be sent directly via an HDF.  The
float96 and complex192 can be recast as float64 and complex128.
   ** float96('g')
   ** complex192('G')
   ** object('o')
   ** read-write buffer('V')

* Sparse and empty matrices have not yet been implemented or tested.

"""
import unittest
import numpy as np
from oct2py import octave, Struct, Oct2Py, Oct2PyError, _utils

TYPE_CONVERSIONS = [(int, 'int32', np.int32),
               (long, 'int64', np.int64),
                (float, 'double', np.float64),
                (complex, 'double', np.complex128),
                (str, 'char', str),
                (unicode, 'char', str),
                (bool, 'int32', np.int32),
                (None, 'double', np.float64),
                (dict, 'struct', Struct),
                (np.int8, 'int8', np.int8),
                (np.int16, 'int16', np.int16),
                (np.int32, 'int32', np.int32),
                (np.int64, 'int64', np.int64),
                (np.uint8, 'uint8', np.uint8),
                (np.uint16, 'uint16', np.uint16),
                (np.uint32, 'uint32', np.uint32),
                (np.uint64, 'uint64', np.uint64),
                #(np.float16, 'double', np.float64),
                (np.float32, 'double', np.float64),
                (np.float64, 'double', np.float64),
                (np.str, 'char', np.str),
                (np.double, 'double', np.float64),
                (np.complex64, 'double', np.complex128),
                (np.complex128, 'double', np.complex128), ]


class TypeConversions(unittest.TestCase):
    """Test roundtrip datatypes starting from Python
    """

    def test_python_conversions(self):
        """Test roundtrip python type conversions
        """
        for out_type, oct_type, in_type in TYPE_CONVERSIONS:
            if out_type == dict:
                outgoing = dict(x=1)
            elif out_type == None:
                outgoing = None
            else:
                outgoing = out_type(1)
            incoming, octave_type = octave.roundtrip(outgoing)
            self.assertEqual(octave_type, oct_type)
            self.assertEqual(type(incoming), in_type)


class IncomingTest(unittest.TestCase):
    """Test the importing of all Octave data types, checking their type

    Uses test_datatypes.m to read in a dictionary with all Octave types
    Tests the types of all the values to make sure they were
        brought in properly.

    """
    def setUp(self):
        """Open an instance of Octave and get a struct with all datatypes.
        """
        self.data = octave.test_datatypes()

    def tearDown(self):
        _utils._remove_files()

    def helper(self, base, keys, types):
        """
        Perform type checking of the values

        Parameters
        ==========
        base : dict
            Sub-dictionary we are accessing.
        keys : array-like
            List of keys to test in base.
        types : array-like
            List of expected return types for the keys.

        """
        for key, type_ in zip(keys, types):
            self.assertEqual(type(base[key]), type_)

    def test_int(self):
        """Test incoming integer types
        """
        keys = ['int8', 'int16', 'int32', 'int64',
                    'uint8', 'uint16', 'uint32', 'uint64']
        types = [np.int8, np.int16, np.int32, np.int64,
                    np.uint8, np.uint16, np.uint32, np.uint64]
        self.helper(self.data.num.int, keys, types)

    def test_floats(self):
        """Test incoming float types
        """
        keys = ['float32', 'float64', 'complex', 'complex_matrix']
        types = [np.float32, np.float64, np.complex128, np.ndarray]
        self.helper(self.data.num, keys, types)
        self.assertEqual(self.data.num.complex_matrix.dtype,
                         np.dtype('complex128'))

    def test_misc_num(self):
        """Test incoming misc numeric types
        """
        keys = ['inf', 'NaN', 'matrix', 'vector', 'column_vector', 'matrix3d',
                'matrix5d']
        types = [np.float64, np.float64, np.ndarray, np.ndarray, np.ndarray,
                 np.ndarray, np.ndarray]
        self.helper(self.data.num, keys, types)

    def test_logical(self):
        """Test incoming logical type
        """
        self.assertEqual(type(self.data.logical), np.ndarray)

    def test_string(self):
        """Test incoming string types
        """
        keys = ['basic', 'char_array', 'cell_array']
        types = [str, list, list]
        self.helper(self.data.string, keys, types)

    def test_struct(self):
        ''' Test incoming struct types '''
        keys = ['name', 'age']
        types = [list, list]
        self.helper(self.data.struct.array, keys, types)

    def test_cell_array(self):
        ''' Test incoming cell array types '''
        keys = ['vector', 'matrix']
        types = [list, list]
        self.helper(self.data.cell, keys, types)


class RoundtripTest(unittest.TestCase):
    """Test roundtrip value and type preservation between Python and Octave.

    Uses test_datatypes.m to read in a dictionary with all Octave types
    uses roundtrip.m to send each of the values out and back,
        making sure the value and the type are preserved.

    """
    def setUp(self):
        """Open an instance of Octave and get a struct all datatypes.
        """
        self.data = octave.test_datatypes()

    def helper(self, outgoing):
        """
        Use roundtrip.m to make sure the data goes out and back intact.

        Parameters
        ==========
        outgoing : object
            Object to send to Octave.

        """
        incoming = octave.roundtrip(outgoing)
        try:
            self.assertEqual(incoming, outgoing)
            self.assertEqual(type(incoming), type(outgoing))
        except ValueError:
            # np arrays must be compared specially
            assert np.allclose(incoming, outgoing)
        except AssertionError:
            # need to test for NaN explicitly
            if np.isnan(outgoing) and np.isnan(incoming):
                pass
            # floats are converted to doubles by Octave
            elif (type(outgoing) == np.float32 and
                  type(incoming) == np.float64):
                pass
            elif np.allclose(incoming, outgoing):
                pass
            else:
                raise

    def test_int(self):
        """Test roundtrip value and type preservation for integer types
        """
        for key in ['int8', 'int16', 'int32', 'int64',
                    'uint8', 'uint16', 'uint32', 'uint64']:
            self.helper(self.data.num.int[key])

    def test_float(self):
        """Test roundtrip value and type preservation for float types
        """
        for key in ['float32', 'float64', 'complex', 'complex_matrix']:
            self.helper(self.data.num[key])

    def test_misc_num(self):
        """Test roundtrip value and type preservation for misc numeric types
        """
        for key in ['inf', 'NaN', 'matrix', 'vector', 'column_vector',
                    'matrix3d', 'matrix5d']:
            self.helper(self.data.num[key])

    def test_logical(self):
        """Test roundtrip value and type preservation for logical type
        """
        self.helper(self.data.logical)

    def test_string(self):
        """Test roundtrip value and type preservation for string types
        """
        for key in ['basic', 'cell_array']:
            self.helper(self.data.string[key])

    def test_struct(self):
        """Test roundtrip value and type preservation for struct types
        """
        for key in ['name', 'age']:
            self.helper(self.data.struct.array[key])

    def test_cell_array(self):
        """Test roundtrip value and type preservation for cell array types
        """
        # TODO implement nested strings and arbitrary data arrays
        for key in ['vector', 'matrix']:
            self.assertRaises(Oct2PyError, octave.roundtrip,
                              self.data.cell[key])
            #self.helper(self.data.cell[key])


class BuiltinsTest(unittest.TestCase):
    """Test the exporting of standard Python data types, checking their type.

    Runs roundtrip.m and tests the types of all the values to make sure they
    were brought in properly.

    """
    def helper(self, outgoing, incoming=None):
        """
        Uses roundtrip.m to make sure the data goes out and back intact.

        Parameters
        ==========
        outgoing : object
            Object to send to Octave
        incoming : object, optional
            Object already retreived from Octave

        """
        if incoming is None:
            incoming = octave.roundtrip(outgoing)
        expected_type = type(outgoing)
        for out_type, _, in_type in TYPE_CONVERSIONS:
            if out_type == type(outgoing):
                expected_type = in_type
                break
        try:
            self.assertEqual(incoming, outgoing)
            self.assertEqual(type(incoming), expected_type)
        except ValueError:
            # np arrays must be compared specially
            #import pdb; pdb.set_trace()
            assert np.allclose(incoming, outgoing)

    def test_dict(self):
        """Test python dictionary
        """
        test = dict(x='spam', y=[1, 2, 3])
        incoming = octave.roundtrip(test)
        incoming = dict(incoming)
        for key in incoming:
            self.helper(test[key], incoming[key])

    def test_nested_dict(self):
        """Test nested python dictionary
        """
        test = dict(x=dict(y=1e3, z=[1, 2]), y='spam')
        incoming = octave.roundtrip(test)
        incoming = dict(incoming)
        for key in test:
            #import pdb; pdb.set_trace()
            if isinstance(test[key], dict):
                for subkey in test[key]:
                    self.helper(test[key][subkey], incoming[key][subkey])
            else:
                self.helper(test[key], incoming[key])

    def test_set(self):
        """Test python set type
        """
        test = set((1, 2, 3, 3))
        incoming = octave.roundtrip(test)
        assert np.allclose(tuple(test), incoming)
        self.assertEqual(type(incoming), np.ndarray)

    def test_tuple(self):
        """Test python tuple type
        """
        test = tuple((1, 2, 3))
        self.helper(test)

    def test_list(self):
        """Test python list type
        """
        tests = [[1, 2], ['a', 'b']]
        for test in tests:
            self.helper(test)

    def test_list_of_tuples(self):
        """Test python list of tuples
        """
        test = [(1, 2), (1.5, 3.2)]
        self.helper(test)

    def test_numeric(self):
        """Test python numeric types
        """
        test = np.random.randint(1000)
        self.helper(int(test))
        self.helper(long(test))
        self.helper(float(test))
        self.helper(complex(1, 2))

    def test_string(self):
        """Test python str and unicode types
        """
        tests = ['spam', u'eggs']
        for test in tests:
            self.helper(test)

    def test_nested_list(self):
        """Test python nested lists
        """
        #TODO implement nested strings
        test = [['spam', 'eggs'], ['foo ', 'bar ']]
        self.assertRaises(Oct2PyError, octave.roundtrip, test)
        test = [[1, 2], [3, 4]]
        self.helper(test)
        # TODO implement arbitrary object passing
        test = [[1, 2], [3, 4, 5]]
        self.assertRaises(Oct2PyError, octave.roundtrip, test)

    def test_bool(self):
        """Test boolean values
        """
        tests = (True, False)
        for test in tests:
            incoming = octave.roundtrip(test)
            self.assertEqual(incoming, test)
            self.assertEqual(type(incoming), np.int32)

    def test_none(self):
        """Test sending None type
        """
        incoming = octave.roundtrip(None)
        assert np.isnan(incoming)


class NumpyTest(unittest.TestCase):
    """Check value and type preservation of Numpy arrays
    """
    def setUp(self):
        """Create the numpy code types to check and blacklist some.
        """
        self.codes = np.typecodes['All']
        self.blacklist = 'g'

    def test_scalars(self):
        """Send a scalar numpy type and make sure we get the same number back.
        """
        for typecode in self.codes:

            outgoing = (np.random.randint(-255, 255) + np.random.rand(1))
            if typecode in 'VUS':
                outgoing = np.array('spam').astype(typecode)
            else:
                try:
                    outgoing = outgoing.astype(typecode)
                except TypeError:
                    pass
            if typecode in self.blacklist:
                self.assertRaises(Oct2PyError, octave.roundtrip, outgoing)
                continue
            incoming = octave.roundtrip(outgoing)
            if typecode == '|b1':
                self.assertEqual(bool(outgoing), bool(incoming))
            else:
                try:
                   assert np.allclose(np.array(incoming), outgoing)
                except NotImplementedError:
                   self.assertEqual(np.array(incoming), outgoing)
                except IndexError:
                    assert np.alltrue(np.array(incoming) == outgoing)
                except TypeError:
                    assert np.allclose(incoming, outgoing.astype(np.uint64))

    def test_ndarrays(self):
        """Send an ndarray and make sure we get the same array back
        """
        for typecode in self.codes:
            ndims = np.random.randint(2, 4)
            size = [np.random.randint(1, 10) for i in range(ndims)]
            outgoing = (np.random.randint(-255, 255, tuple(size)))
            outgoing += np.random.rand(*size)
            if typecode in 'USV':
                outgoing = np.array('spam').astype(typecode)
            else:
                try:
                    outgoing = outgoing.astype(typecode)
                except TypeError:
                    pass
            if typecode in self.blacklist:
                self.assertRaises(Oct2PyError, octave.roundtrip, outgoing)
                continue
            incoming = octave.roundtrip(outgoing)
            try:
                assert np.allclose(incoming, outgoing)
            except AssertionError:
                assert np.alltrue(abs(incoming - outgoing) < 1e-3)
            except TypeError:
                assert np.allclose(incoming, outgoing.astype(np.uint64))


class BasicUsageTest(unittest.TestCase):
    """Excercise the basic interface of the package
    """
    def test_run(self):
        """Test the run command
        """
        out = octave.run('y=ones(3,3)')
        desired = """y =

        1        1        1
        1        1        1
        1        1        1
"""
        self.assertEqual(out, desired)
        out = octave.run('x = mean([[1, 2], [3, 4]])', verbose=True)
        self.assertEqual(out, 'x =  2.5000')
        self.assertRaises(Oct2PyError, octave.run, '_spam')

    def test_call(self):
        """Test the call command
        """
        out = octave.call('ones', 1, 2)
        self.assertEqual(repr(out), '(1.0, 1.0, 0.0)')
        U, S, V = octave.call('svd', [[1, 2], [1, 3]])
        assert np.allclose(U, ([[-0.57604844, -0.81741556],
                            [-0.81741556, 0.57604844]]))
        assert np.allclose(S,  ([[3.86432845, 0.],
                             [0., 0.25877718]]))
        assert np.allclose(V,  ([[-0.36059668, -0.93272184],
         [-0.93272184, 0.36059668]]))
        out = octave.call('roundtrip.m', 1)
        self.assertEqual(out, 1)
        import os
        fname = os.path.join(__file__, 'roundtrip.m')
        out = octave.call(fname, 1)
        self.assertEqual(out, 1)
        self.assertRaises(Oct2PyError, octave.call, '_spam')


    def test_put_get(self):
        """Test putting and getting values
        """
        octave.put('spam', [1, 2])
        out = octave.get('spam')
        assert np.allclose(out, np.array([1, 2]))
        octave.put(['spam', 'eggs'], ['foo', [1, 2, 3, 4]])
        spam, eggs = octave.get(['spam', 'eggs'])
        self.assertEqual(spam, 'foo')
        assert np.allclose(eggs, np.array([[1, 2, 3, 4]]))
        self.assertRaises(Oct2PyError, octave.put, '_spam', 1)
        self.assertRaises(Oct2PyError, octave.get, '_spam')

    def test_help(self):
        """Testing help command
        """
        out = octave.cos.__doc__
        self.assertEqual(out[:5], '\n`cos')

    def test_dynamic(self):
        """Test the creation of a dynamic function
        """
        tests = [octave.zeros, octave.ones, octave.plot]
        for test in tests:
            self.assertEqual(repr(type(test)), "<type 'function'>")
        self.assertRaises(Oct2PyError, octave.__getattr__, 'aaldkfasd')
        self.assertRaises(Oct2PyError, octave.__getattr__, '_foo')
        self.assertRaises(Oct2PyError, octave.__getattr__, 'foo\W')
        out = octave.list()
        self.assertEqual(out, dict())

    def test_open_close(self):
        """Test opening and closing the Octave session
        """
        oct_ = Oct2Py()
        oct_._close()
        self.assertEqual(True, True)

    def test_struct(self):
        """Test Struct construct
        """
        test = Struct()
        test.spam = 'eggs'
        test.eggs.spam = 'eggs'
        self.assertEqual(test['spam'], 'eggs')
        self.assertEqual(test['eggs']['spam'], 'eggs')

if __name__ == '__main__':
    print 'py2oct test'
    print '*' * 20
    unittest.main()
