#!/bin/bash
# usage: cmp.sh file.png [input]  -- 自作インタプリタと npiet の出力を比較
HERE=$(cd "$(dirname "$0")" && pwd)
NP=${NPIET:-$HERE/../ext/npiet-1.3h/npiet}
f=$1; in=${2:-}
a=$(printf "%b" "$in" | timeout 30 python3 "$HERE/piet.py" run "$f" | od -c)
b=$(printf "%b" "$in" | timeout 30 $NP -q "$f" 2>/dev/null | od -c)
if [ "$a" == "$b" ]; then echo "OK   $f"; else echo "DIFF $f"; echo "--- piet.py:"; echo "$a"|head -4; echo "--- npiet:"; echo "$b"|head -4; fi
