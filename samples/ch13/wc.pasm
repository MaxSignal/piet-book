; 行数と文字数を数える（wc -l -c のようなもの）
        push 0          ; [L]
        push 0          ; [L C]
loop:
        push 0
        inc             ; [L C 0 c] または [L C 0]
        dup
        jz eof
        swap
        pop             ; [L C c]
        swap
        push 1
        add
        swap            ; [L C+1 c]
        push 10
        sub
        not             ; [L C f]        f = 1 なら改行
        swap            ; [L f C]
        bury 2          ; [C L f]
        add             ; [C L+f]
        swap            ; [L' C]
        jmp loop
eof:
        pop             ; [L C]
        swap
        outn            ; 行数
        push 32
        outc
        outn            ; 文字数
        push 10
        outc
