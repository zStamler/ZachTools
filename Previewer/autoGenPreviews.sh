#!/bin/bash

# When downloading, launch this script with command-line args {ACQUISITION_NAME}, {TOTAL_NUM_ACQS}.
# It will then wait until the last acquisition finishes downloading into the Cam3 folder,
# then generate previews for all the Cam3 acqs

ACQNAME=$1
NUMACQS=$2

# this should be whatever the path is to the Cam3 folder on this particular system
NFS_PATH=/private/nfs

SCANPATH=$NFS_PATH/202109_Fall_Data/Cam3/$ACQNAME
PREVPATH=$NFS_PATH/202109_Fall_Data/PREVIEWS
python ./readConf.py $SCANPATH $NUMACQS
mkdir $PREVPATH/$ACQNAME
mkdir $PREVPATH/${ACQNAME}/symlinks
ln -s $SCANPATH/* ${PREVPATH}/${ACQNAME}/symlinks/
python ./Previewer.py input_path=${SCANPATH} output_path=${PREVPATH}/${ACQNAME} symlinks=True cam_folder=3
