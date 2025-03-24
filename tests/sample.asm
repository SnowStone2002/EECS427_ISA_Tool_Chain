
; 测试汇编文件 sample.asm

; RR 格式测试：ADD R1, R2
ADD R1, R2

; RI 格式测试：ADDI R3, 10
ADDI R3, 10

; RI4 格式测试：LSHI R4, -5
LSHI R4, -5

; Bcond 格式测试：Bcond 2, -8
Bcond 2, -8

; Jcond 格式测试：Jcond 3, R5
Jcond 3, R5

; RS 格式测试：STOR R6, R7
STOR R6, R7
