; 入力を大文字に変換して出力する（EOF まで）
loop:
        push 0          ; [0]            EOF 検出用の番兵
        inc             ; [0 c] または [0]
        dup
        jz eof          ; 何も読めなかった
        swap
        pop             ; [c]
        dup             ; [c c]
        push 96
        gt              ; [c (c>96)]
        pick 1          ; [c f1 c]
        push 123
        swap            ; [c f1 123 c]
        gt              ; [c f1 (123>c)]
        mul             ; [c f]          f = 1 なら英小文字
        push 32
        mul             ; [c 32f]
        sub             ; [c-32f]
        outc
        jmp loop
eof:
        halt
