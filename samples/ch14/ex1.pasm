; 99 Bottles of Beer（練習問題: 共通部分 " of beer" をサブルーチンに移した版）
; 「n bottles」を出力する部分を、戻り先番号 r を使って共有する
        push 99                 ; [n]
verse:
        dup
        push 1                  ; [n n 1]   戻り先 1
        jmp bottles
ret1:
        prints " on the wall, "
        dup
        push 2                  ; [n n 2]   戻り先 2
        jmp bottles
ret2:
        prints ".\nTake one down and pass it around, "
        push 1
        sub                     ; [n-1]
        dup
        push 3                  ; [n-1 n-1 3]  戻り先 3
        jmp bottles
ret3:
        prints " on the wall.\n\n"
        dup
        jnz verse               ; [n]
        pop
        prints "No more bottles of beer on the wall, no more bottles of beer.\n"
        prints "Go to the store and buy some more, 99 bottles of beer on the wall.\n"
        halt

; ---- サブルーチン bottles: [.. m r] → m に応じて出力し、r 番の戻り先へ
bottles:
        swap                    ; [r m]
        dup
        jz b0                   ; m = 0
        dup
        push 1
        sub
        jz b1                   ; m = 1
        outn
        prints " bottles"
        jmp ofbeer
b0:
        pop
        prints "no more bottles"
        jmp ofbeer
b1:
        outn
        prints " bottle"
ofbeer:
        prints " of beer"       ; 3 か所で共通の部分をここにまとめた
return:                         ; [r]
        dup
        push 1
        sub
        jz r1
        dup
        push 2
        sub
        jz r2
        pop
        jmp ret3
r1:
        pop
        jmp ret1
r2:
        pop
        jmp ret2
