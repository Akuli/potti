#!/bin/bash

if [ -d downloaded-deps ]; then
    echo "Delete downloaded-deps folder and download everything again? (y/N)"
    read x
    if [ "$x" != y ]; then
        echo "Aborted."
        exit 1
    fi
fi

rm -rvf downloaded-deps
mkdir -vp downloaded-deps
cd downloaded-deps

# Download pyodide (wasm implementation of Python, meant for browser)
# https://github.com/pyodide/pyodide/releases/tag/0.25.0
wget https://github.com/pyodide/pyodide/releases/download/0.25.0/pyodide-0.25.0.tar.bz2

# Download deno (javascript interpreter to run wasm interpreter)
# https://github.com/denoland/deno/releases/download/v1.40.2/deno-x86_64-unknown-linux-gnu.zip
wget https://github.com/denoland/deno/releases/download/v1.40.2/deno-x86_64-unknown-linux-gnu.zip

# Extract pyodide
tar xvf pyodide-0.25.0.tar.bz2

# Extract deno
unzip deno-x86_64-unknown-linux-gnu.zip
