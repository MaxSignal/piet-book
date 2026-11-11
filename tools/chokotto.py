#!/usr/bin/env python3
"""chokotto.py -- ちょ古っ都製本工房の自動見積もりから料金と表紙の原稿サイズ（背幅）を取得する

  python3 tools/chokotto.py 432 216      # ページ数、カラーページ数（巻頭）
条件: B5・高彩度フルカラー・モノクロ混在印刷 お得Ver.・上質70kg・くるみ製本・表紙アートポスト200kg フルカラー・マットPP・ネコポス・1 冊
"""
import sys, re, subprocess
from bs4 import BeautifulSoup


def estimate(pages, color_pages, copies=1):
    data = ["submit_type=top", "size=6", "print=11", "kami=1", f"b={pages}", f"b2={color_pages}", "hyo=5",
            "insatsu_type=1", "insatsu_type23=9", f"a={copies}", "c=1", "form_data06_8=8", "shipping_carrier=4", "submit=1"]
    html = subprocess.run(["curl", "-s", "-X", "POST", "https://www.chokotto.jp/auto_mitsumori.php"] + sum([["--data", d] for d in data], []),
                          capture_output=True).stdout.decode("utf-8", "replace")
    t = BeautifulSoup(html, "lxml").get_text("\n", strip=True)
    total = re.search(r"合計（税込）\n([0-9,]+) 円", t)
    spine = re.search(r"背幅 ([0-9.]+)ミリ", t)
    size = re.search(r"塗り足し・背幅を含めた原稿サイズは\nh：([0-9.]+)mm × w：([0-9.]+)mm", t)
    return dict(total=int(total.group(1).replace(",", "")) if total else None,
                spine=float(spine.group(1)) if spine else None,
                cover=(float(size.group(1)), float(size.group(2))) if size else None)


if __name__ == "__main__":
    r = estimate(int(sys.argv[1]), int(sys.argv[2]))
    if len(sys.argv) > 3 and sys.argv[3] == "spine":
        print(r["spine"] if r["spine"] else "")
    else:
        print(r)
