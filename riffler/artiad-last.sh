SCRIPTPATH=`dirname $0`
DART_PATH=$SCRIPTPATH/../../../third_party/dart-sdk-last/bin
CLIENTPATH=$SCRIPTPATH/..
SRCPATH=$CLIENTPATH/..

export PATH=$DART_PATH:$PATH

clear
echo 'ARTIAD dart to js compilation...'
# frogc $CLIENTPATH/artiad/artiad.dart --enable_type_checks --out $SRCPATH/server/static/js/artiad
dart2js $CLIENTPATH/artiad/artiad.dart --enable-checked-mode --out=$SRCPATH/server/static/js/artiad
echo 'compiled'
