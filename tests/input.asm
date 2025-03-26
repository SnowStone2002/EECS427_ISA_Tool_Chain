; input.asm
; Demonstration of labels, condition mnemonics, and some basic instructions.

start:
    ; 初始化 R0 = 5, R1 = 0
    MOVI R0, 0x5
    MOVI R1, 0x0

loop:
    ; R1 = R1 + 1
    ADDI R1, 1

    ; 比较 R0 和 R1，相当于 (R0 - R1) 更新标志
    CMP R1, R0

    ; 如果 R0 == R1 则跳转到 finish
    Bcond EQ, finish

    ; 如果 R0 != R1 则回到 loop
    Bcond NE, loop

    ; 理论上永远不会执行到这里
    ; 可以放一些“不会执行”的指令以做测试
    MOVI R2, 0xFF

finish:
    ; 此处可以再做点事情
    ; 示例：R1 = R1 - R0
    SUB R0, R1

    ; 最后无条件跳转到 R2 中的地址
    ; (需要你在模拟器里决定 R2 里是什么，或运行时再写)
    Jcond UC, R2

    ; 也可以放 WAIT、STOR、LOAD 等看你需求
