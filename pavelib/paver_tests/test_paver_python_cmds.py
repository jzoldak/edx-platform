"""
Tests for the paver nosetest commands themselves.
Run just this test with: paver test_lib -t pavelib/paver_tests/test_paver_python_cmds.py
"""
from mock import patch
import unittest

from paver.easy import call_task

import pavelib.tests
from pavelib.utils.test.suites import SystemTestSuite
from .utils import PaverTestCase

EXPECTED_SYSTEM_SUITE_COMMAND = [
        'python',
        '-m',
        'coverage',
        'run',
        '',
        '--rcfile=/edx/app/edxapp/edx-platform/.coveragerc',
        './manage.py',
        'lms',
        'test',
        '--verbosity=1',
        'lms/djangoapps/* common/djangoapps/* openedx/core/djangoapps/* openedx/tests/* '
        'openedx/core/lib/* lms/lib/* lms/tests.py openedx/core/djangolib',
        '--with-id',
        '--settings=test',
        '',
        '--xunitmp-file=/edx/app/edxapp/edx-platform/reports/lms/nosetests.xml',
        '--with-database-isolation',
        '--with-randomly'
    ]

EXPECTED_COMMANDS = [u"", ]

class TestPaverSystemTestSuiteCmd(unittest.TestCase):
    """
    Paver Nose Suite Command test cases
    """
    def setUp(self):
        super(TestPaverSystemTestSuiteCmd, self).setUp()

    def test_with_coverage(self):
        suite = SystemTestSuite('lms', with_coverage=True)
        expected = EXPECTED_SYSTEM_SUITE_COMMAND[:]
        self.assertEqual(suite.cmd, expected)

    def test_with_cov_args(self):
        cov_args='-p --debug=dataio'
        suite = SystemTestSuite('lms', with_coverage=True, cov_args=cov_args)
        expected = EXPECTED_SYSTEM_SUITE_COMMAND[:]
        expected[4] = cov_args
        self.assertEqual(suite.cmd, expected)


class TestPaverTestSystemCmd(PaverTestCase):
    """
    Paver Nose Suite Command test cases
    """
    def setUp(self):
        super(TestPaverTestSystemCmd, self).setUp()

        # Mock the paver @needs decorator
        self._mock_paver_needs = patch.object(pavelib.tests.test_system, 'needs').start()
        self._mock_paver_needs.return_value = 0

        # Cleanup mocks
        self.addCleanup(self._mock_paver_needs.stop)


    # def test_test_js_dev(self):
    #     """
    #     Test the "test_js_run" task.
    #     """
    #     options = {
    #         "suite": 'lms',
    #         "coverage": False,
    #         "port": None,
    #     }
    #     self.reset_task_messages()
    #     call_task("pavelib.js_test.test_js_dev", options=options)
    #     self.assertEquals(self.task_messages, [])


    def test_test_system_lms(self):
        """
        Test the "test_system" task.
        """
        options = {
            'system': 'lms',
            'cov-args': '',
        }
        self.reset_task_messages()
        # from nose.tools import set_trace; set_trace()
        call_task("pavelib.tests.test_system", options=options)
        self.assertEquals(self.task_messages, [])
