import unittest, foo

class FooTests(unittest.TestCase):

    def testTrue(self):
        f = foo.Foo()
        self.failUnlessEqual(f.foo(True), True)
    
    def testFalse(self):
        f = foo.Foo()
        self.failUnlessEqual(f.foo(False), False)
