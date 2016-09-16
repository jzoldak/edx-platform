from __future__ import with_statement
"""
Tests for Passthrough options
"""
import unittest

import os
from pprint import pprint

from paver.deps.six import exec_, PY2, print_, PY3
from paver.easy import call_task
from paver import setuputils, misctasks, tasks, options
import types
from pavelib.utils.passthrough_opts import PassthroughTask

OP_T1_CALLED = 0
subpavement = os.path.join(os.path.dirname(__file__), "other_pavement.py")

class FakeModule(object):
    def __init__(self, **kw):
        for name, value in kw.items():
            setattr(self, name, value)

def patched_print(self, output):
    self.patch_captured.append(output)

class FakeExitException(Exception):
    """ Fake out tasks.Environment._exit to avoid interupting tests """

def patched_exit(self, code):
    self.exit_code = 1
    raise FakeExitException(code)


def _set_environment(patch_print=False, **kw):
    pavement = FakeModule(**kw)
    env = tasks.Environment(pavement)
    tasks.environment = env
    if PY3:
        method_args = (env,)
    else:
        method_args = (env, tasks.Environment)
    env._exit = types.MethodType(patched_exit, *method_args)
    if patch_print:
        env._print = types.MethodType(patched_print, *method_args)
        env.patch_captured = []
    return env


class TestPassthrough(unittest.TestCase):

    def test_setting_of_options_with_equals(self):

        @PassthroughTask
        def t1(options, passthrough_options):
            print options
            assert options.foo == '1'
            # assert not hasattr(options, 'bar')
            # from nose.tools import set_trace; set_trace()
            pass

        @PassthroughTask
        def t2(options, passthrough_options):
            assert options.foo == '1'
            assert options.bar == '2'
            pass

        environment = _set_environment(t1=t1, t2=t2)
        tasks._process_commands(['foo=1', 't1', 'bar=2', 't2'])
        assert t1.called
        assert t2.called


    def test_options_inherited_via_needs(self):
        @PassthroughTask
        @tasks.cmdopts([('foo=', 'f', "Foo!"), ('zed=', 'z', "Zee!")])
        def t1(options, passthrough_options):
            assert options.t1.foo == "1"

        @PassthroughTask
        # @tasks.needs('t1')
        @tasks.cmdopts([('bar=', 'b', "Bar!")])
        def t2(options, passthrough_options):
            assert options.t2.bar == '2'

        environment = _set_environment(t1=t1, t2=t2)
        tasks._process_commands("t2 --foo 1 -b 2".split())
        assert t1.called
        assert t2.called
        # environment.call_task('t2', options="--foo 1 -b 2")

    def test_options_inherited_via_needs_even_from_grandparents(self):
        @tasks.task
        @tasks.cmdopts([('foo=', 'f', "Foo!")])
        def t1(options):
            assert options.t1.foo == "1"

        @tasks.task
        @tasks.needs('t1')
        @tasks.cmdopts([('bar=', 'b', "Bar!")])
        def t2(options):
            assert options.t2.bar == '2'

        @tasks.task
        @tasks.needs('t2')
        @tasks.cmdopts([('spam=', 's', "Spam!")])
        def t3(options):
            assert options.t3.spam == '3'

        environment = _set_environment(t1=t1, t2=t2, t3=t3)
        tasks._process_commands("t3 --foo 1 -b 2 -s 3".split())
        assert t1.called
        assert t2.called
        assert t3.called

    def test_options_shouldnt_overlap(self):
        @tasks.task
        @tasks.cmdopts([('foo=', 'f', "Foo!")])
        def t1(options):
            assert False

        @tasks.task
        @tasks.needs('t1')
        @tasks.cmdopts([('force=', 'f', "Force!")])
        def t2(options):
            assert False

        environment = _set_environment(t1=t1, t2=t2)
        try:
            tasks._process_commands("t2 -f 1".split())
            assert False, "should have gotten a PavementError"
        except tasks.PavementError:
            pass

    def test_options_shouldnt_overlap_when_bad_task_specified(self):
        @tasks.task
        @tasks.cmdopts([('foo=', 'f', "Foo!")])
        def t1(options):
            assert False

        @tasks.task
        @tasks.needs('t1')
        @tasks.cmdopts([('force=', 'f', "Force!")], share_with=['nonexisting_task'])
        def t2(options):
            assert False

        environment = _set_environment(t1=t1, t2=t2)
        try:
            tasks._process_commands("t2 -f 1".split())
            assert False, "should have gotten a PavementError"
        except tasks.PavementError:
            pass

    def test_options_may_overlap_if_explicitly_allowed(self):
        @tasks.task
        @tasks.cmdopts([('foo=', 'f', "Foo!")])
        def t1(options):
            assert options.t1.foo == "1"

        @tasks.task
        @tasks.needs('t1')
        @tasks.cmdopts([('foo=', 'f', "Foo!")], share_with=['t1'])
        def t2(options):
            assert options.t2.foo == "1"

        environment = _set_environment(t1=t1, t2=t2)

        tasks._process_commands("t2 -f 1".split())

        assert t1.called
        assert t2.called

    def test_exactly_same_parameters_must_be_specified_in_order_to_allow_sharing(self):
        @tasks.task
        @tasks.cmdopts([('foo=', 'f', "Foo!")])
        def t1(options):
            assert False

        @tasks.task
        @tasks.needs('t1')
        @tasks.cmdopts([('force=', 'f', "Force!")], share_with=['t1'])
        def t2(options):
            assert False

        environment = _set_environment(t1=t1, t2=t2)
        try:
            tasks._process_commands("t2 -f 1".split())
            assert False, "should have gotten a PavementError"
        except tasks.PavementError:
            pass

    def test_dest_parameter_should_map_opt_to_property(self):
        from optparse import make_option as opt

        @tasks.task
        @tasks.cmdopts([opt('-f', '--force', dest='force')])
        def t1(options):
            assert options.force == '1'

        @tasks.task
        @tasks.cmdopts([opt('-f', '--force', dest='foo_force')])
        def t2(options):
            assert options.foo_force == '1'

        environment = _set_environment(t1=t1, t2=t2)
        tasks._process_commands("t1 -f 1".split())
        tasks._process_commands("t2 -f 1".split())
        assert t1.called
        assert t2.called

    def test_dotted_options(self):
        environment = _set_environment()
        tasks._process_commands(['this.is.cool=1'])
        assert environment.options.this['is'].cool == '1'

    def test_dry_run(self):
        environment = _set_environment()
        tasks._process_commands(['-n'])
        assert environment.dry_run

    def test_consume_args(self):
        @tasks.task
        @tasks.consume_args
        def t1(options):
            assert options.args == ["1", "t2", "3"]

        @tasks.task
        def t2(options):
            assert False, "Should not have run t2 because of consume_args"

        env = _set_environment(t1=t1, t2=t2)
        tasks._process_commands("t1 1 t2 3".split())
        assert t1.called

        @tasks.task
        @tasks.consume_args
        def t3(options):
            assert options.args[0] == '-v'
            assert options.args[1] == '1'

        env = _set_environment(t3=t3)
        tasks._process_commands("t3 -v 1".split())
        assert t3.called

    def test_consume_nargs(self):
        # consume all args on first task
        @tasks.task
        @tasks.consume_nargs()
        def t11(options):
            assert options.args == ["1", "t12", "3"]

        @tasks.task
        def t12(options):
            assert False, ("Should not have run t12 because of previous "
                           "consume_nargs()")

        env = _set_environment(t11=t11, t12=t12)
        tasks._process_commands("t11 1 t12 3".split())
        assert t11.called

        # consume some args (specified numbers) on first and second task
        @tasks.task
        @tasks.consume_nargs(2)
        def t21(options):
            assert options.args == ["1", "2"]

        @tasks.task
        @tasks.consume_nargs(3)
        def t22(options):
            assert options.args == ["3", "4", "5"]

        env = _set_environment(t21=t21, t22=t22)
        tasks._process_commands("t21 1 2 t22 3 4 5".split())
        assert t21.called
        assert t22.called

        # not enougth args consumable on called task, and other task not called
        env = _set_environment(t21=t21, t12=t12)
        try:
            tr, args = tasks._parse_command_line("t21 t12".split())
            print_(tr)
            assert False, "Expected BuildFailure exception for not enougth args"
        except tasks.BuildFailure:
            pass

        # too much args passed, and unconsumed args are not tasks
        tr, args = tasks._parse_command_line("t21 1 2 3 4 5".split())
        assert args == ["3", "4", "5"]

        # consume some args (specified numbers) on first and all other on second task
        @tasks.task
        @tasks.consume_nargs(2)
        def t31(options):
            assert options.args == ["1", "2"]

        @tasks.task
        @tasks.consume_nargs()
        def t32(options):
            assert options.args == ["3", "4", "t33", "5"]

        @tasks.task
        @tasks.consume_nargs()
        def t33(options):
            assert False, ("Should not have run t33 because of previous "
                           "consume_nargs()")

        env = _set_environment(t31=t31, t32=t32, t33=t33)
        tasks._process_commands("t31 1 2 t32 3 4 t33 5".split())
        assert t31.called
        assert t32.called

    def test_consume_nargs_and_options(self):
        from optparse import make_option

        @tasks.task
        @tasks.consume_nargs(2)
        @tasks.cmdopts([
            make_option("-f", "--foo", help="foo")
        ])
        def t1(options):
            assert options.foo == "1"
            assert options.t1.foo == "1"
            assert options.args == ['abc', 'def']

        @tasks.task
        @tasks.consume_nargs(2)
        @tasks.cmdopts([
            make_option("-f", "--foo", help="foo")
        ])
        def t2(options):
            assert options.foo == "2"
            assert options.t2.foo == "2"
            assert options.args == ['ghi', 'jkl']


        environment = _set_environment(t1=t1, t2=t2)
        tasks._process_commands([
            't1', '--foo', '1', 'abc', 'def',
            't2', '--foo', '2', 'ghi', 'jkl',
        ])
        assert t1.called

    def test_optional_args_in_tasks(self):
        @tasks.task
        def t1(options, optarg=None):
            assert optarg is None

        @tasks.task
        def t2(options, optarg1='foo', optarg2='bar'):
            assert optarg1 == 'foo'
            assert optarg2 == 'bar'

        env = _set_environment(t1=t1, t2=t2)
        tasks._process_commands(['t1', 't2'])
        assert t1.called
        assert t2.called

    def test_debug_logging(self):
        @tasks.task
        def t1(debug):
            debug("Hi %s", "there")

        env = _set_environment(t1=t1, patch_print=True)
        tasks._process_commands(['-v', 't1'])
        assert env.patch_captured[-1] == "Hi there"
        env.patch_captured = []

        tasks._process_commands(['t1'])
        assert env.patch_captured[-1] != "Hi there"

    def test_base_logging(self):
        @tasks.task
        def t1(info):
            info("Hi %s", "you")

        env = _set_environment(t1=t1, patch_print=True)
        tasks._process_commands(['t1'])
        assert env.patch_captured[-1] == 'Hi you'
        env.patch_captured = []

        tasks._process_commands(['-q', 't1'])
        assert not env.patch_captured

    def test_error_show_up_no_matter_what(self):
        @tasks.task
        def t1(error):
            error("Hi %s", "error")

        env = _set_environment(t1=t1, patch_print=True)
        tasks._process_commands(['t1'])
        assert env.patch_captured[-1] == "Hi error"
        env.patch_captured = []

        tasks._process_commands(['-q', 't1'])
        assert env.patch_captured[-1] == "Hi error"

    def test_all_messages_for_a_task_are_captured(self):
        @tasks.task
        def t1(debug, error):
            debug("This is debug msg")
            error("This is error msg")
            raise tasks.BuildFailure("Yo, problem, yo")

        env = _set_environment(t1=t1, patch_print=True)
        try:
            tasks._process_commands(['t1'])
        except FakeExitException:
            assert "This is debug msg" in "\n".join(env.patch_captured)
            assert env.exit_code == 1

    def test_messages_with_formatting_and_no_args_still_work(self):
        @tasks.task
        def t1(error):
            error("This is a %s message")

        env = _set_environment(t1=t1, patch_print=True)
        tasks._process_commands(['t1'])
        assert env.patch_captured[-1] == "This is a %s message"
        env.patch_captured = []

        tasks._process_commands(['-q', 't1'])
        assert env.patch_captured[-1] == "This is a %s message"


    def test_captured_output_shows_up_on_exception(self):
        @tasks.task
        def t1(debug, error):
            debug("Dividing by zero!")
            1/0

        env = _set_environment(t1=t1, patch_print=True, patch_exit=1)
        try:
            tasks._process_commands(['t1'])
            assert False and "Expecting FakeExitException"
        except FakeExitException:
            assert "Dividing by zero!" in "\n".join(env.patch_captured)
            assert env.exit_code == 1

    def test_options_passed_to_task(self):
        from optparse import make_option

        @tasks.task
        @tasks.cmdopts([
            make_option("-f", "--foo", help="foo")
        ])
        def t1(options):
            assert options.foo == "1"
            assert options.t1.foo == "1"

        environment = _set_environment(t1=t1)
        tasks._process_commands(['t1', '--foo', '1'])
        assert t1.called

    def test_calling_task_with_option_arguments(self):
        @tasks.task
        @tasks.cmdopts([('foo=', 'f', "Foo!")])
        def t1(options):
            assert options.foo == 'true story'

        env = _set_environment(t1=t1)

        env.call_task('t1', options={
            'foo' : 'true story'
        })

    def test_calling_task_with_arguments_do_not_overwrite_it_for_other_tasks(self):
        @tasks.task
        @tasks.cmdopts([('foo=', 'f', "Foo!")])
        def t3(options):
            assert options.foo == 'cool story'

        @tasks.task
        @tasks.cmdopts([('foo=', 'f', "Foo!")])
        def t2(options):
            assert options.foo == 'true'


        @tasks.task
        @tasks.needs('t2')
        def t1(options):
            env.call_task('t3', options={
                'foo' : 'cool story'
            })

        env = _set_environment(t1=t1, t2=t2, t3=t3)

        tasks._process_commands(['t1', '--foo', 'true'])


    def test_options_might_be_provided_if_task_might_be_called(self):

        @tasks.task
        @tasks.cmdopts([('foo=', 'f', "Foo!")])
        def t1(options):
            assert options.foo == "YOUHAVEBEENFOOD"

        @tasks.task
        @tasks.might_call('t1')
        def t2(options):
            pass

        environment = _set_environment(t1=t1, t2=t2)
        tasks._process_commands("t2 -f YOUHAVEBEENFOOD".split())

    def test_calling_task_with_arguments(self):
        @tasks.task
        @tasks.consume_args
        def t2(args):
            assert args[0] == 'SOPA'


        @tasks.task
        def t1(options):
            env.call_task('t2', args=['SOPA'])

        env = _set_environment(t1=t1, t2=t2)

        tasks._process_commands(['t1'])

    def test_calling_nonconsuming_task_with_arguments(self):
        @tasks.task
        def t2():
            pass

        @tasks.task
        def t1():
            env.call_task('t2')

        env = _set_environment(t1=t1, t2=t2)

        try:
            env.call_task('t1', args=['fail'])
        except tasks.BuildFailure:
            pass
        else:
            assert False, ("Task without @consume_args canot be called with them "
                          "(BuildFailure should be raised)")

    def test_options_may_overlap_between_multiple_tasks_even_when_specified_in_reverse_order(self):
        @tasks.task
        @tasks.cmdopts([('foo=', 'f', "Foo!")], share_with=['t2', 't3'])
        def t1(options):
            assert options.t1.foo == "1"

        @tasks.task
        @tasks.needs('t1')
        @tasks.cmdopts([('foo=', 'f', "Foo!")])
        def t2(options):
            assert options.t2.foo == "1"

        @tasks.task
        @tasks.needs('t1')
        @tasks.cmdopts([('foo=', 'f', "Foo!")])
        def t3(options):
            assert options.t3.foo == "1"

        environment = _set_environment(t1=t1, t2=t2, t3=t3)

        tasks._process_commands("t2 -f 1".split())

        assert t1.called
        assert t2.called

        tasks._process_commands("t3 -f 1".split())

        assert t1.called
        assert t3.called


    def test_options_might_be_shared_both_way(self):
        @tasks.task
        @tasks.cmdopts([('foo=', 'f', "Foo!")], share_with=['t2'])
        def t1(options):
            assert options.t1.foo == "1"

        @tasks.task
        @tasks.needs('t1')
        @tasks.cmdopts([('foo=', 'f', "Foo!")], share_with=['t1'])
        def t2(options):
            assert options.t2.foo == "1"

        environment = _set_environment(t1=t1, t2=t2)

        tasks._process_commands("t2 -f 1".split())

        assert t1.called
        assert t2.called
