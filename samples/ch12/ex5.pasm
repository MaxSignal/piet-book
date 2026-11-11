; 階乗（npiet でも 64 ビットの範囲で正しく計算できる版）
; roll で動かす値が、いつも小さい n になるようにする
        push 1          ; [acc]
        inn             ; [acc n]
loop:
        dup
        jz done         ; [acc n]
        dup             ; [acc n n]
        push 3
        push 1
        roll            ; [n acc n]      正の回数: 先頭の n を沈める
        mul             ; [n acc*n]
        push 2
        push -1
        roll            ; [acc*n n]      負の回数: 底側の n を持ち上げる
        push 1
        sub             ; [acc n-1]
        jmp loop
done:
        pop             ; [acc]
        outn
        push 10
        outc
