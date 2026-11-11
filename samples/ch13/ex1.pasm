; 英大文字を小文字に変換する（EOF まで）
loop:
        push 0
        inc
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
        mul             ; [c f]
        push 32
        mul
        add             ; [c+32f]
        outc
        jmp loop
eof:
        halt
