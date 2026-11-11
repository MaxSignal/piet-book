; 「数 演算子 数」を読んで計算する電卓（+ - * / %）
        inn             ; [a]
        inc             ; [a op]
        inn             ; [a op b]
        swap            ; [a b op]
        dup
        push 43         ; '+'
        sub
        jz plus
        dup
        push 45         ; '-'
        sub
        jz minus
        dup
        push 42         ; '*'
        sub
        jz times
        dup
        push 47         ; '/'
        sub
        jz divide
        dup
        push 37         ; '%'
        sub
        jz modulo
        prints "?\n"    ; 知らない演算子
        halt
plus:
        pop
        add
        jmp print
minus:
        pop
        sub
        jmp print
times:
        pop
        mul
        jmp print
divide:
        pop
        div
        jmp print
modulo:
        pop
        mod
print:
        outn
        push 10
        outc
