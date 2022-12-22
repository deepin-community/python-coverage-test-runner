import logging

class Foo:

    def foo(self, a):
        logging.error('this should not be displayed when testrun runs')
        if a:
            return True
        elif False: # pragma: no cover
            return None # pragma: no cover
        else:
            import time
            time.sleep(0)
            return False

foo = Foo()
