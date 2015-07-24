#!/usr/bin/env bash
set -e

###############################################################################
#
#   edx-all-tests.sh
#
#   Execute all tests for edx-platform.
#
#   This script can be called from a Jenkins
#   multiconfiguration job that defines these environment
#   variables:
#
#   `TEST_SUITE` defines which kind of test to run.
#   Possible values are:
#
#       - "quality": Run the quality (pep8/pylint) checks
#       - "lms-unit": Run the LMS Python unit tests
#       - "cms-unit": Run the CMS Python unit tests
#       - "js-unit": Run the JavaScript tests
#       - "commonlib-unit": Run Python unit tests from the common/lib directory
#       - "commonlib-js-unit": Run the JavaScript tests and the Python unit
#           tests from the common/lib directory
#       - "lms-acceptance": Run the acceptance (Selenium/Lettuce) tests for
#           the LMS
#       - "cms-acceptance": Run the acceptance (Selenium/Lettuce) tests for
#           Studio
#       - "bok-choy": Run acceptance tests that use the bok-choy framework
#
#   `SHARD` is a number indicating which subset of the tests to build.
#
#       For "bok-choy" and "lms-unit", the tests are put into shard groups
#       using the nose'attr' decorator (e.g. "@attr('shard_1')"). Anything with
#       the 'shard_n' attribute will run in the nth shard. If there isn't a
#       shard explicitly assigned, the test will run in the last shard (the one
#       with the highest number).
#
#   Jenkins configuration:
#
#   - The edx-platform git repository is checked out by the Jenkins git plugin.
#
#   - Jenkins logs in as user "jenkins"
#
#   - The Jenkins file system root is "/home/jenkins"
#
#   - An init script creates a virtualenv at "/home/jenkins/edx-venv"
#     with some requirements pre-installed (such as scipy)
#
#  Jenkins worker setup:
#  See the edx/configuration repo for Jenkins worker provisioning scripts.
#  The provisioning scripts install requirements that this script depends on!
#
###############################################################################

doCheckVars() {
    if [ -n "$CIRCLECI" ]
        then SCRIPT_TO_RUN=scripts/circle.sh
    fi
    if [ -n "$JENKINS_HOME" ]
        then
        source scripts/jenkins-common.sh
        SCRIPT_TO_RUN=scripts/generic-ci-tests.sh

    fi
}

# Clean up previous builds
git clean -qxfd

# Determine the CI system for the environment
doCheckVars

# Run appropriate CI system script
if [ -n "$SCRIPT_TO_RUN" ]
    then $SCRIPT_TO_RUN
else
    echo "ERROR. Could not detect continuous integration system."
    exit 1
fi


