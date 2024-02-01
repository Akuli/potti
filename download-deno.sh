#!/bin/bash
set -e

rm -rf deno

mkdir -v deno
cd deno

wget https://github.com/denoland/deno/releases/download/v1.40.2/deno-x86_64-unknown-linux-gnu.zip
unzip deno-x86_64-unknown-linux-gnu.zip
rm -v deno-x86_64-unknown-linux-gnu.zip
