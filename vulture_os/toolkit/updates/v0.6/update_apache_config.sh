#!/bin/sh

if [ -d /zroot/apache ] ; then
    cp /home/jails.apache/.zfs-source/usr/local/etc/apache24/* /zroot/apache/usr/local/etc/apache24/
    /usr/sbin/jexec apache /usr/sbin/service apache24 restart
fi

if [ -d /zroot/portal ] ; then
    cp /home/jails.apache/.zfs-source/usr/local/etc/apache24/* /zroot/portal/usr/local/etc/apache24/
    /usr/sbin/jexec portal /usr/sbin/service apache24 restart
fi
