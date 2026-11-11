; 入力から数字の文字だけを取り出して出力する
loop:
        push 0
        inc
        dup
        jz eof
        swap
        pop             ; [c]
        dup
        push 47
        gt              ; [c (c>47)]
        pick 1
        push 58
        swap
        gt              ; [c (c>47) (58>c)]
        mul             ; [c f]
        jnz digit
        pop             ; 数字以外は捨てる
        jmp loop
digit:
        outc
        jmp loop
eof:
        push 10
        outc
