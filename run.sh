#!/bin/bash

set -euxo pipefail

SCRIPT_DIR=$(dirname "$(readlink -f "$0")")

cd $SCRIPT_DIR
export FLASK_APP=omer
flask run
