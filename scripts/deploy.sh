#!/bin/sh
echo "Building package for distribution"
poetry build
echo "Pushing new version to PyPi"
poetry config http-basic.pypi $PYPI_USERNAME $PYPI_PASSWORD
poetry publish