#!/usr/bin/env bash

set -e

case $CIRCLE_NODE_INDEX in
    0) TEST_SUITE="noop" ;;
    1) TEST_SUITE="noop" ;;
    2) paver test_system -s cms --extra_args="--with-flaky" --cov_args="-p"
    3) TEST_SUITE="noop" ;;
esac


