; ROT13: 英字を 13 文字ずらす（EOF まで）
loop:
        push 0
        inc             ; [0 c] または [0]
        dup
        jz eof
        swap
        pop             ; [c]
        dup
        push 64
        gt              ; [c (c>64)]
        pick 1
        push 91
        swap
        gt              ; [c (c>64) (91>c)]
        mul             ; [c U]          U = 1 なら英大文字
        jnz upper       ; [c]
        dup
        push 96
        gt
        pick 1
        push 123
        swap
        gt
        mul             ; [c L]          L = 1 なら英小文字
        jnz lower       ; [c]
        outc            ; 英字以外はそのまま
        jmp loop
upper:
        push 52
        sub             ; [c-65+13]
        push 26
        mod
        push 65
        add
        outc
        jmp loop
lower:
        push 84
        sub             ; [c-97+13]
        push 26
        mod
        push 97
        add
        outc
        jmp loop
eof:
        halt
