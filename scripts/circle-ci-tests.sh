#!/usr/bin/env bash
set -e

###############################################################################
#
#   circle-ci-tests.sh
#
#   Execute tests for edx-platform on circleci.com
#
#   Forks should configure parallelism, and use this script
#   to define which tests to run in each of the containers.
#
###############################################################################

case $CIRCLE_NODE_INDEX in
    0)  # run the quality metrics
        echo "Finding fixme's and storing report..."
        paver find_fixme > fixme.log || { cat fixme.log; EXIT=1; }
        echo "Finding pep8 violations and storing report..."
        paver run_pep8 > pep8.log || { cat pep8.log; EXIT=1; }
        echo "Finding pylint violations and storing in report..."
        paver run_pylint -l $PYLINT_THRESHOLD | tee pylint.log || { cat pylint.log; EXIT=1; }
        # Run quality task. Pass in the 'fail-under' percentage to diff-quality
        paver run_quality -p 100

        mkdir -p reports
        echo "Finding jshint violations and storing report..."
        PATH=$PATH:node_modules/.bin
        paver run_jshint -l $JSHINT_THRESHOLD > jshint.log || { cat jshint.log; EXIT=1; }
        echo "Running code complexity report (python)."
        paver run_complexity > reports/code_complexity.log || echo "Unable to calculate code complexity. Ignoring error."

        exit $EXIT
        ;;

    19)  # run all of the lms unit tests
        paver test_system -s lms --extra_args="--with-flaky" --cov_args="-p"
        ;;

    29)  # run all of the cms unit tests
        paver test_system -s cms --extra_args="--with-flaky" --cov_args="-p"
        ;;

    39)  # run the commonlib unit tests
        paver test_lib --extra_args="--with-flaky" --cov_args="-p"
        ;;

    *)  # catch-all (no-op)
        echo "No tests were executed in this container."
        echo "Please adjust scripts/circle-ci-tests.sh to match your parallelism."
        exit 1
        ;;
esac
