#!/bin/sh
# 第19章の npiet トレース画像（-tpic）を生成する。samples.py の後に実行する。
cd "$(dirname "$0")/../.." || exit 1
N=ext/npiet-1.3h/npiet
D=site/img/ch19
T=$(mktemp -d)
for spec in "size_fix:32" "cc_fix:32" "loop_fix:16"; do
  name=${spec%%:*}; z=${spec#*:}
  (cd "$T" && "$OLDPWD/$N" -q -cs 1 -tpic -tpf "$z" "$OLDPWD/$D/$name.png" >/dev/null 2>&1)
  mv "$T/npiet-trace.png" "$D/trace-$name.png"
done
rmdir "$T"
