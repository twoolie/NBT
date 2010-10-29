from nbt import *
import unittest
from StringIO import StringIO
from gzip import GzipFile

class ReadWriteTest(unittest.TestCase):     # test that we can read the test file correctly
    def setUp(self):
        pass
    
    def testReadBig(self):
        mynbt = NBTFile("bigtest.nbt")
        self.assertTrue(mynbt.file != None)
    
    def testWriteBig(self):
        mynbt = NBTFile("bigtest.nbt")
        output = StringIO()
        mynbt.write_file(buffer=output)
        self.assertTrue(GzipFile("bigtest.nbt").read() == output.getvalue())
    
    def tearDown(self):
        pass
                
class TreeManipulationTest(unittest.TestCase):
    
    def setUp(self):
        self.nbtfile = NBTFile()
    
    def testRootNodeSetup(self):
        self.nbtfile.name = TAG_String("Hello World")
        self.assertEqual(self.nbtfile.name.value, "Hello World")
        
    def testTagAdd(self):
        self.testRootNodeSetup()
        #try a simple byte tag
        self.nbtfile.tags.append(TAG_Byte(name="TestByte", value=10))
        self.assertEqual(self.nbtfile["TestByte"].value, 10)
        
    #etcetera..... will finish later
        
    def tearDown(self):
        del self.nbtfile

class EmptyStringTest(unittest.TestCase):

    def setUp(self):
        self.golden_value = "\x0A\0\x04Test\x08\0\x0Cempty string\0\0\0"
        self.nbtfile = NBTFile(buffer=StringIO(self.golden_value))

    def testReadEmptyString(self):
        self.assertEqual(self.nbtfile.name.value, "Test")
        print self.nbtfile.tags
        self.assertEqual(self.nbtfile["empty string"].value, "")

    def testWriteEmptyString(self):
        buffer = StringIO()
        self.nbtfile.write_file(buffer=buffer)
        self.assertEqual(buffer.getvalue(), self.golden_value)

    def tearDown(self):
        pass

if __name__ == '__main__':
    unittest.main()
