# Copyright (C) 2007-2013  Lars Wirzenius <liw@iki.fi>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# =*= License: GPL-3+ =*=

import coverage
import unittest
import optparse
import os
import imp
import sys
import time
import logging


__version__ = '1.11'


class AllowNothing(logging.Filter):

    '''A logging library filter that disables everything.'''

    def filter(self, record):
        return False


class CoverageTestResult(unittest.TestResult):

    def __init__(self, output, total):
        unittest.TestResult.__init__(self)
        self.output = output
        self.total = total
        self.lastmsg = ""
        self.coverage_missed = []
        self.coverage_excluded = []
        self.timings = []
        self.missing_test_modules = []

    def addCoverageMissed(self, filename, statements, missed_statements,
                          missed_description):
        self.coverage_missed.append((filename, statements, missed_statements,
                                     missed_description))

    def addCoverageExcluded(self, statements):
        self.coverage_excluded += statements

    def addMissingTestModule(self, modulepath):
        self.missing_test_modules.append(modulepath)

    def wasSuccessful(self, ignore_coverage=False, ignore_missing=False):
        return (unittest.TestResult.wasSuccessful(self) and
                (ignore_coverage or not self.coverage_missed) and
                (ignore_missing or not self.missing_test_modules))

    def _ttywrite(self, string):
        if self.output.isatty():
            self.output.write(string)
            self.output.flush()

    def clearmsg(self):
        self._ttywrite("\b \b" * len(self.lastmsg))
        self.lastmsg = ""

    def write(self, test):
        self.clearmsg()
        self.lastmsg = "Running test %d/%d: %s" % (self.testsRun,
                                                   self.total,
                                                   str(test)[:50])
        self._ttywrite(self.lastmsg)

    def startTest(self, test):
        unittest.TestResult.startTest(self, test)
        self.write(test)
        self.start_time = time.time()

    def stopTest(self, test):
        end_time = time.time()
        unittest.TestResult.stopTest(self, test)
        self.timings.append((end_time - self.start_time, test))


class CoverageTestRunner:

    """A test runner class that insists modules' tests cover them fully."""

    def __init__(self):
        self._dirname = None
        self._module_pairs = []
        self._missing_test_modules = []
        self._excluded_modules = []
        self.allow_nothing = AllowNothing()

    def add_pair(self, module_pathname, test_module_pathname):
        """Add a module and its test module to list of tests."""
        self._module_pairs.append((module_pathname, test_module_pathname))

    def add_missing(self, module_pathname):
        self._missing_test_modules.append(module_pathname)

    def add_excluded_module(self, module_pathname):
        self._excluded_modules.append(module_pathname)

    def find_pairs(self, dirname, ignored_modules):
        """Find all module/test module pairs in directory tree.

        This method relies on a naming convention: it scans a directory
        tree and assumes that for any file foo.py, if there exists a
        file foo_tests.py or fooTests.py, they form a pair.

        """

        suffixes = ["_tests.py", "Tests.py"]

        self._dirname = os.path.abspath(dirname)
        if not self._dirname.endswith(os.sep):
            self._dirname += os.sep

        for dirname, dirnames, filenames in os.walk(dirname):
            filenames = [x for x in filenames if x.endswith(".py")]

            tests = []
            for suffix in suffixes:
                tests += [(x, x[:-len(suffix)] + ".py")
                          for x in filenames if x.endswith(suffix)]

            nontests = []
            nontests = [x for x in filenames
                        if x not in [a for a, b in tests]]

            for filename, module in tests:
                if module in nontests:
                    nontests.remove(module)
                    module = os.path.join(dirname, module)
                    filename = os.path.join(dirname, filename)
                    self.add_pair(module, filename)

            for filename in nontests:
                filename = os.path.normpath(os.path.join(dirname, filename))
                if filename not in ignored_modules:
                    self.add_missing(filename)
                else:
                    self.add_excluded_module(filename)

    def _load_module_from_pathname(self, pathname):
        for tuple in imp.get_suffixes():
            suffix, mode, type = tuple
            if pathname.endswith(suffix):
                name = os.path.basename(pathname[:-len(suffix)])
                f = open(pathname, mode)
                return imp.load_module(name, f, pathname, tuple)
        raise Exception("Unknown module: %s" % pathname)

    def _load_pairs(self):
        module_pairs = []
        loader = unittest.defaultTestLoader
        for pathname, test_pathname in self._module_pairs:
            module = self._load_module_from_pathname(pathname)
            test_module = self._load_module_from_pathname(test_pathname)
            suite = loader.loadTestsFromModule(test_module)
            module_pairs.append((module, test_module, suite))
        return module_pairs

    def printErrorList(self, flavor, errors):
        for test, error in errors:
            print("%s: %s" % (flavor, str(test)))
            print(str(error))

    def enable_logging(self):
        logger = logging.getLogger()
        logger.removeFilter(self.allow_nothing)

    def disable_logging(self):
        logger = logging.getLogger()
        logger.addFilter(self.allow_nothing)

    def run(self):
        start_time = time.time()

        module_pairs = self._load_pairs()
        total_tests = sum(suite.countTestCases()
                          for x, y, suite in module_pairs)
        result = CoverageTestResult(sys.stdout, total_tests)

        for path in self._missing_test_modules:
            result.addMissingTestModule(path)

        # coverage.Coverage is a coverage.py 4.x feature.
        if hasattr(coverage, 'Coverage'):
            _coverage = coverage.Coverage()
        else:
            _coverage = coverage

        for module, test_module, suite in module_pairs:
            _coverage.erase()
            _coverage.exclude(r"#\s*pragma: no cover")
            _coverage.start()
            sys.path.insert(0, os.path.dirname(module.__file__))
            imp.reload(module)
            del sys.path[0]
            self.disable_logging()
            suite.run(result)
            self.enable_logging()
            _coverage.stop()
            filename, stmts, excluded, missed, missed_desc = \
                _coverage.analysis2(module)
            if self._dirname and filename.startswith(self._dirname):
                filename = filename[len(self._dirname):]
            if missed:
                result.addCoverageMissed(filename, stmts, missed, missed_desc)
            result.addCoverageExcluded(excluded)

        end_time = time.time()

        sys.stdout.write("\n\n")

        if result.wasSuccessful():
            print("OK")
        else:
            print("FAILED")
            print()
            if result.errors:
                self.printErrorList("ERROR", result.errors)
            if result.failures:
                self.printErrorList("FAILURE", result.failures)
            if result.coverage_missed:
                print ("Statements missed by per-module tests:")
                width = max(len(x[0]) for x in result.coverage_missed)
                fmt = "  %-*s   %s"
                print(fmt % (width, "Module", "Missed statements"))
                for filename, _, _, desc in sorted(result.coverage_missed):
                    print(fmt % (width, filename, desc))
                print()
            if result.missing_test_modules:
                print("Modules missing test modules:")
                for pathname in result.missing_test_modules:
                    print("  %s" % pathname)
                print()

            print("%d failures, %d errors" % (
                len(result.failures), len(result.errors)))

        if result.coverage_excluded:
            print(len(result.coverage_excluded), "excluded statements")
        if self._excluded_modules:
            print(len(self._excluded_modules), "excluded modules")
        if result.missing_test_modules:
            print(len(result.missing_test_modules), "missing test modules")

        maxtime = int(os.environ.get('COVERAGE_TEST_RUNNER_MAX_TIME', '10'))
        if end_time - start_time > maxtime:
            print()
            print("Slowest tests:")
            for secs, test in sorted(result.timings)[-10:]:
                print("  %5.1f s %s" % (secs, str(test)[:70]))

        print("Time: %.1f s" % (end_time - start_time))

        return result


def run():
    """Use CoverageTestRunner on the desired directory."""

    parser = optparse.OptionParser()
    parser.add_option("--ignore-coverage", action="store_true",
                      help="Don't fail tests even if coverage is "
                           "incomplete.")
    parser.add_option("--ignore-missing", action="store_true",
                      help="Don't fail even if some modules have no test "
                           "module.")
    parser.add_option("--ignore-missing-from", metavar="FILE",
                      help="Ignore missing test modules for modules listed "
                           "in FILE.")

    opts, dirnames = parser.parse_args()
    if not dirnames:
        dirnames = ['.']

    if opts.ignore_missing_from:
        lines = open(opts.ignore_missing_from).readlines()
        lines = [x.strip() for x in lines]
        lines = [x for x in lines if x and not x.startswith('#')]
        lines = [os.path.normpath(x) for x in lines]
        ignored_modules = lines
    else:
        ignored_modules = ['setup.py']

    runner = CoverageTestRunner()
    for dirname in dirnames:
        runner.find_pairs(dirname, ignored_modules)
    result = runner.run()
    if not result.wasSuccessful(ignore_coverage=opts.ignore_coverage,
                                ignore_missing=opts.ignore_missing):
        sys.exit(1)


if __name__ == "__main__":
    profname = os.environ.get('COVERAGE_TEST_RUNNER_PROFILE', None)
    if profname is None:
        run()
    else:
        import cProfile
        cProfile.run('run()', profname)
