#!/bin/bash
mkdir temp
export PYTHONPATH=./temp
python setup.py develop --install-dir ./temp
cp ./temp/PreventSuspend.egg-link ~/.config/deluge/plugins
rm -fr ./temp
