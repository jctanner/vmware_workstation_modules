#!/bin/bash

CWD=$(pwd)
GOVCDIR=/tmp
GOVCPATH=$GOVCDIR/govc_linux_amd64
GOVCBIN=$GOVCDIR/govc
GOVCARCHIVE=govc_linux_amd64.gz
GOVCVERSION=v0.14.0
GOVCRELEASE=https://github.com/vmware/govmomi/releases/download/$GOVCVERSION/$GOVCARCHIVE

if [ ! -f $GOVCPATH ]; then
    cd $GOVCDIR
    wget $GOVCRELEASE
    gunzip $GOVCARCHIVE
    chmod +x $GOVCPATH
fi

if [ ! -s $GOVCBIN ]; then
    ln -s $GOVCPATH $GOVCBIN
fi
