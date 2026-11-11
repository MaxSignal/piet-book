# 付録H Piet の派生言語と関連言語

Piet の核になっているのは、「画像そのものがプログラムである」ことと、「命令は色そのものではなく、隣り合う色ブロックの色の変化で決まる」ことの 2 つの発想です。この発想を手本にしたり、組み替えたり、別の題材に移し替えたりした言語が、これまでにいくつも作られてきました。この付録では、そうした派生言語・方言と、Piet と比べてみると面白い 2 次元の言語・画像の言語、そして Piet の作者 David Morgan-Mar のほかの言語を紹介します。最後に、自分で Piet の派生言語を設計するときの考え方をまとめます。

Piet の処理系・開発環境・コンパイラ、クワインなどの作品は[第20章](ch20.html)で扱ったので、ここでは繰り返しません。本付録の内容は、2026 年 11 月の時点で各ページを確認したものです。出典の URL は末尾の「参考 URL」にまとめました。

紹介する言語の多くは、難解プログラミング言語の情報を集めた wiki である Esolang wiki（esolangs.org）に載っています。この wiki は誰でも編集でき、ページに作者名が書かれていないこともよくあります。その場合は、ページの編集履歴で最初にページを作った利用者を調べ、「ページの作成者」として示しました。ページの作成者が言語の作者と同じとは限らない点に注意してください。

## H.1 全体の見取り図

まず、本付録で取り上げる言語を、Piet との関係で大まかに分けておきます。

| 分類 | 言語 | Piet との関係 |
|---|---|---|
| Piet を拡張した方言 | Piet++（Esolang wiki）、UltraPiet | 色や命令、データ型を増やす |
| 色の解釈を変えた派生 | Piet-Q、Pietfuck | 画像を使う点は同じだが、命令の決め方が違う |
| 表現の形式を変えた派生 | 🅿🅸🅴🆃、Pietfood、pgmpiet | 命令は Piet と同じで、色を絵文字・単語・灰色で表す |
| Piet の先輩・同時代の言語 | Befunge、Brainloller、Braincopter | 2 次元の言語、画像の言語 |
| Piet に影響を受けた言語 | Velato、Floater、Annoying Alice 2D、Reso ほか | 「変化で命令を決める」「画像がプログラム」などの発想を借りる |

Esolang wiki の Piet のページの「See also」には、Piet++、🅿🅸🅴🆃、Pietfood、pgmpiet の 4 つが挙げられています。なお、「Piet の派生言語」を集めたカテゴリー（Category:Piet derivatives のような名前のもの）は、確認した時点の Esolang wiki には存在しませんでした。

## H.2 「Piet++」という名前の 2 つのもの

「Piet++」という名前は、少なくとも 2 か所で使われています。Esolang wiki の言語のページと、SourceForge のプロジェクトです。両者の関係を示す記述は見つからず、名前が同じだけの別物と考えられますが、関係の有無そのものは確認できませんでした。

### Esolang wiki の Piet++

Esolang wiki の Piet++ のページは、2015 年 4 月に利用者 SplatterWorthy によって作られました。その後も同じ利用者が 2018 年と 2022 年に手を入れており、2026 年 8 月には別の利用者がサンプルを追加しています。ページの冒頭には「作業中で、まだ開発途上である」と書かれていて、カテゴリーは「未実装（Unimplemented）」です。

ページによると、Piet++ は「メインのスタックの中に複数のスタックを持てるようにした Piet の変種」で、スタック操作の副作用を抑えつつ、Piet の感触と哲学に忠実であることを目指しています。色ブロック、DP と CC、出口のコーデルの選び方といった実行の仕組みは Piet と同じです。変わったのは次の点です。

- **64 色のパレット**: 赤・緑・青の各チャンネルが 00、55、AA、FF の 4 段階をとる 6 ビットの色空間を使う。白（#FFFFFF）と黒（#000000）は Piet と同じ振る舞いをする。
- **命令の決め方**: 2 つの色の差を、赤と青のチャンネルでは 4 を法として、緑のチャンネルでは 2 を法として求め、その組で命令を選ぶ（緑のチャンネルの最上位ビットは、白と黒を除いて無視される）。組み合わせは 4 × 4 × 2 = 32 通りで、何もしない Noop を除く 31 個の命令がある。
- **入れ子のスタック**: スタックには整数だけでなくスタックも積める。スタックポインタを上下の階層に動かす命令や、階層をまたいで値を移す命令がある。
- **画像の読み書き**: プログラムの画像そのもののコーデルの色を読み書きする Read と Write の命令がある。つまり自己書き換えができる。

命令表は次のとおりです（行が青の差、列が赤の差）。

| 緑の差 0 | 赤 0 | 赤 1 | 赤 2 | 赤 3 |
|---|---|---|---|---|
| 青 0 | Noop | Push-Int | Push-Stack | Pop |
| 青 1 | Dup | Roll | Roll-Context | Push-up |
| 青 2 | Push Down | Pull Up | Up | Down |
| 青 3 | Add | Subtract | Multiply | Divide |

| 緑の差 1 | 赤 0 | 赤 1 | 赤 2 | 赤 3 |
|---|---|---|---|---|
| 青 0 | Mod | Negate | Not | Greater |
| 青 1 | Equal | Lesser | Size | In Integer |
| 青 2 | In Character | Out Integer | Out Character | Depth |
| 青 3 | Read | Write | Pointer | Toggle |

Push-Int は Piet の `push` と同じく、出てきたブロックの大きさを積みます。Pointer と Toggle は、Piet の `pointer` と `switch` にあたります。Piet にはない Equal（等しい）や Lesser（小さい）、Negate（符号反転）が加わっている一方で、仕様に定義されていない動作は「無視して実行を続けることを推奨する」としている点は Piet の流儀を受け継いでいます。

例として、XKCD の漫画（第 221 回）にちなんだ「4 を出力するだけの乱数生成器」という Esolang wiki のお題（XKCD Random Number）を解く 7 × 3 コーデルの画像が載っていますが、ページ自身が「言語は開発中で、このプログラムは仕様を完全には反映していないかもしれない」と注記しています。

### SourceForge の Piet++

SourceForge には「pietpp」というプロジェクトがあり、2008 年 10 月 10 日に登録されています。説明文は「Piet++ は、元の Piet プログラミング言語を拡張・発展させた Piet++ の、第一の処理系である」というもので、開発者は coppro、言語は C++ です。

公開されている Subversion のリポジトリには 2008 年 10 月から 12 月までの 5 回のコミットがあり、ソースには「Piet++ - Advanced Piet Interpreter」「Copyright (C) 2008 Sean "coppro" Hunt」と書かれています。ソースを読むと、画像を読み込んでコーデルの大きさを推定し、色ブロックとその隣接関係を組み立て、`--print` オプションでその構造を文字で出力するところまでが実装されていました。一方、プログラムを実行する部分は見当たらず、Piet をどのように拡張する予定だったのかを説明する文書も見つかりませんでした。したがって、この Piet++ が言語としてどんな拡張を持つのかは確認できませんでした。

### 「Piet+」「Piet 2」「PietPlus」

似た名前についても調べました。Esolang wiki には「Piet+」「Piet 2」「Piet2」「PietPlus」という題のページはなく、題が「Piet」で始まるページは Piet、Piet++、Piet-Q、Pietfood、Pietfuck の 5 つだけでした。GitHub で「pietplus」を検索して見つかるのは SanguineL の PietPlus だけで、これは標準の Piet のための JavaScript 製の IDE とインタプリタ（ascii-piet 形式の読み込みに対応）であり、方言ではありません。「Piet 2」という名前の言語は見つかりませんでした。

## H.3 そのほかの派生言語・方言

### UltraPiet

UltraPiet は、Muratam が作った日本語の Piet 拡張です。GitHub のリポジトリは 2016 年 2 月に作られ、最後の更新は同年 4 月です。C++ と Qt で書かれていて、リポジトリの説明には「最強のPiet拡張 (IDE付き)」とあります。[第20章](ch20.html)でも名前だけ紹介しました。

README によると、新しい機能は次のとおりです。

- 既存の Piet のプログラムもそのまま動く。
- スタックに木構造を積める。
- 強力な文字処理の仕組みがある。
- DLL を読み込んで関数を呼べる。
- 別の Piet の画像を呼び出せる。
- 専用の IDE で、キーボードでの編集、ステップ実行、命令の履歴を扱える。

UltraPiet の面白いところは、互換性を保つための工夫です。README は「UltraPiet はあくまでも Piet」であり、色は 18 色しか使わず、C に対する C++ のように旧来の Piet のコードもそのまま動く、と述べています。では、新しい命令はどこに入れたのでしょうか。wiki の仕様によると、ふつうは実行しない「0 による除算」と「0 による剰余」に新しい意味を持たせています。

- `divide` で `[… n 0]` を割ると、`n.png` という名前の Piet の画像を読み込んで実行する（モジュールの呼び出し）。
- `mod` で `[… x1 … xn n 0]` を割ると、上から n 個の要素をまとめた木を 1 つ積む。

木どうしの `add` は連結になり、`switch` は入れ子の木を平らにし、`out(char)` は木を文字列として出力する、というように、既存の命令が木に対しても意味を持つように拡張されています。木を引数にした `roll` は DLL の関数を呼び出す命令になり、仕様には Windows の `user32` の `MessageBoxA` を呼ぶ例が載っています。また、20 色以外の色のコーデルに入ると、そのカラーコードが表す数を要素とする木を積みます（たとえば #000048 なら 72）。コーデルサイズは、関数呼び出しでの混乱を避けるため 1 に固定されています。

リポジトリには、UltraPiet で作ったハンググライダーのゲームのサンプルも含まれています。

### Piet-Q

Piet-Q は、Esolang wiki によると poiuy_qwert が作った Piet の改造版で、ページは 2006 年に作られています。画像をプログラムとして使う点は Piet と同じですが、命令の決め方がまったく違います。

- 色ブロックではなく、1 ピクセルが 1 つの命令になる。
- ピクセルの色を赤・緑・青に分け、**赤の値が命令の番号**、緑と青の値がその命令の引数になる。
- 0〜255 の番号を持つ 256 本のスタックがある。

命令は 0〜22 の 23 個で、終了、整数や文字の出力、スタックの複製や回転、比較して右か左に曲がる分岐、座標を指定したジャンプ、指定した座標のピクセルの色を書き換える命令（自己書き換え）などがあります。ページでは、Piet が色相の**差**で命令を呼ぶのに対して、Piet-Q はピクセルの色の**値**そのものを使う、という違いが強調されています。作者のインタプリタへのリンクは切れています。

### テキストで書く Piet ― 🅿🅸🅴🆃 と Pietfood

画像の代わりに文字で Piet を書く派生言語もあります。どちらも「命令は Piet と同じ」とされていて、変わっているのは色の表し方だけです。

**🅿🅸🅴🆃**（Piet を囲み文字で書いた名前）は、2022 年 3 月に利用者 ColorfulGalaxy が作ったページで、「Piet に触発された、Piet のテキスト版」と説明されています。20 色のそれぞれに絵文字を割り当て、淡い色はハート（❤ など）、通常の色は丸（🔴 など）、濃い色は四角（🟥 など）で表し、白と黒は白丸と黒丸です。茶色の絵文字は未定義の動作、行の長さがそろっていないのも未定義の動作とされています。処理系によっては、通るたびに白か黒かをランダムに決める灰色の記号を備えていて、乱数生成器を作れる、とも書かれています。

**Pietfood** は、2026 年 1 月に利用者 Yoyolin0409 が作ったページで、🅿🅸🅴🆃 に触発された言語とされています。色の代わりに食べ物の名前を使い、白は Tofu、黒は Dry Olive、赤は Spicy、淡赤は Rose、濃赤は Tomato、といった対応になっています。🅿🅸🅴🆃 の灰色の記号にあたるものとして、白か黒かをランダムに決める「Cooked Pork」も紹介されています。ただし、1 行の中で食べ物の名前をどう区切るのかは、ページからは読み取れませんでした。

本書のテキスト格子（[付録B](appB.html)）や、第20章で紹介した ascii-piet も、「1 コーデル = 1 文字」で Piet を文字に置き換える点では同じ発想です。違いは、本書のテキスト格子や ascii-piet が画像を作るための記法であるのに対して、🅿🅸🅴🆃 や Pietfood は文字の並びそのものを独立した言語として定めていることです。

### pgmpiet

pgmpiet は、2026 年 9 月に利用者 Miui が作ったページで、「Piet から派生した言語」とされています。プログラムは灰色の濃淡だけからなる PGM（portable graymap）形式の画像として保存します。Piet の 18 色を 18 段階の灰色に置き換え、白は 255 のまま、黒の役目は 33 の灰色が担い、0 の黒は PGM のヘッダを出力する、という対応になっています。命令は Piet と同じです。

PGM には、画素の値をバイト列で並べるバイナリ形式（P5）と、数を空白区切りで並べるテキスト形式（P2）があります。pgmpiet のページは同じプログラムをこの両方の形で示しています。各濃淡には対応する文字（33 は `!`、255 は `ÿ` など）も添えられていて、バイナリ形式のプログラムは文字の並びとしても表示されています。ページには「Hello, world!」のプログラムのほか、Python のインタプリタ、オンラインのビジュアルエディタ、Brainfuck から pgmpiet への変換器、韓国語の 2 次元言語 Aheui から pgmpiet への変換ツールへのリンクが載っています。

名前の似た Pgmpietoncracklang というページもありますが、こちらは PGM 形式のファイルをプログラムとする冗談の言語で、pgmpiet とは別物です。

### Pietfuck

Pietfuck は、2025 年 6 月に利用者 Tommyaweosme が作った、Piet と Brainfuck を混ぜた言語です。色は赤・緑・青の 3 色相と淡・通常・濃の 3 段階の明度で 9 色に減らされ、実行は淡赤から始まります。命令は Piet と同じく「何色相右へ、何段階暗く」で決まり、Brainfuck の 8 つの命令（`+ - . < > , [ ]`）と「反時計回りに曲がる」命令が割り当てられています。白は何もしない命令です。

ただし、命令表の「3 色相右・3 段階暗く」の欄は、色相も明度も一周して同じ色に戻る組み合わせです。これが同じ色のブロックの中の移動とどう区別されるのかは、ページからは読み取れませんでした。パレットを小さくすると、こうした「一周」の扱いを決めておく必要が出てくる、というよい例です。

## H.4 2 次元の言語・画像の言語と Piet

### Befunge ― Piet の着想のもと

Befunge は、Chris Pressey が 1993 年に作った 2 次元の言語です。Esolang wiki によると、できるだけコンパイルしにくい言語を目標に作られました。プログラムは ASCII 文字の 2 次元の格子で、命令ポインタは上下左右のどれかの向きに「慣性」で進み続け、`>` `v` `<` `^` などの命令で向きを変えます。データは主にスタックに置き、格子の任意のセルを読み書きできるので、自己書き換えもできます。

Morgan-Mar は esoteric.codes のインタビュー（2015 年、聞き手は Daniel Temkin）で、Piet は Befunge に触発されたもので、「単なる文字の 2 次元配列ではなく、本物の画像をプログラムのコードとして使えないかと考えた」と語っています。両者を比べると、Piet がどこを変えたのかがよくわかります。

- Befunge では 1 つのセルが 1 つの命令で、命令は文字そのもので決まる。Piet では色ブロックが単位で、命令は隣のブロックとの色の差で決まる。
- Befunge は向きを変える専用の命令を持つ。Piet では、黒や画像の端にぶつかったときの DP と CC の規則と、`pointer` と `switch` で向きを変える。
- Befunge の数は文字（`0`〜`9`）で書く。Piet の数はブロックの大きさで表す。
- Befunge は自己書き換えができるが、Piet にはその手段がない。

### Brainloller と Braincopter ― 画像の Brainfuck

Brainloller は、Lode Vandevenne が 2005 年に作った、PNG 画像のピクセルから命令を読む Brainfuck のクローンです。Esolang wiki には「Piet のように」画像から命令を読むと書かれています。

- Brainfuck の 8 つの命令に、赤 (255,0,0) が `>`、濃い赤 (128,0,0) が `<`、緑が `+` というように、**決まった RGB 値**を割り当てる。
- 命令ポインタを時計回り・反時計回りに 90 度回す 2 つの命令（シアンと濃いシアン）を加え、1 次元の Brainfuck のコードを 2 次元に折りたたんで並べられるようにした。
- それ以外の色はすべて何もしない命令。命令ポインタが画像の外に出ると終了する。

回転の命令は機能を増やすものではなく、取り除けば元の 1 次元の Brainfuck に戻せる、とページに書かれています。何もしない色が多いので、写真の中にコードを隠したり、コメントを絵で描いたりできるのも特徴です。2015 年には別の人（TrapperHell）が、Extended Brainfuck の命令に対応する色を追加しています。

Braincopter は、同じ Lode Vandevenne が同じ 2005 年に作った、Brainloller とほぼ同じ言語です。違いは命令の決め方で、色の値から `(65536 × R + 256 × G + B) % 11` を計算し、0〜7 が Brainfuck の命令、8 と 9 が回転、10 が何もしない命令になります。どんな色でもいずれかの命令になるので、写真の各ピクセルを「目的の命令になる、いちばん近い色」に置き換えれば、見た目をほとんど変えずにプログラムを埋め込めます。Esolang wiki は、これを優れたステガノグラフィ（情報を目立たないように埋め込む技術）の性質として紹介しています。

Brainloller は「色の値 = 命令」という最も素直な対応で、使える色は限られます。Braincopter は計算式で色を命令に写して、見た目の自由をほぼ取り戻しました。Piet は「色の差 = 命令」とすることで、どの色から描き始めても同じ命令の列を描けます。3 つの言語は、見た目の自由と命令の読みやすさの間で、それぞれ違う位置を選んでいるといえます。

### Piet に影響を受けた言語

Esolang wiki で Piet に触れている言語のページから、Piet との関係がページに明記されているものを選んで紹介します。

| 言語 | 作者・ページの作成者 | 年 | 概要 |
|---|---|---|---|
| Velato | Daniel Temkin | 2009 | MIDI ファイルがプログラム。最初の音を基準の音とし、そこからの**音程**で命令や式を表す。影響を受けた言語として Piet を挙げる |
| Floater | Zom-B | 2014 | 16 色の EGA パレットで命令のグループを選び、同じ色が上下左右につながった**領域の面積**で、グループの中の命令や数値を選ぶ。分岐は自己書き換えでしか作れない。作者は Piet に触発され、色相の循環を覚えなくてよい言語を目指したと書いている |
| Annoying Alice 2D | Reddy Alice（ページの作成者） | 2018 | Piet のような 2 次元言語に触発され、隣り合うピクセルの ARGB 値の差を使う。緑とアルファの差で命令を、赤と青の差で値を決める |
| Reso | lynndotpy | 2024 | 画像で論理回路を描く言語。AND と XOR のゲート、入出力、3 種類の配線（各オン・オフ）を 10 色で表す。影響を受けた言語に Piet を挙げる（最初の実装は 2018 年） |
| RandBow | Fox | 2021 | 「Brainfuck と Piet を混ぜたような」画像の言語。ピクセルを左上から 1 行ずつ順に実行し、色ごとに決まった命令を持つ |
| Cbazyx | ページの作成者は Ϫ | 2025 | 色の差で命令を決める Piet の方法を、アルファベットに当てはめた言語。2 文字の間の「シーザー暗号の円盤の回転量」が命令になるので、シーザー暗号をかけても同じように動く |
| Letterfuck | ページの作成者は 4A10LOAIH | 2026 | Brainfuck と Piet に触発された言語。隣り合う文字の差で命令を、同じ文字の繰り返し（ブロック）の長さで引数を表す |
| Peet | Hammy | 2025 | Brainfuck の拡張。ピクセルの R+G+B を 16 で割った余りで命令を選ぶ方式と、Piet 風に RGB の変化で命令を選ぶ方式がある。未実装 |

中でも Velato は興味深い存在です。音の高さそのものではなく、基準の音からの「音程」で命令を決めるのは、色そのものではなく「色の変化」で命令を決める Piet とまったく同じ考え方です。この仕組みなら、基準の音ごと旋律を移調しても音程は変わらないので、同じプログラムになると考えられます。これは、Piet のプログラムの色相を一斉にずらしても色の差が変わらず、同じ動作になることと対応しています。Cbazyx がシーザー暗号に強いのも、同じ理由です。Velato の作者 Daniel Temkin は、前述の Morgan-Mar へのインタビューを行った esoteric.codes の運営者でもあります。

Floater も、Piet の `push` が「ブロックの大きさ」を積むという発想を、命令の選択にまで広げたものとして読めます。

### 設計の比較

ここまでの言語を、いくつかの観点で並べてみます。

| 言語 | 命令の単位 | 命令の決め方 | 数の作り方 | 向きの変え方 | 自己書き換え |
|---|---|---|---|---|---|
| Piet | 色ブロック | 隣のブロックとの色相と明度の差 | ブロックの大きさ | 黒・端での DP と CC の規則、`pointer` と `switch` | なし |
| Befunge | 1 文字 | 文字そのもの | 数字の文字（その数を積む）と演算 | 向きを変える命令 | あり |
| Brainloller | 1 ピクセル | 決まった RGB 値 | `+` と `-` の繰り返し | 回転の命令 | なし |
| Braincopter | 1 ピクセル | RGB 値から計算した値 | `+` と `-` の繰り返し | 回転の命令 | なし |
| Piet-Q | 1 ピクセル | 赤の値 | 緑と青の値（引数） | 比較して曲がる命令、座標へのジャンプ | あり |
| Floater | 同じ色の領域 | 色（16 色）と領域の面積 | 領域の面積 | 命令による回転 | あり（分岐に必須） |
| Piet++ | 色ブロック | 64 色の RGB の差 | ブロックの大きさ | Piet と同じ | あり（Read・Write） |
| Velato | 音符 | 基準の音からの音程 | 数字ごとの音符 | while・if の構文 | なし |

## H.5 David Morgan-Mar のほかの言語

Piet の作者 David Morgan-Mar は、自分のサイトの「DM's Esoteric Programming Languages」のページで、次の 8 つの言語を公開しています（説明はそのページの 1 行紹介と各言語のページによります）。

| 言語 | 概要 |
|---|---|
| BIT | すべてのデータを、C が文字列を扱うように扱う言語。データ型はビットと「ビットのアドレス」の 2 つだけ |
| Chef | プログラムが料理のレシピに見える言語。材料が値を持ち、ボウルや焼き皿がスタックの役目をする |
| Haifu | 東洋の哲学と美意識に基づく言語。コードは英語の俳句（5・7・5 音節）で書き、五行（木・火・土・金・水）を元にする。作者自身が仕様は未完成と書いている |
| HQ9++ | Cliff L. Biffle の HQ9+ をオブジェクト指向に拡張した言語。HQ9+ のプログラムはそのまま動く |
| Ook! | オランウータンのための言語。`Ook.` `Ook?` `Ook!` の 3 語の組み合わせで命令を表し、Brainfuck と本質的に同型 |
| Piet | 本書の主題。プログラムが現代美術の作品に見える言語 |
| Whenever | 「急ぐ気のない」言語。行は書いた順ではなく、インタプリタがランダムに選んだ順に実行される |
| ZOMBIE | 邪悪な死霊術師のための言語。ゾンビや幽霊、悪魔などの「実体」を使ってプログラムを書く |

同じページには、ソートなどの「難解なアルゴリズム」（Dropsort、Bogobogosort、Intelligent Design Sort など）や、「報酬と罰」に基づく難解なオペレーティングシステム Petrovich も載っています。

前述のインタビューで、Morgan-Mar は、最初に作った言語はおそらく Ook! で、Piet はその次だったと思う、と語っています。また、作ったときにいちばん満足したのは Whenever で、Piet は「プログラムが画像でありうる」という 1 つの常識を破っただけだが、Whenever は「制御の流れのない言語」という、より大きな飛躍だった、とも述べています。一方で、Ook! は自分の言語の中で「いちばん恥ずかしい」ものだそうです。

## H.6 派生言語を自分で設計するには

ここからは、筆者の考えをまとめます。Piet の派生言語を自分で作ってみたいときに、どんな選択肢があるかを、本章で紹介した言語を例に整理しましょう。

### パレットの大きさ

Piet の 20 色は、6 つの色相と 3 段階の明度の組（18 色）に、白と黒を加えたものです。色相と明度がどちらも循環するので、2 色の差は「色相の差（0〜5）」と「明度の差（0〜2）」の組になり、命令は 6 × 3 − 1 = 17 個になります（差が 0 の組は同じ色なので命令がありません）。

パレットを大きくすれば、命令を増やせます。Piet++ は 64 色で 31 個の命令を用意しました。反対に、Pietfuck は 9 色に減らし、Brainfuck の命令に合わせています。ただし、色を増やすほど、見分けにくい色が増え、描くときにも読むときにも間違えやすくなります。また、H.3 の Pietfuck で見たように、色相や明度の段階が少ないと「一周して同じ色に戻る」組み合わせが命令表に入り込みやすくなるので、その扱いも決めておく必要があります。

### 命令の割り当て ― 差か、値か

Brainloller や Piet-Q のように「色の値そのもの」に命令を割り当てると、画像を見ただけで命令が読み取りやすくなります。その代わり、同じ命令を続けるには同じ色のピクセルを並べるしかなく、見た目の自由は狭まります。Piet や Velato のように「変化」に命令を割り当てると、どの色からでも描き始められ、全体の色調を変えても同じプログラムになります。その代わり、1 つの色だけを見ても命令は決まりません。Braincopter のように、計算式で色を命令に写すという中間の道もあります。

### 数の作り方

Piet の `push` は、ブロックの大きさを積みます。大きな数は、小さな数の掛け算や足し算で作ることになります（[第6章](ch06.html)）。これを変える方法としては、Floater のように領域の面積を命令の引数にも使う、Piet-Q のように色のチャンネルの値を数として使う、UltraPiet のように 20 色以外の色にカラーコードの値を持たせる、などが考えられます。色の値を数として使うと文字列の出力は楽になりますが、その分「絵を描く自由」と「数を表す自由」が競合します。

### 制御の流れ

Piet の制御の流れは、DP と CC、黒と画像の端、白の上の滑り、そして `pointer` と `switch` で決まります。ほかの言語を見ると、Befunge や Brainloller のように向きを変える専用の命令を置く、Piet-Q のように座標へジャンプする、Floater や Piet++ のように画像を書き換える、といった方法があります。自己書き換えを入れると表現力は増しますが、[第20章](ch20.html)で見たような「画像を解析してコンパイルする」道具は作りにくくなります。

### データ構造と入出力

Piet のデータはスタック 1 本と整数だけです。Piet-Q の 256 本のスタック、Piet++ の入れ子のスタック、UltraPiet の木構造は、どれもこの制約を緩める工夫です。入出力も、UltraPiet はモジュールや DLL の呼び出しで標準入出力の外へ広げています。

### 互換性

UltraPiet が「0 による除算」に新しい意味を持たせたのは、既存の Piet のプログラムを壊さずに命令を追加するための、よく考えられた方法です。Piet の仕様は 0 による除算を処理系に任せ、無視することを推奨しているので、まともなプログラムはふつう 0 で割りません（[付録C](appC.html)）。ただし厳密には、「0 で割っても何も起きない」ことを当てにしたプログラムは、UltraPiet では動作が変わります。互換性を保つ拡張を考えるときは、このような「仕様で無視される操作」や「規定外の色」が、命令を追加できる数少ない隙間になります。

### piet.py を改造して試す

本書付属の `tools/piet.py`（[第16章](ch16.html)、全文は付録G）は、派生言語の実験台にちょうどよい大きさです。ただし、`tools/piet.py` そのものは本書のサンプルの検証や Piet スタジオから使われているので、別の名前のファイル（たとえば `mypiet.py`）にコピーしてから改造するか、次の例のように `import` して部分的に差し替えるのが安全です。主な改造の場所は次のとおりです。

| 変えたいこと | piet.py の場所 |
|---|---|
| パレット（色の数と RGB 値） | `HUES`、`LIGHTS`、`(色相, 明度)` を RGB 値に対応させる辞書 `RGB` と、その逆引きの `RGB2COL` |
| 規定外の色の扱い | `Program.from_image` の引数 `unknown`（既定は白） |
| テキスト格子の文字 | `CHARS` と `COL2CHAR` |
| 色の差と命令の対応 | 表 `CMDS`（`CMDS[色相の差][明度の差]`）と、差を 6 と 3 を法として求める `command_between` |
| 命令の意味 | `Machine.execute`（命令名とブロックの大きさを受け取る） |
| 制御の流れ | `Machine.step`（出口のコーデルと、8 回の試行）、`Machine._slide`（白の上の滑り）、`exit_codel` |

たとえば、UltraPiet にならって「0 による `divide`」に新しい意味を与えるには、`Machine` を継承して `execute` だけを差し替えれば済みます。piet.py の `execute` は、実行できない命令のときに `"ignored"` を返してスタックを変えない作りなので、その手前で新しい動作を割り込ませます。次の例は、`[… n 0]` で `divide` を実行したら 2 つの値を取り除き、残りのスタックの中身を標準エラー出力に表示する、デバッグ用の方言です。

```python
import sys
import piet   # tools/ をモジュールの検索パスに入れておく

class MyMachine(piet.Machine):
    """0 による divide に新しい意味を与えた方言"""
    def execute(self, cmd, size):
        st = self.stack
        if cmd == "divide" and len(st) >= 2 and st[-1] == 0:
            st.pop(); st.pop()
            print("stack:", piet.fmt_stack(st), file=sys.stderr)
            return None
        return super().execute(cmd, size)
```

`MyMachine(プログラム, 入力).run()` のように使えば、`step` が自動的にこの `execute` を呼びます。パレットや命令表を変えたい場合は、`RGB`・`RGB2COL`・`CHARS` と、`CMDS`・`command_between` をまとめて書き換えることになります。たとえば明度を 4 段階にするなら、`LIGHTS` と `RGB` に 6 色を加え、`CMDS` の各行を 4 列にし、`command_between` の明度の差を 4 を法として求めるように変えます。

なお、`tools/pasm.py` は piet.py の `CMDS` から逆引きした `CMD_DELTA` と `next_color` を使って色を選んでいるので、命令表を変えた方言の画像をアセンブラで作るには、こちらにも対応する変更が必要です。また、npiet や Piet スタジオ、本書のブラウザ版ビューアは、当然ながら自作の方言を知りません。方言のプログラムは、方言の処理系で確かめましょう。

### 仕様を書く

派生言語を作ったら、仕様を文章にして公開しましょう。[付録C](appC.html)で見たように、Piet は多くの細部を処理系に任せたため、処理系ごとに動作が分かれました。命令表だけでなく、スタックが足りないとき、0 で割ったとき、規定外の色に出会ったときの動作まで決めておけば、ほかの人が処理系を書きやすくなります。そこに自分の処理系で動く「Hello, world!」の画像を 1 つ添えれば、新しい難解プログラミング言語の誕生です。

## 参考 URL

- Esolang wiki「Piet」: https://esolangs.org/wiki/Piet
- Esolang wiki「Piet++」: https://esolangs.org/wiki/Piet%2B%2B
- Esolang wiki「Piet++」の編集履歴: https://esolangs.org/w/index.php?title=Piet%2B%2B&action=history
- SourceForge「Piet++」（pietpp）: https://sourceforge.net/projects/pietpp/
- 同 Subversion リポジトリ: https://svn.code.sf.net/p/pietpp/code/trunk/
- PietPlus（SanguineL）: https://sanguinel.github.io/PietPlus/ 、https://github.com/SanguineL/PietPlus
- UltraPiet（Muratam）: https://github.com/Muratam/UltraPiet
- UltraPiet の wiki（仕様）: https://github.com/Muratam/UltraPiet/wiki
- Esolang wiki「Piet-Q」: https://esolangs.org/wiki/Piet-Q
- Esolang wiki「🅿🅸🅴🆃」: https://esolangs.org/wiki/%F0%9F%85%BF%F0%9F%85%B8%F0%9F%85%B4%F0%9F%86%83
- Esolang wiki「Pietfood」: https://esolangs.org/wiki/Pietfood
- Esolang wiki「pgmpiet」: https://esolangs.org/wiki/Pgmpiet
- pgmpiet のインタプリタ: https://github.com/iannmiui-png/pgmpiet
- Esolang wiki「Pgmpietoncracklang」: https://esolangs.org/wiki/Pgmpietoncracklang
- Esolang wiki「Pietfuck」: https://esolangs.org/wiki/Pietfuck
- Esolang wiki「Befunge」: https://esolangs.org/wiki/Befunge
- Esolang wiki「XKCD Random Number」: https://esolangs.org/wiki/XKCD_Random_Number
- Esolang wiki「Brainloller」: https://esolangs.org/wiki/Brainloller
- Esolang wiki「Braincopter」: https://esolangs.org/wiki/Braincopter
- Lode Vandevenne の難解言語のファイル: https://lodev.org/esolangs/
- Esolang wiki「Velato」: https://esolangs.org/wiki/Velato
- Esolang wiki「Floater」: https://esolangs.org/wiki/Floater
- Esolang wiki「Annoying Alice 2D」: https://esolangs.org/wiki/Annoying_Alice_2D
- Esolang wiki「Reso」: https://esolangs.org/wiki/Reso
- Esolang wiki「RandBow」: https://esolangs.org/wiki/RandBow
- Esolang wiki「Cbazyx」: https://esolangs.org/wiki/Cbazyx
- Esolang wiki「Letterfuck」: https://esolangs.org/wiki/Letterfuck
- Esolang wiki「Peet」: https://esolangs.org/wiki/Peet
- Esolang wiki「Category:Two-dimensional languages」: https://esolangs.org/wiki/Category:Two-dimensional_languages
- Esolang wiki「David Morgan-Mar」: https://esolangs.org/wiki/David_Morgan-Mar
- DM's Esoteric Programming Languages（David Morgan-Mar）: https://www.dangermouse.net/esoteric/
- 同 各言語のページ: https://www.dangermouse.net/esoteric/bit.html 、https://www.dangermouse.net/esoteric/chef.html 、https://www.dangermouse.net/esoteric/haifu.html 、https://www.dangermouse.net/esoteric/hq9plusplus.html 、https://www.dangermouse.net/esoteric/ook.html 、https://www.dangermouse.net/esoteric/whenever.html 、https://www.dangermouse.net/esoteric/zombie.html
- Interview with David Morgan-Mar（esoteric.codes、2015 年）: https://esoteric.codes/blog/david-morgan-mar
