; 文字を逆順に積んでから、0 が出るまで出力するループ
        push 0          ; 番兵
        push 10   ; '\n'
        push 33   ; '!'
        push 100  ; 'd'
        push 108  ; 'l'
        push 114  ; 'r'
        push 111  ; 'o'
        push 87   ; 'W'
        push 32   ; ' '
        push 44   ; ','
        push 111  ; 'o'
        push 108  ; 'l'
        push 108  ; 'l'
        push 101  ; 'e'
        push 72   ; 'H'
loop:
        dup
        jz done         ; 番兵の 0 なら終わり
        outc
        jmp loop
done:
        halt
