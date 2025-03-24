#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import unittest
from src.assembler import assemble_file

class TestAssembler(unittest.TestCase):
    def setUp(self):
        # 定义测试输入和输出文件路径
        self.input_file = "tests/sample.asm"
        self.output_file = "tests/output.hex"
        # 写入示例汇编代码到 sample.asm
        asm_content = """
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
"""
        with open(self.input_file, "w", encoding="utf-8") as f:
            f.write(asm_content)

    # def tearDown(self):
    #     # 清理测试生成的文件
    #     if os.path.exists(self.input_file):
    #         os.remove(self.input_file)
    #     if os.path.exists(self.output_file):
    #         os.remove(self.output_file)

    def test_assembler(self):
        # 调用汇编器，处理 sample.asm 生成 output.hex
        assemble_file(self.input_file, self.output_file)
        # 读取输出文件的每行结果（去掉空行）
        with open(self.output_file, "r") as f:
            lines = [line.strip() for line in f if line.strip()]

        # 下面计算预期的机器码：
        #
        # 1. ADD R1, R2:
        #    RR格式：machine_code = (opcode<<12) | (Rdest<<8) | (ext<<4) | Rsrc
        #    对于 ADD: opcode = 0b0000, ext = 0b0101, Rdest=1, Rsrc=2
        #    机器码 = (0 << 12) | (1<<8) | (0x5<<4) | 2 = 0x0100 + 0x50 + 0x2 = 0x0152
        #
        # 2. ADDI R3, 10:
        #    RI格式：machine_code = (opcode<<12) | (Rdest<<8) | imm
        #    对于 ADDI: opcode = 0b0101, Rdest=3, imm=10 (0x0A)
        #    机器码 = (0x5<<12) | (3<<8) | 0x0A = 0x5000 + 0x0300 + 0x0A = 0x530A
        #
        # 3. LSHI R4, -5:
        #    RI4格式：machine_code = (opcode<<12) | (Rdest<<8) | (s<<4) | imm
        #    对于 LSHI: opcode = 0b1000, Rdest=4, 对于 -5，取绝对值5且 s=1
        #    机器码 = (0x8<<12) | (4<<8) | (1<<4) | 5 = 0x8000 + 0x0400 + 0x10 + 5 = 0x8415
        #
        # 4. Bcond 2, -8:
        #    Bcond格式：machine_code = (opcode<<12) | (cond<<8) | disp
        #    对于 Bcond: opcode = 0b1100, cond=2, disp = -8（8位2's complement: 256-8=248，即0xF8）
        #    机器码 = (0xC<<12) | (2<<8) | 0xF8 = 0xC000 + 0x0200 + 0xF8 = 0xC2F8
        #
        # 5. Jcond 3, R5:
        #    Jcond格式：machine_code = (opcode<<12) | (cond<<8) | (ext<<4) | Rtarget
        #    对于 Jcond: opcode = 0b0100, ext = 0b1100, cond=3, Rtarget=5
        #    机器码 = (0x4<<12) | (3<<8) | (0xC<<4) | 5 = 0x4000 + 0x0300 + 0xC0 + 5 = 0x43C5
        #
        # 6. STOR R6, R7:
        #    RS格式：machine_code = (opcode<<12) | (Rsrc<<8) | (ext<<4) | Raddr
        #    对于 STOR: opcode = 0b0100, ext = 0b0100, Rsrc=6, Raddr=7
        #    机器码 = (0x4<<12) | (6<<8) | (0x4<<4) | 7 = 0x4000 + 0x0600 + 0x40 + 7 = 0x4647
        expected = [
            "0152",
            "530A",
            "8415",
            "C2F8",
            "43C5",
            "4647"
        ]
        self.assertEqual(lines, expected)

if __name__ == '__main__':
    unittest.main()
