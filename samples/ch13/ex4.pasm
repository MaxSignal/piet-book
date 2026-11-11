; NUL 文字も通す cat（番兵に -1 を使う）
loop:
        push -1         ; [-1]           どの文字コードとも重ならない番兵
        inc             ; [-1 c] または [-1]
        dup
        push 1
        add             ; [.. top+1]
        jz eof          ; 先頭が -1 なら EOF
        swap
        pop             ; [c]
        outc
        jmp loop
eof:
        halt
