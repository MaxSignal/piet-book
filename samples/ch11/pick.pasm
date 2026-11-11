; pick と bury の動作を確かめる
  push 1
  push 2
  push 3
  push 4         ; [1 2 3 4]
  pick 2         ; [1 2 3 4 2]
  outn           ; 2 を出力 → [1 2 3 4]
  push 9         ; [1 2 3 4 9]
  bury 2         ; [1 2 9 3 4]
  outn
  outn
  outn
  outn
  outn           ; 4 3 9 2 1
