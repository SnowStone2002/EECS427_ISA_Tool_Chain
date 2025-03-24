#!/usr/bin/env python3
import os
import sys
import unittest

# 将项目根目录添加到 sys.path，以便能够导入 src 包
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.disassembler import disassemble_file

class TestDisassembler(unittest.TestCase):
    def setUp(self):
        self.input_file = "tests/sample.hex"
        self.output_file = "tests/output_asm.asm"
        # 创建包含6条机器码的输入文件，每行4位十六进制数
        sample_hex = """0152
530A
8415
C2F8
43C5
4647
"""
        with open(self.input_file, "w", encoding="utf-8") as f:
            f.write(sample_hex)

    def tearDown(self):
        if os.path.exists(self.input_file):
            os.remove(self.input_file)
        if os.path.exists(self.output_file):
            os.remove(self.output_file)

    def test_disassembler(self):
        # 调用反汇编器，将输入 hex 文件转换为汇编代码文件
        disassemble_file(self.input_file, self.output_file)
        # 读取输出文件的内容，去除空行和首尾空白字符
        with open(self.output_file, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]

        # 预期的汇编码（对应之前汇编器生成的机器码）
        expected = [
            "ADD R1, R2",      # 对应 0152
            "ADDI R3, 0xA",    # 对应 530A
            "LSHI R4, -5",     # 对应 8415
            "BCOND 2, -8",     # 对应 C2F8
            "JCOND 3, R5",     # 对应 43C5
            "STOR R6, R7"      # 对应 4647
        ]
        self.assertEqual(lines, expected)

if __name__ == '__main__':
    unittest.main()
