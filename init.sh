#!/bin/sh

if [ -z "$(cat ~/.bashrc | grep $(pwd))" ]
then
    echo "PATH=\$PATH:$(pwd)" >> ~/.bashrc
fi

