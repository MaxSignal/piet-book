"""ean13.py -- EAN-13（JAN／ISBN／ISDN）バーコードを SVG で描く"""
L = ["0001101", "0011001", "0010011", "0111101", "0100011", "0110001", "0101111", "0111011", "0110111", "0001011"]
G = ["0100111", "0110011", "0011011", "0100001", "0011101", "0111001", "0000101", "0010001", "0001001", "0010111"]
R = ["1110010", "1100110", "1101100", "1000010", "1011100", "1001110", "1010000", "1000100", "1001000", "1110100"]
PARITY = ["LLLLLL", "LLGLGG", "LLGGLG", "LLGGGL", "LGLLGG", "LGGLLG", "LGGGLL", "LGLGLG", "LGLGGL", "LGGLGL"]


def check_digit(d12):
    s = sum(int(c) * (1 if i % 2 == 0 else 3) for i, c in enumerate(d12))
    return str((10 - s % 10) % 10)


def full(code):
    code = "".join(c for c in code if c.isdigit())
    if len(code) == 12:
        code += check_digit(code)
    assert len(code) == 13 and code[12] == check_digit(code[:12]), f"チェックディジットが違います: {code}"
    return code


def bits(code):
    code = full(code)
    first, left, right = int(code[0]), code[1:7], code[7:]
    s = "101"
    for p, c in zip(PARITY[first], left):
        s += (L if p == "L" else G)[int(c)]
    s += "01010"
    for c in right:
        s += R[int(c)]
    return s + "101"


def decode(b):
    """検算用: ビット列から 13 桁を復元する"""
    assert b[:3] == "101" and b[45:50] == "01010" and b[-3:] == "101"
    left = [b[3 + 7 * i: 10 + 7 * i] for i in range(6)]
    right = [b[50 + 7 * i: 57 + 7 * i] for i in range(6)]
    par, ld = "", ""
    for x in left:
        if x in L:
            par += "L"; ld += str(L.index(x))
        else:
            par += "G"; ld += str(G.index(x))
    return str(PARITY.index(par)) + ld + "".join(str(R.index(x)) for x in right)


def svg(code, module=0.33, height=15.0, font="Noto Sans Mono, monospace"):
    """1 モジュール 0.33mm（標準倍率）。左右に余白、下に数字"""
    code = full(code)
    b = bits(code)
    assert decode(b) == code
    q = 11   # 左の余白（モジュール）
    w = (q + 95 + 7) * module
    h = height + 3.2
    rects = []
    for i, c in enumerate(b):
        if c == "1":
            guard = i < 3 or 45 <= i < 50 or i >= 92
            rects.append(f'<rect x="{(q + i) * module:.3f}" y="0" width="{module:.3f}" height="{height + (1.6 if guard else 0):.2f}" fill="#000"/>')
    t = lambda x, s: f'<text x="{x:.2f}" y="{h - 0.2:.2f}" font-size="2.6" font-family="{font}" text-anchor="middle">{s}</text>'
    texts = [t(5 * module, code[0])]
    texts += [t((q + 3 + 7 * i + 3.5) * module, code[1 + i]) for i in range(6)]
    texts += [t((q + 50 + 7 * i + 3.5) * module, code[7 + i]) for i in range(6)]
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w:.2f}mm" height="{h:.2f}mm" viewBox="0 0 {w:.3f} {h:.3f}">'
            f'<rect width="{w:.3f}" height="{h:.3f}" fill="#fff"/>{"".join(rects)}{"".join(texts)}</svg>')


if __name__ == "__main__":
    import sys
    c = full(sys.argv[1])
    print(c, decode(bits(c)) == c)
