; 直前の文字との差だけを足し引きする
        push 72   ; 'H'
        dup
        outc
        dup
        push 29   ; +29 → 'e'
        add
        dup
        outc
        dup
        push 7    ; +7 → 'l'
        add
        dup
        outc
        dup
        ; 差 0 → 'l'
        dup
        outc
        dup
        push 3    ; +3 → 'o'
        add
        dup
        outc
        dup
        push 67   ; -67 → ','
        sub
        dup
        outc
        dup
        push 12   ; -12 → ' '
        sub
        dup
        outc
        dup
        push 55   ; +55 → 'W'
        add
        dup
        outc
        dup
        push 24   ; +24 → 'o'
        add
        dup
        outc
        dup
        push 3    ; +3 → 'r'
        add
        dup
        outc
        dup
        push 6    ; -6 → 'l'
        sub
        dup
        outc
        dup
        push 8    ; -8 → 'd'
        sub
        dup
        outc
        dup
        push 67   ; -67 → '!'
        sub
        dup
        outc
        dup
        push 23   ; -23 → '\n'
        sub
        dup
        outc
