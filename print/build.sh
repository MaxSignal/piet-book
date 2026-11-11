#!/bin/bash
# 書籍版の入稿データを作る（ちょ古っ都製本工房「高彩度フルカラー・モノクロ混在印刷 お得Ver.」向け）
#   bash print/build.sh A        版A: 1 冊、第I〜III部カラー
#   bash print/build.sh B        版B: 1 冊、版A＋第IV部カラー図版
#   bash print/build.sh C1       版C 上巻（付録以外すべてカラー）
#   bash print/build.sh C2       版C 下巻
#   bash print/build.sh A cover  表紙だけ作り直す
set -euo pipefail
cd "$(dirname "$0")"
ROOT=..
ED=${1:-A}
MODE=${2:-all}
OUT=out/$ED
# Chromium / Chrome の実行ファイル（環境変数 CHROME で指定。既定は Playwright が入れる Chromium）
CHROME=${CHROME:-$HOME/.cache/ms-playwright/chromium-1169/chrome-linux/chrome}
VIV="npx vivliostyle build --executable-browser $CHROME"
GS="gs -q -dBATCH -dNOPAUSE -dSAFER"
GCR="{ } setblackgeneration { } setundercolorremoval"   # 黒・グレーは墨（K）だけで刷る
export EDITION=$ED
mkdir -p $OUT fonts
[ -f fonts/DelaGothicOne-Regular.ttf ] || curl -sL -o fonts/DelaGothicOne-Regular.ttf https://github.com/google/fonts/raw/main/ofl/delagothicone/DelaGothicOne-Regular.ttf

if [ "$MODE" = all ]; then
  echo "== [$ED] 1. 原稿から書籍用 HTML を生成して組版"
  PAD=0
  for i in 1 2 3 4; do
    PAD_PAGES=$PAD python3 $ROOT/tools/printbook.py
    $VIV book.html --size 182mm,257mm -o $OUT/_raw.pdf -t 1500 >/dev/null
    MORE=$(python3 $ROOT/tools/printsplit.py pad $OUT/_raw.pdf)
    echo "   $(pdfinfo $OUT/_raw.pdf | awk '/^Pages/{print $2}') ページ（方眼メモ $PAD）、さらに必要な調整 $MORE ページ"
    [ "$MORE" = 0 ] && break
    PAD=$((PAD + MORE))
  done
  echo "== [$ED] 2. 巻頭カラー（CMYK）＋モノクロ（K のみ）の入稿用 PDF（文字はアウトライン化）"
  python3 $ROOT/tools/printsplit.py $OUT/_raw.pdf $OUT/honbun.pdf 2>&1 | grep -v Ghostscript | grep -v "Outline has" || true
  $GS -sDEVICE=pdfwrite -dNoOutputFonts -sOutputFile=$OUT/honbun_proof_RGB.pdf $OUT/_raw.pdf
fi

read N C < $OUT/color_pages.txt
echo "== [$ED] 3. 表紙（背幅はちょ古っ都の自動見積もりの原稿サイズから）"
SPINE=$(python3 $ROOT/tools/chokotto.py $N $C spine || true)
python3 $ROOT/tools/chokotto.py $N $C > $OUT/estimate.txt || true
if [ -n "$SPINE" ]; then export SPINE_MM=$SPINE; fi
python3 $ROOT/tools/printbook.py cover "$N"
$VIV cover.html -o $OUT/_cover_raw.pdf -t 300 >/dev/null
$GS -sDEVICE=pdfwrite -dNoOutputFonts -dCompatibilityLevel=1.3 -sColorConversionStrategy=CMYK \
    -dProcessColorModel=/DeviceCMYK -dUseFastColor=true -sOutputFile=$OUT/cover.pdf -c "$GCR" -f $OUT/_cover_raw.pdf
$GS -sDEVICE=png16m -r100 -dTextAlphaBits=4 -dGraphicsAlphaBits=4 -sOutputFile=$OUT/cover_preview.png $OUT/_cover_raw.pdf
rm -f $OUT/_cover_raw.pdf

echo "== [$ED] 4. 確認"
for f in $OUT/honbun.pdf $OUT/cover.pdf; do
  echo "-- $f  ($(du -h "$f" | cut -f1))  $(pdfinfo "$f" | awk '/^Pages/{p=$2} /^Page size/{s=$3"x"$5} END{print p" ページ, "s" pt"}')  フォント $(pdffonts "$f" | tail -n +3 | wc -l)"
done
echo "   カラー 1〜$C / 総 $N ページ（半分以下: $([ $((C * 2)) -le $N ] && echo OK || echo NG)）  見積もり: $(cat $OUT/estimate.txt)"
