#!/usr/bin/env python3
"""
EECS 427 Processor Simulator (Prototype)
- IMEM  : asm lines stored in a list
- DMEM  : 512 x 16-bit signed
- RegFile: 16 x 16-bit signed
- PSR   : flags F, N, Z  (Overflow, Negative, Zero)
- PC    : index into program_lines
- Stop conditions:
  1) PC out of range
  2) WAIT encountered
"""

import sys
import re

# 定义条件码助记符与数字的映射
cond_map = {
    "EQ": 0,   # Equal: Z=1
    "NE": 1,   # Not Equal: Z=0
    "CS": 2,   # Carry Set: C=1（若实现）
    "CC": 3,   # Carry Clear: C=0
    "HI": 4,   # Higher Than: L=1
    "LS": 5,   # Lower or Same: L=0
    "GT": 6,   # Greater Than: N=1
    "LE": 7,   # Less or Equal: N=0
    "FS": 8,   # Flag Set: F=1
    "FC": 9,   # Flag Clear: F=0
    "LO": 10,  # Lower Than: L=0 & Z=0
    "HS": 11,  # Higher or Same: L=1 or Z=1
    "LT": 12,  # Less Than: N=0 & Z=0
    "GE": 13,  # Greater or Equal: N=1 or Z=1
    "UC": 14,  # Unconditional: 必跳
    "NV": 15   # Never Jump: 不跳
}

class Simulator:
    def __init__(self):
        # 16个16位寄存器
        self.regs = [0] * 16
        # 512个16位有符号数
        self.dmem = [0] * 512
        # PSR标志 F（溢出）、N（负数）、Z（零）
        self.flagF = False
        self.flagN = False
        self.flagZ = False
        # 另外两个可能的标志，用于条件码（如果需要）
        self.flagC = False
        self.flagL = False
        # 程序计数器从0开始
        self.pc = 0
        # 存储asm代码行
        self.program_lines = []
        # 是否结束模拟
        self.halt = False

    def load_asm_file(self, asm_path):
        """
        读取asm文件内容到program_lines，去除注释和空行
        """
        with open(asm_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        for line in lines:
            line = line.split(";")[0].strip()
            if line:
                self.program_lines.append(line)

    def run(self):
        """
        主执行循环：逐行执行，直到PC超出范围或遇到WAIT
        """
        while not self.halt:
            if self.pc < 0 or self.pc >= len(self.program_lines):
                print(f"[SIM] PC {self.pc} out of range! Simulation stops.")
                break
            asm_line = self.program_lines[self.pc]
            print(f"\n[SIM] PC={self.pc}, executing: {asm_line}")
            self.execute_line(asm_line)
            if not self.halt:
                self.pc += 1
        self.dump_state()

    def execute_line(self, asm_line):
        """
        解析并执行一条汇编码指令，
        支持的指令:
          - ADD, SUB, CMP, AND, OR, XOR, MOV
          - ADDI, SUBI, CMPI, ANDI, ORI, XORI, MOVI
          - LSH, LSHI, LUI
          - LOAD, STOR
          - Bcond, Jcond, JAL, WAIT
        """
        # 去除注释
        line = asm_line.split(";")[0].strip()
        if not line:
            return

        tokens = re.split(r'[,\s]+', line)
        if not tokens:
            return
        mnemonic = tokens[0].upper()

        # 特殊指令 WAIT
        if mnemonic == "WAIT":
            print(f"[SIM] WAIT encountered at PC={self.pc}. Simulation stops.")
            self.halt = True
            return

        # -------------- 寄存器-寄存器型 --------------
        if mnemonic == "ADD":
            # ADD Rsrc, Rdest => Rdest = Rdest + Rsrc
            if len(tokens) != 3:
                print("[SIM] Syntax error in ADD (expected ADD Rsrc, Rdest)")
                return
            rdest = self.parse_reg(tokens[1])
            rsrc  = self.parse_reg(tokens[2])
            a = self.regs[rdest]
            b = self.regs[rsrc]
            result = a + b
            val_16 = self.to_16bit(result)
            self.regs[rdest] = val_16
            self.update_flags(val_16)
            self.check_overflow_add(a, b, result)
            self.debug_print(f"ADD => R{rdest} = {a} + {b} => {val_16}")

        elif mnemonic == "SUB":
            # SUB Rsrc, Rdest => Rdest = Rdest - Rsrc
            if len(tokens) != 3:
                print("[SIM] Syntax error in SUB (expected SUB Rsrc, Rdest)")
                return
            rdest = self.parse_reg(tokens[1])
            rsrc  = self.parse_reg(tokens[2])
            a = self.regs[rdest]
            b = self.regs[rsrc]
            result = a - b
            val_16 = self.to_16bit(result)
            self.regs[rdest] = val_16
            self.update_flags(val_16)
            self.check_overflow_sub(a, b, result)
            self.debug_print(f"SUB => R{rdest} = {a} - {b} => {val_16}")

        elif mnemonic == "CMP":
            # CMP Rsrc, Rdest => (Rdest - Rsrc)更新标志，不写回
            if len(tokens) != 3:
                print("[SIM] Syntax error in CMP (expected CMP Rsrc, Rdest)")
                return
            rdest = self.parse_reg(tokens[1])
            rsrc  = self.parse_reg(tokens[2])
            a = self.regs[rdest]
            b = self.regs[rsrc]
            result = a - b
            val_16 = self.to_16bit(result)
            self.update_flags(val_16)
            self.check_overflow_sub(a, b, result)
            self.debug_print(f"CMP => compare R{rdest}({a}) - R{rsrc}({b}) = {val_16} => flags updated")

        elif mnemonic == "AND":
            # AND Rsrc, Rdest => Rdest = Rdest & Rsrc
            if len(tokens) != 3:
                print("[SIM] Syntax error in AND (expected AND Rsrc, Rdest)")
                return
            rdest = self.parse_reg(tokens[1])
            rsrc  = self.parse_reg(tokens[2])
            a = self.regs[rdest]
            b = self.regs[rsrc]
            result = a & b
            val_16 = self.to_16bit(result)
            self.regs[rdest] = val_16
            self.update_flags(val_16)
            self.debug_print(f"AND => R{rdest} = {a} & {b} => {val_16}")

        elif mnemonic == "OR":
            # OR Rsrc, Rdest => Rdest = Rdest | Rsrc
            if len(tokens) != 3:
                print("[SIM] Syntax error in OR (expected OR Rsrc, Rdest)")
                return
            rdest = self.parse_reg(tokens[1])
            rsrc  = self.parse_reg(tokens[2])
            a = self.regs[rdest]
            b = self.regs[rsrc]
            result = a | b
            val_16 = self.to_16bit(result)
            self.regs[rdest] = val_16
            self.update_flags(val_16)
            self.debug_print(f"OR => R{rdest} = {a} | {b} => {val_16}")

        elif mnemonic == "XOR":
            # XOR Rsrc, Rdest => Rdest = Rdest ^ Rsrc
            if len(tokens) != 3:
                print("[SIM] Syntax error in XOR (expected XOR Rsrc, Rdest)")
                return
            rdest = self.parse_reg(tokens[1])
            rsrc  = self.parse_reg(tokens[2])
            a = self.regs[rdest]
            b = self.regs[rsrc]
            result = a ^ b
            val_16 = self.to_16bit(result)
            self.regs[rdest] = val_16
            self.update_flags(val_16)
            self.debug_print(f"XOR => R{rdest} = {a} ^ {b} => {val_16}")

        elif mnemonic == "MOV":
            # MOV Rsrc, Rdest => Rdest = Rsrc
            if len(tokens) != 3:
                print("[SIM] Syntax error in MOV (expected MOV Rsrc, Rdest)")
                return
            rdest = self.parse_reg(tokens[1])
            rsrc  = self.parse_reg(tokens[2])
            val = self.regs[rsrc]
            self.regs[rdest] = self.to_16bit(val)
            self.update_flags(self.regs[rdest])
            self.debug_print(f"MOV => R{rdest} = R{rsrc} ({val})")

        #-------------- 寄存器-立即数型指令 --------------
        elif mnemonic == "ADDI":
            # ADDI Rdest, imm => Rdest = Rdest + imm (有符号扩展)
            if len(tokens) != 3:
                print("[SIM] Syntax error in ADDI (expected ADDI Rdest, imm)")
                return
            rdest = self.parse_reg(tokens[1])
            imm = self.parse_imm(tokens[2])
            old_val = self.regs[rdest]
            result = old_val + imm
            val_16 = self.to_16bit(result)
            self.regs[rdest] = val_16
            self.update_flags(val_16)
            self.check_overflow_add(old_val, imm, result)
            self.debug_print(f"ADDI => R{rdest} = {old_val} + {imm} => {val_16}")

        elif mnemonic == "SUBI":
            # SUBI Rdest, imm => Rdest = Rdest - imm (有符号扩展)
            if len(tokens) != 3:
                print("[SIM] Syntax error in SUBI (expected SUBI Rdest, imm)")
                return
            rdest = self.parse_reg(tokens[1])
            imm = self.parse_imm(tokens[2])
            old_val = self.regs[rdest]
            result = old_val - imm
            val_16 = self.to_16bit(result)
            self.regs[rdest] = val_16
            self.update_flags(val_16)
            self.check_overflow_sub(old_val, imm, result)
            self.debug_print(f"SUBI => R{rdest} = {old_val} - {imm} => {val_16}")

        elif mnemonic == "CMPI":
            # CMPI Rdest, imm => (Rdest - imm)只更新标志
            if len(tokens) != 3:
                print("[SIM] Syntax error in CMPI (expected CMPI Rdest, imm)")
                return
            rdest = self.parse_reg(tokens[1])
            imm = self.parse_imm(tokens[2])
            a = self.regs[rdest]
            result = a - imm
            val_16 = self.to_16bit(result)
            self.update_flags(val_16)
            self.check_overflow_sub(a, imm, result)
            self.debug_print(f"CMPI => compare R{rdest}({a}) - {imm} => {val_16}")

        elif mnemonic == "ANDI":
            # ANDI Rdest, imm => Rdest = Rdest & zero_extend(imm)
            if len(tokens) != 3:
                print("[SIM] Syntax error in ANDI (expected ANDI Rdest, imm)")
                return
            rdest = self.parse_reg(tokens[1])
            imm = self.parse_imm(tokens[2]) & 0xFF
            old_val = self.regs[rdest]
            result = old_val & imm
            val_16 = self.to_16bit(result)
            self.regs[rdest] = val_16
            self.update_flags(val_16)
            self.debug_print(f"ANDI => R{rdest} = {old_val} & 0x{imm:02X} => {val_16}")

        elif mnemonic == "ORI":
            # ORI Rdest, imm => Rdest = Rdest | zero_extend(imm)
            if len(tokens) != 3:
                print("[SIM] Syntax error in ORI (expected ORI Rdest, imm)")
                return
            rdest = self.parse_reg(tokens[1])
            imm = self.parse_imm(tokens[2]) & 0xFF
            old_val = self.regs[rdest]
            result = old_val | imm
            val_16 = self.to_16bit(result)
            self.regs[rdest] = val_16
            self.update_flags(val_16)
            self.debug_print(f"ORI => R{rdest} = {old_val} | 0x{imm:02X} => {val_16}")

        elif mnemonic == "XORI":
            # XORI Rdest, imm => Rdest = Rdest ^ zero_extend(imm)
            if len(tokens) != 3:
                print("[SIM] Syntax error in XORI (expected XORI Rdest, imm)")
                return
            rdest = self.parse_reg(tokens[1])
            imm = self.parse_imm(tokens[2]) & 0xFF
            old_val = self.regs[rdest]
            result = old_val ^ imm
            val_16 = self.to_16bit(result)
            self.regs[rdest] = val_16
            self.update_flags(val_16)
            self.debug_print(f"XORI => R{rdest} = {old_val} ^ 0x{imm:02X} => {val_16}")

        elif mnemonic == "MOVI":
            # MOVI Rdest, imm => Rdest = zero_extend(imm)
            if len(tokens) != 3:
                print("[SIM] Syntax error in MOVI (expected MOVI Rdest, imm)")
                return
            rdest = self.parse_reg(tokens[1])
            imm = self.parse_imm(tokens[2]) & 0xFF
            val_16 = self.to_16bit(imm)
            self.regs[rdest] = val_16
            self.update_flags(val_16)
            self.debug_print(f"MOVI => R{rdest} = 0x{imm:02X} => {val_16}")

        #-------------- 移位指令 --------------
        elif mnemonic == "LSH":
            # LSH Rsrc, Rdest => Rdest = Rdest << Rsrc (仅正移位)
            if len(tokens) != 3:
                print("[SIM] Syntax error in LSH (expected LSH Rsrc, Rdest)")
                return
            rdest = self.parse_reg(tokens[1])
            rsrc = self.parse_reg(tokens[2])
            shift_val = self.regs[rsrc]
            if shift_val < 0:
                # 当负数时取无符号低4位
                shift_val = shift_val & 0xF
                print(f"[SIM] LSH negative shift adjusted to {shift_val}")
            old_val = self.regs[rdest]
            result = old_val << shift_val
            val_16 = self.to_16bit(result)
            self.regs[rdest] = val_16
            self.update_flags(val_16)
            self.debug_print(f"LSH => R{rdest} = {old_val} << {shift_val} => {val_16}")

        elif mnemonic == "LSHI":
            # LSHI Rdest, imm => Rdest = Rdest << imm (仅支持正移位)
            if len(tokens) != 3:
                print("[SIM] Syntax error in LSHI (expected LSHI Rdest, imm)")
                return
            rdest = self.parse_reg(tokens[1])
            shift_amt = self.parse_imm(tokens[2])
            if shift_amt < 0:
                print(f"[SIM] LSHI negative shift {shift_amt} not supported.")
                return
            old_val = self.regs[rdest]
            result = old_val << shift_amt
            val_16 = self.to_16bit(result)
            self.regs[rdest] = val_16
            self.update_flags(val_16)
            self.debug_print(f"LSHI => R{rdest} = {old_val} << {shift_amt} => {val_16}")

        elif mnemonic == "LUI":
            # LUI Rdest, imm => Rdest = imm << 8
            if len(tokens) != 3:
                print("[SIM] Syntax error in LUI (expected LUI Rdest, imm)")
                return
            rdest = self.parse_reg(tokens[1])
            imm = self.parse_imm(tokens[2]) & 0xFF
            val_16 = self.to_16bit(imm << 8)
            self.regs[rdest] = val_16
            self.update_flags(val_16)
            self.debug_print(f"LUI => R{rdest} = 0x{imm:02X} << 8 => {val_16}")

        #-------------- 内存访问指令 --------------
        elif mnemonic == "LOAD":
            # LOAD Rdest, Rsrc => Rdest = DMEM[Rsrc]
            if len(tokens) != 3:
                print("[SIM] Syntax error in LOAD (expected LOAD Rdest, Rsrc)")
                return
            rdest = self.parse_reg(tokens[1])
            rsrc = self.parse_reg(tokens[2])
            addr = self.regs[rsrc] & 0x1FF
            val_16 = self.to_16bit(self.dmem[addr])
            self.regs[rdest] = val_16
            self.update_flags(val_16)
            self.debug_print(f"LOAD => R{rdest} = DMEM[{addr}] => {val_16}")

        elif mnemonic == "STOR":
            # STOR Rsrc, Rdest => DMEM[Rdest] = Rsrc
            if len(tokens) != 3:
                print("[SIM] Syntax error in STOR (expected STOR Rsrc, Rdest)")
                return
            rsrc = self.parse_reg(tokens[1])
            rdest = self.parse_reg(tokens[2])
            addr = self.regs[rdest] & 0x1FF
            self.dmem[addr] = self.to_16bit(self.regs[rsrc])
            self.debug_print(f"STOR => DMEM[{addr}] = R{rsrc} ({self.regs[rsrc]})")

        #-------------- 分支、跳转指令 --------------
        elif mnemonic == "BCOND":
            # Bcond cond, disp => if(check_condition(cond)) pc += disp
            if len(tokens) != 3:
                print("[SIM] Syntax error in Bcond (expected Bcond cond, disp)")
                return
            # 解析条件码：支持助记符
            cond_token = tokens[1].upper()
            try:
                cond_val = cond_map[cond_token]
            except KeyError:
                cond_val = self.parse_imm(tokens[1])
            # 解析位移：这里直接当作立即数（应为8位2's complement）
            disp = self.parse_imm(tokens[2])
            if self.check_condition(cond_val):
                old_pc = self.pc
                self.pc += disp
                self.debug_print(f"BCOND => cond {cond_token} true, jump from {old_pc} to {self.pc+1}")
            else:
                self.debug_print(f"BCOND => cond {cond_token} false, no jump")

        elif mnemonic == "JCOND":
            # Jcond cond, Rsrc => if(check_condition(cond)) pc = Rsrc
            if len(tokens) != 3:
                print("[SIM] Syntax error in Jcond (expected Jcond cond, Rsrc)")
                return
            cond_token = tokens[1].upper()
            try:
                cond_val = cond_map[cond_token]
            except KeyError:
                cond_val = self.parse_imm(tokens[1])
            rsrc = self.parse_reg(tokens[2])
            if self.check_condition(cond_val):
                old_pc = self.pc
                new_pc = self.regs[rsrc]
                self.debug_print(f"JCOND => cond {cond_token} true, jump from {old_pc} to {new_pc}")
            else:
                self.debug_print(f"JCOND => cond {cond_token} false, no jump")

        elif mnemonic == "JAL":
            # JAL Rdest, Rsrc => Rdest = PC+1, PC = Rsrc
            if len(tokens) != 3:
                print("[SIM] Syntax error in JAL (expected JAL Rdest, Rsrc)")
                return
            rdest = self.parse_reg(tokens[1])
            rsrc = self.parse_reg(tokens[2])
            link_val = self.pc + 1
            self.regs[rdest] = self.to_16bit(link_val)
            new_pc = self.regs[rsrc]
            old_pc = self.pc
            self.debug_print(f"JAL => R{rdest} = {link_val}, jump from {old_pc} to {new_pc}")

        else:
            print(f"[SIM] Unsupported instruction: {mnemonic}")

    # --------------------- 工具函数 ---------------------

    def parse_reg(self, token):
        token = token.strip().upper()
        if not token.startswith('R'):
            raise ValueError(f"Invalid register token: {token}")
        idx = int(token[1:])
        if idx < 0 or idx > 15:
            raise ValueError(f"Register index out of range: {idx}")
        return idx

    def parse_imm(self, token):
        token = token.strip().upper()
        if token.startswith("0X"):
            return int(token, 16)
        else:
            return int(token, 10)

    def to_16bit(self, val):
        masked = val & 0xFFFF
        if masked & 0x8000:
            return masked - 0x10000
        else:
            return masked

    def update_flags(self, val_16):
        self.flagN = (val_16 < 0)
        self.flagZ = (val_16 == 0)
        # flagF 由具体运算判断

    def check_overflow_add(self, a, b, result):
        if (a >= 0 and b >= 0 and result < 0) or (a < 0 and b < 0 and result >= 0):
            self.flagF = True
        else:
            self.flagF = False

    def check_overflow_sub(self, a, b, result):
        if ((a ^ b) >= 0) and ((a ^ result) < 0):
            self.flagF = True
        else:
            self.flagF = False

    def check_condition(self, cond):
        # cond 是数字0..15
        if cond == 0:   # EQ
            return self.flagZ
        elif cond == 1: # NE
            return not self.flagZ
        elif cond == 2: # CS
            return self.flagC
        elif cond == 3: # CC
            return not self.flagC
        elif cond == 4: # HI
            return self.flagL
        elif cond == 5: # LS
            return not self.flagL
        elif cond == 6: # GT
            return self.flagN
        elif cond == 7: # LE
            return not self.flagN
        elif cond == 8: # FS
            return self.flagF
        elif cond == 9: # FC
            return not self.flagF
        elif cond == 10: # LO
            return (not self.flagL) and (not self.flagZ)
        elif cond == 11: # HS
            return self.flagL or self.flagZ
        elif cond == 12: # LT
            return (not self.flagN) and (not self.flagZ)
        elif cond == 13: # GE
            return self.flagN or self.flagZ
        elif cond == 14: # UC
            return True
        elif cond == 15:
            return False
        else:
            return False

    def debug_print(self, msg):
        print(f"  [DEBUG] {msg}")

    def dump_state(self):
        print("\n----- Simulation Finished -----")
        print("Registers:")
        for i in range(16):
            print(f"  R{i} = {self.regs[i]}")
        print(f"Flags: F={self.flagF}, N={self.flagN}, Z={self.flagZ}")
        # 可打印部分 DMEM 内容

def main():
    if len(sys.argv) < 2:
        print("Usage: python simulate.py input.asm")
        sys.exit(1)

    sim = Simulator()
    sim.load_asm_file(sys.argv[1])
    sim.run()

if __name__ == "__main__":
    main()
