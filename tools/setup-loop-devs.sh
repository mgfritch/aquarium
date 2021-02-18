#!/bin/bash -e

SCRIPT_NAME=$(basename ${BASH_SOURCE[0]})
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

OSD_IMAGE_NAME="${SCRIPT_NAME%.*}_osd.img"
OSD_IMAGE_SIZE='6G'
OSD_TO_CREATE=2
OSD_VG_NAME=${SCRIPT_NAME%.*}
OSD_LV_NAME=${SCRIPT_NAME%.*}

[ -z "$SUDO" ] && SUDO=sudo

function cleanup()
{
    echo
    echo "CLEAN-UP"
    $SUDO vgchange -an $OSD_VG_NAME || true
    loopdev=$($SUDO losetup -a | grep $(basename $OSD_IMAGE_NAME) | awk -F : '{print $1}')
    if ! [ "$loopdev" = "" ]; then
        $SUDO losetup -d $loopdev
    fi
    rm -rf $TMPDIR
}
trap cleanup EXIT

# clean up previous run(s)?
cleanup

# TMPDIR for test data
[ -d "$TMPDIR" ] || TMPDIR=$(mktemp -d tmp.$SCRIPT_NAME.XXXXXX)
[ -d "$TMPDIR_TEST_MULTIPLE_MOUNTS" ] || TMPDIR_TEST_MULTIPLE_MOUNTS=$(mktemp -d tmp.$SCRIPT_NAME.XXXXXX)

echo
echo "CREATE"

# add osd.{1,2,..}
dd if=/dev/zero of=$TMPDIR/$OSD_IMAGE_NAME bs=1 count=0 seek=$OSD_IMAGE_SIZE
loop_dev=$($SUDO losetup -f)
$SUDO vgremove -f $OSD_VG_NAME || true
$SUDO losetup $loop_dev $TMPDIR/$OSD_IMAGE_NAME
$SUDO pvcreate $loop_dev && $SUDO vgcreate $OSD_VG_NAME $loop_dev

# create lvs first so ceph-volume doesn't overlap with lv creation
for id in `seq 0 $((--OSD_TO_CREATE))`; do
    echo "Creating device: $OSD_LV_NAME.$id"
    $SUDO lvcreate -l $((100/$OSD_TO_CREATE))%VG -n $OSD_LV_NAME.$id $OSD_VG_NAME
done

echo
while [ /bin/true ]; do
    duration=10
    echo "WAIT (${duration}s) ..."
    sleep 10
done
