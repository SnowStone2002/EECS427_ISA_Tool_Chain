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

class Simulator:
    def __init__(self):
        # 16个16位寄存器（用Python int存储，但每次写回时需取16位范围）
        self.regs = [0] * 16
        # 512个16位有符号数，地址范围0~511
        self.dmem = [0] * 512
        # 程序状态寄存器（F=溢出标志, N=负数标志, Z=零标志）
        # 可以用布尔或0/1来表示，也可以合并到一个整数位域中
        self.flagF = False  # 溢出（overflow）
        self.flagN = False  # 负数（negative）
        self.flagZ = False  # 零（zero）
        # PC从0开始
        self.pc = 0
        # 程序存储：直接存asm的行
        self.program_lines = []

        # 是否结束模拟
        self.halt = False

    def load_asm_file(self, asm_path):
        """
        将asm文件的内容存到 self.program_lines 中，去掉注释和空行。
        """
        with open(asm_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        # 去除注释和空行
        for line in lines:
            line = line.split(";")[0].strip()
            if line:
                self.program_lines.append(line)

    def run(self):
        """
        主执行循环：一直执行，直到 pc 超过范围或者遇到 WAIT 指令。
        """
        while not self.halt:
            if self.pc < 0 or self.pc >= len(self.program_lines):
                print(f"[SIM] PC {self.pc} out of range! Simulation stops.")
                break

            asm_line = self.program_lines[self.pc]
            print(f"\n[SIM] PC={self.pc}, executing: {asm_line}")
            self.execute_line(asm_line)
            
            # 如果还没停，就PC + 1
            if not self.halt:
                self.pc += 1

        # 打印最终状态
        self.dump_state()
        
    def execute_line(self, asm_line):
        """
        解析并执行单条汇编码指令，
        覆盖 Verilog 宏定义中列出的所有指令:
            - ADD, SUB, CMP, AND, OR, XOR, MOV
            - ADDI, SUBI, CMPI, ANDI, ORI, XORI, MOVI
            - LSH, LSHI, LUI
            - LOAD, STOR
            - Bcond, Jcond, JAL
        """
        import re

        # 去除注释和空白
        line = asm_line.split(";")[0].strip()
        if not line:
            return  # 空行或注释行直接跳过
        
        # 分割指令和操作数
        tokens = re.split(r'[,\s]+', line)
        if not tokens:
            return
        
        mnemonic = tokens[0].upper()

        #-------------------------
        # 1) 寄存器-寄存器型指令
        #-------------------------
        if mnemonic == "ADD":
            # 格式: ADD Rsrc, Rdest => Rdest = Rdest + Rsrc
            if len(tokens) != 3:
                print("[SIM] Syntax error in ADD (expected ADD Rsrc, Rdest)")
                return
            rdest = self.parse_reg(tokens[1])
            rsrc = self.parse_reg(tokens[2])
            a = self.regs[rdest]
            b = self.regs[rsrc]
            result = a + b
            val_16 = self.to_16bit(result)
            self.regs[rdest] = val_16
            self.update_flags(val_16)
            self.check_overflow_add(a, b, result)
            self.debug_print(f"ADD => R{rdest} = {a} + {b} => {val_16}")

        elif mnemonic == "SUB":
            # 格式: SUB Rsrc, Rdest => Rdest = Rdest - Rsrc
            if len(tokens) != 3:
                print("[SIM] Syntax error in SUB (expected SUB Rsrc, Rdest)")
                return
            rdest = self.parse_reg(tokens[1])
            rsrc = self.parse_reg(tokens[2])
            a = self.regs[rdest]
            b = self.regs[rsrc]
            result = a - b
            val_16 = self.to_16bit(result)
            self.regs[rdest] = val_16
            self.update_flags(val_16)
            self.check_overflow_sub(a, b, result)
            self.debug_print(f"SUB => R{rdest} = {a} - {b} => {val_16}")

        elif mnemonic == "CMP":
            # 格式: CMP Rsrc, Rdest => (Rdest - Rsrc)只更新标志，不写回
            if len(tokens) != 3:
                print("[SIM] Syntax error in CMP (expected CMP Rsrc, Rdest)")
                return
            rdest = self.parse_reg(tokens[1])
            rsrc = self.parse_reg(tokens[2])
            a = self.regs[rdest]
            b = self.regs[rsrc]
            result = a - b
            val_16 = self.to_16bit(result)
            self.update_flags(val_16)
            self.check_overflow_sub(a, b, result)
            self.debug_print(f"CMP => compare R{rdest}({a}) - R{rsrc}({b}) = {val_16} => flags updated")

        elif mnemonic == "AND":
            # 格式: AND Rsrc, Rdest => Rdest = Rdest & Rsrc
            if len(tokens) != 3:
                print("[SIM] Syntax error in AND (expected AND Rsrc, Rdest)")
                return
            rdest = self.parse_reg(tokens[1])
            rsrc = self.parse_reg(tokens[2])
            a = self.regs[rdest]
            b = self.regs[rsrc]
            result = a & b
            val_16 = self.to_16bit(result)
            self.regs[rdest] = val_16
            self.update_flags(val_16)  # 不改变F
            self.debug_print(f"AND => R{rdest} = {a} & {b} => {val_16}")

        elif mnemonic == "OR":
            # OR Rsrc, Rdest => Rdest = Rdest | Rsrc
            if len(tokens) != 3:
                print("[SIM] Syntax error in OR (expected OR Rsrc, Rdest)")
                return
            rdest = self.parse_reg(tokens[1])
            rsrc = self.parse_reg(tokens[2])
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
            rsrc = self.parse_reg(tokens[2])
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
            rsrc = self.parse_reg(tokens[2])
            val = self.regs[rsrc]
            self.regs[rdest] = self.to_16bit(val)
            self.update_flags(self.regs[rdest])
            self.debug_print(f"MOV => R{rdest} = R{rsrc} ({val})")

        #-------------------------
        # 2) 寄存器-立即数型指令
        #-------------------------
        elif mnemonic == "ADDI":
            # ADDI Rdest, imm => Rdest = Rdest + imm(有符号扩展)
            if len(tokens) != 3:
                print("[SIM] Syntax error in ADDI (expected ADDI Rdest, imm)")
                return
            rdest = self.parse_reg(tokens[1])
            imm = self.parse_imm(tokens[2])  # 自行确保符号扩展
            old_val = self.regs[rdest]
            result = old_val + imm
            val_16 = self.to_16bit(result)
            self.regs[rdest] = val_16
            self.update_flags(val_16)
            self.check_overflow_add(old_val, imm, result)
            self.debug_print(f"ADDI => R{rdest} = {old_val} + {imm} => {val_16}")

        elif mnemonic == "SUBI":
            # SUBI Rdest, imm => Rdest = Rdest - imm(有符号扩展)
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
            imm = self.parse_imm(tokens[2]) & 0xFF  # 零扩展8位
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

        #-------------------------
        # 3) 移位指令
        #-------------------------
        elif mnemonic == "LSH":
            # LSH Rsrc, Rdest => Rdest 左移 Rsrc(可能只支持正数)
            if len(tokens) != 3:
                print("[SIM] Syntax error in LSH (expected LSH Rsrc, Rdest)")
                return
            rdest = self.parse_reg(tokens[1])
            rsrc = self.parse_reg(tokens[2])
            shift_val = self.regs[rsrc]
            if shift_val < 0:
                print(f"[SIM] LSH negative shift {shift_val} not supported in baseline!")
                return
            old_val = self.regs[rdest]
            result = old_val << shift_val
            val_16 = self.to_16bit(result)
            self.regs[rdest] = val_16
            self.update_flags(val_16)
            self.debug_print(f"LSH => R{rdest} << {shift_val} => {val_16}")

        elif mnemonic == "LSHI":
            # LSHI Rdest, imm => Rdest 左移 imm (imm可能-15..+15,看需求)
            if len(tokens) != 3:
                print("[SIM] Syntax error in LSHI (expected LSHI Rdest, imm)")
                return
            rdest = self.parse_reg(tokens[1])
            shift_amt = self.parse_imm(tokens[2])  # 可能是负数 => 右移?
            if shift_amt < 0:
                print(f"[SIM] LSHI negative shift {shift_amt} not supported.")
                return
            old_val = self.regs[rdest]
            result = old_val << shift_amt
            val_16 = self.to_16bit(result)
            self.regs[rdest] = val_16
            self.update_flags(val_16)
            self.debug_print(f"LSHI => R{rdest} << {shift_amt} => {val_16}")

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

        #-------------------------
        # 4) 内存访问指令
        #-------------------------
        elif mnemonic == "LOAD":
            # LOAD Rdest, Rsrc => Rdest = dmem[Rsrc]
            if len(tokens) != 3:
                print("[SIM] Syntax error in LOAD (expected LOAD Rdest, Rsrc)")
                return
            rdest = self.parse_reg(tokens[1])
            raddr = self.parse_reg(tokens[2])
            addr = self.regs[raddr] & 0x1FF  # 512=2^9
            val_16 = self.to_16bit(self.dmem[addr])
            self.regs[rdest] = val_16
            self.update_flags(val_16)
            self.debug_print(f"LOAD => R{rdest} = DMEM[{addr}] => {val_16}")

        elif mnemonic == "STOR":
            # STOR Rsrc, Rdest => dmem[Rdest] = Rsrc
            if len(tokens) != 3:
                print("[SIM] Syntax error in STOR (expected STOR Rsrc, Rdest)")
                return
            rsrc = self.parse_reg(tokens[1])
            raddr = self.parse_reg(tokens[2])
            addr = self.regs[raddr] & 0x1FF
            self.dmem[addr] = self.to_16bit(self.regs[rsrc])
            self.debug_print(f"STOR => DMEM[{addr}] = R{rsrc} ({self.regs[rsrc]})")

        #-------------------------
        # 5) 分支、跳转指令
        #-------------------------
        elif mnemonic == "BCOND":
            # Bcond cond, disp => if(check_condition(cond)) pc += disp
            if len(tokens) != 3:
                print("[SIM] Syntax error in Bcond (expected Bcond cond, disp)")
                return
            cond = self.parse_imm(tokens[1])
            disp = self.parse_imm(tokens[2])  # 符号扩展8位
            if self.check_condition(cond):
                old_pc = self.pc
                self.pc += disp
                self.pc -= 1
                self.debug_print(f"Bcond => jump from {old_pc} to {self.pc+1}")

        elif mnemonic == "JCOND":
            # Jcond cond, Rsrc => if(check_condition(cond)) pc = Rsrc
            if len(tokens) != 3:
                print("[SIM] Syntax error in Jcond (expected Jcond cond, Rsrc)")
                return
            cond = self.parse_imm(tokens[1])
            rsrc = self.parse_reg(tokens[2])
            if self.check_condition(cond):
                old_pc = self.pc
                new_pc = self.regs[rsrc]
                self.pc = new_pc - 1
                self.debug_print(f"Jcond => jump from {old_pc} to {new_pc}")

        elif mnemonic == "JAL":
            # JAL Rdest, Rsrc => Rdest=PC+1, PC=Rsrc
            if len(tokens) != 3:
                print("[SIM] Syntax error in JAL (expected JAL Rdest, Rsrc)")
                return
            rdest = self.parse_reg(tokens[1])
            rsrc  = self.parse_reg(tokens[2])
            link_val = self.pc + 1
            self.regs[rdest] = self.to_16bit(link_val)
            new_pc = self.regs[rsrc]
            old_pc = self.pc
            self.pc = new_pc - 1
            self.debug_print(f"JAL => R{rdest}={link_val}, jump from {old_pc} to {new_pc}")

        else:
            # 其余未列出的指令或未实现
            print(f"[SIM] Unsupported instruction: {mnemonic}")


    # --------------------- 工具函数 ----------------------

    def parse_reg(self, token):
        """
        解析寄存器标记 'R0'..'R15'，返回寄存器编号。
        """
        token = token.strip().upper()
        if not token.startswith('R'):
            raise ValueError(f"Invalid register token: {token}")
        idx = int(token[1:])
        if idx < 0 or idx > 15:
            raise ValueError(f"Register index out of range: {idx}")
        return idx

    def parse_imm(self, token):
        """
        解析立即数，可以是十进制或带0x前缀的16进制。
        """
        token = token.strip().upper()
        if token.startswith("0X"):
            return int(token, 16)
        else:
            return int(token, 10)

    def to_16bit(self, val):
        """
        强制数值 val 限制在有符号16位范围: -32768..32767
        Python int是无限精度，这里要模拟16位CPU的溢出。
        """
        # 先用 0xFFFF mask 保留低16位
        masked = val & 0xFFFF
        # 如果最高位(15)是1，则为负数 => 进行符号扩展
        if masked & 0x8000:
            return masked - 0x10000
        else:
            return masked

    def update_flags(self, val_16):
        """
        根据 val_16 更新 N 和 Z 标志。
        F 标志（溢出）要根据加减运算来单独更新。
        """
        self.flagN = (val_16 < 0)
        self.flagZ = (val_16 == 0)
        # F 在具体加减运算里判断，这里不动

    def check_overflow_add(self, a, b, result):
        """
        判断对有符号16位数做 a + b = result 是否溢出
        """
        # 原理：若 a 和 b 同号，但 result 与 a 异号，则溢出
        # 但要注意 Python int 无限制，需要比较 16 位范围内的符号
        # 这里只做简单判断:
        if (a >= 0 and b >= 0 and result < 0) or (a < 0 and b < 0 and result >= 0):
            self.flagF = True
        else:
            self.flagF = False

    def check_overflow_sub(self, a, b, result):
        """
        判断 a - b 是否发生溢出
        """
        # a>=0, b<0 => a-b>=0 不溢出
        # a<0, b>=0 => a-b<0 不溢出
        # 如果 a、b 同号，且 result 与 a 异号 => 溢出
        if ((a ^ b) >= 0) and ((a ^ result) < 0):
            self.flagF = True
        else:
            self.flagF = False

    def check_condition(self, cond):
        """
        cond 可以是数字，对应处理 F、N、Z 的组合。
        例如:
          0 => EQ => Z=1
          1 => NE => Z=0
          2 => ...
        这里仅做示例，你可自行扩展
        """
        if cond == 0:  # EQ
            return self.flagZ
        elif cond == 1:  # NE
            return not self.flagZ
        elif cond == 2:  # F=1?
            return self.flagF
        # ...
        else:
            # 默认不满足
            return False

    def debug_print(self, msg):
        """
        用于打印每条指令的调试信息
        """
        print(f"  [DEBUG] {msg}")

    def dump_state(self):
        """
        打印最终所有寄存器、标志位、以及可选的 dmem 局部状态
        """
        print("\n----- Simulation Finished -----")
        print("Registers:")
        for i in range(16):
            print(f"  R{i} = {self.regs[i]}")
        print(f"Flags: F={self.flagF}, N={self.flagN}, Z={self.flagZ}")
        # 如果想查看DMEM可在此打印
        # print("DMEM[0..15]:", self.dmem[:16])


def main():
    if len(sys.argv) < 2:
        print("Usage: python simulate.py input.asm")
        sys.exit(1)

    sim = Simulator()
    sim.load_asm_file(sys.argv[1])
    sim.run()

if __name__ == "__main__":
    main()
