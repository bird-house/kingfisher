#!/bin/bash

# call it like this:
# $ source activate kingfisher
# $ bash install-snappy.sh

# configuration
APP_ROOT="$(pwd -P)"

DOWNLOAD_CACHE="$APP_ROOT/downloads"
PREFIX="$APP_ROOT/src"

# misc
ESA_SNAP_URL="http://step.esa.int/downloads/6.0/installers"
ESA_SNAP="esa-snap_sentinel_unix_6_0.sh"
PYTHON=$(which python)
INSTALL_DIR=$PREFIX/snap
VARFILE=$INSTALL_DIR/install.conf

# end of configuration

echo '***************************************************'
echo '*********** start snappy installation *************'
echo '***************************************************'
echo ' '
echo '##########################'
echo '#### PYTHON is set to: ' $PYTHON
echo '##########################'
echo '#### INSTALL_DIR is set to : ' $INSTALL_DIR
echo '##########################'

mkdir -p $INSTALL_DIR
mkdir -p $DOWNLOAD_CACHE

[ -f "$DOWNLOAD_CACHE/$ESA_SNAP" ] && echo "ESA SNAP installation file already downloaded " || wget -P $DOWNLOAD_CACHE $ESA_SNAP_URL/$ESA_SNAP


cat <<EOT >> $VARFILE
deleteSnapDir=ALL
executeLauncherWithPythonAction$Boolean=true
forcePython$Boolean=true
pythonExecutable=$PYTHON
sys.adminRights$Boolean=false
sys.component.RSTB$Boolean=true
sys.component.S1TBX$Boolean=true
sys.component.S2TBX$Boolean=true
sys.component.S3TBX$Boolean=true
sys.component.SNAP$Boolean=true
sys.installationDir=$INSTALL_DIR
sys.languageId=en
sys.programGroupDisabled$Boolean=false
sys.symlinkDir=
EOT

bash $DOWNLOAD_CACHE/$ESA_SNAP -q -varfile $VARFILE

$INSTALL_DIR/bin/snappy-conf $PYTHON $INSTALL_DIR

cd $INSTALL_DIR/snappy
$PYTHON setup.py install
cd -

echo 'python snappy installed'

echo '***************************************************'
echo '*********** snappy installation done **************'
echo '***************************************************'
