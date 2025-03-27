start:
    ; R0 = 0 (F0)
    ; R1 = 1 (F1)
    ; R2 = memory pointer
    ; R6 = 50 (upper limit)
    MOVI R0, 0
    MOVI R1, 1
    MOVI R2, 0
    MOVI R6, 50

fibo_loop:
    CMP R6, R0
    Bcond GT, done_fibo
    WAIT

    STOR R0, R2

    MOV R3, R0      
    ADD R3, R1      ; R3 = R0 + R1
    MOV R0, R1
    MOV R1, R3

    ADDI R2, 1
    Bcond UC, fibo_loop
    WAIT

done_fibo:
    ; 存入哨兵值 255，告诉后面循环“读到我就停”
    MOVI R4, 255
    STOR R4, R2

    ; 重置 R2，准备从内存第 0 单元开始读
    MOVI R2, 0

multiply_loop:
    LOAD R4, R2

    ; 需要先把 255 装到某个寄存器（比如 R7），再做 CMP
    MOVI R7, 255
    CMP R4, R7
    Bcond EQ, finish
    WAIT

    ; 用加法模拟 乘以 8
    ADD R4, R4      ; 2x
    ADD R4, R4      ; 4x
    ADD R4, R4      ; 8x

    STOR R4, R2

    ADDI R2, 1
    Bcond UC, multiply_loop
    WAIT

finish:
    MOVI R0, 0
    MOVI R1, 0
    MOVI R2, 0
    MOVI R3, 0
    MOVI R4, 0
    MOVI R5, 0
    MOVI R6, 0
    MOVI R7, 0