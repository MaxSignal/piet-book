; 電卓に累乗 ^ を加えた版
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
        dup
        push 94         ; '^'
        sub
        jz power
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
        jmp print
power:
        pop             ; [a b]
        push 1          ; [a b r]
ploop:
        pick 1
        jz pdone        ; b = 0 なら終わり
        pick 2
        mul             ; [a b r*a]
        swap
        push 1
        sub
        swap            ; [a b-1 r]
        jmp ploop
pdone:
        bury 2
        pop
        pop             ; [r]
print:
        outn
        push 10
        outc
