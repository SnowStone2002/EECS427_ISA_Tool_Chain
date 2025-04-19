#!/usr/bin/env python3
"""
简单的 EECS 427 反汇编器

用法：
    python disassembler.py input.hex output.asm

输入文件为十六进制格式的机器码（每行一个 16 位的机器码），
输出文件为对应的汇编代码（每行一条）。
"""

import sys
from src.mapping import instruction_set

# 在文件开头或适当位置定义 cond_map 和辅助函数
cond_map = {
    "EQ": 0,   # Z=1
    "NE": 1,   # Z=0
    "CS": 2,   # C=1（若实现）
    "CC": 3,   # C=0
    "HI": 4,   # L=1
    "LS": 5,   # L=0
    "GT": 6,   # N=1
    "LE": 7,   # N=0
    "FS": 8,   # F=1
    "FC": 9,   # F=0
    "LO": 10,  # L=0 & Z=0
    "HS": 11,  # L=1 or Z=1
    "LT": 12,  # N=0 & Z=0
    "GE": 13,  # N=1 or Z=1
    "UC": 14,  # Unconditional
    "NV": 15   # Never jump
}

def get_cond_mnemonic(cond_val):
    """返回给定条件码数字对应的助记符；如果没有找到，则返回数字字符串。"""
    for mnem, val in cond_map.items():
        if val == cond_val:
            return mnem
    return str(cond_val)


def disassemble_instruction(machine_code):
    """
    根据 16 位机器码反汇编出汇编语句字符串。
    对于 FIX/FIXV 格式，先检查是否匹配；否则根据 opcode 以及格式解析剩余字段。
    如果无法识别，则返回 "???"。
    """
    # 先检查 FIX 格式指令（完全固定值）
    for mnemonic, instr in instruction_set.items():
        if instr.fmt == "FIX":
            if machine_code == instr.fields["value"]:
                return mnemonic

    # 检查 FIXV 格式指令（低4位为变量）
    for mnemonic, instr in instruction_set.items():
        if instr.fmt == "FIXV":
            fixed = instr.fields["fixed"] & 0xFFF0
            if (machine_code & 0xFFF0) == fixed:
                vector = machine_code & 0xF
                return f"{mnemonic} 0x{vector:X}"

    # 非固定格式，先提取高 4 位的 opcode
    opcode = (machine_code >> 12) & 0xF

    # 针对不同格式的指令进行解析
    for mnemonic, instr in instruction_set.items():
        if instr.fmt == "RR":
            if opcode == instr.opcode:
                # RR 格式：位15-12: opcode, 11-8: Rdest, 7-4: ext, 3-0: Rsrc
                ext = (machine_code >> 4) & 0xF
                if instr.ext is not None and ext == instr.ext:
                    Rdest = (machine_code >> 8) & 0xF
                    Rsrc = machine_code & 0xF
                    return f"{mnemonic} R{Rdest}, R{Rsrc}"
        elif instr.fmt == "I4":
            if opcode == instr.opcode:
                ext = (machine_code >> 4) & 0xF
                if instr.ext is not None and ext == instr.ext:
                    # I4 格式：位15-12: opcode, 11-8:, 位7-4:, 位3-0: immed
                    # 提取位4作为 s 位（假设只有这一位有效）
                    imm = machine_code & 0xF
                    # 如果 s == 1，则认为立即数为负
                    return f"{mnemonic} {imm}"
        elif instr.fmt == "RI":
            if opcode == instr.opcode:
                # RI 格式：位15-12: opcode, 11-8: Rdest, 7-0: imm
                Rdest = (machine_code >> 8) & 0xF
                imm = machine_code & 0xFF
                return f"{mnemonic} R{Rdest}, 0x{imm:X}"
        elif instr.fmt == "RI4":
            if opcode == instr.opcode:
                ext = (machine_code >> 4) & 0xF
                if instr.ext is not None and ext == instr.ext:
                    # RI4 格式：位15-12: opcode, 11-8: Rdest, 位7-4: (固定为0 except bit4存 s), 位3-0: immed
                    Rdest = (machine_code >> 8) & 0xF
                    # 提取位4作为 s 位（假设只有这一位有效）
                    s = (machine_code >> 4) & 0x1
                    imm = machine_code & 0xF
                    # 如果 s == 1，则认为立即数为负
                    imm_value = -imm if s == 1 else imm
                    return f"{mnemonic} R{Rdest}, {imm_value}"
        elif instr.fmt == "Bcond":
            if opcode == instr.opcode:
                # BCOND 格式：位15-12: opcode, 11-8: cond, 7-0: disp (8位2's complement)
                cond = (machine_code >> 8) & 0xF
                cond_str = get_cond_mnemonic(cond)
                disp = machine_code & 0xFF
                # 进行 8 位符号扩展
                if disp & 0x80:
                    disp = disp - 256
                return f"{mnemonic} {cond_str}, {disp}"

        elif instr.fmt == "Jcond":
            if opcode == instr.opcode:
                # JCOND 格式：位15-12: opcode, 11-8: cond, 7-4: ext, 3-0: Rtarget
                cond = (machine_code >> 8) & 0xF
                cond_str = get_cond_mnemonic(cond)
                ext = (machine_code >> 4) & 0xF
                if instr.ext is not None and ext == instr.ext:
                    Rtarget = machine_code & 0xF
                    return f"{mnemonic} {cond_str}, R{Rtarget}"

        elif instr.fmt == "RS":
            if opcode == instr.opcode:
                # RS 格式（例如 STOR）：位15-12: opcode, 11-8: Rsrc, 7-4: ext, 3-0: Raddr
                Rsrc = (machine_code >> 8) & 0xF
                ext = (machine_code >> 4) & 0xF
                if instr.ext is not None and ext == instr.ext:
                    Raddr = machine_code & 0xF
                    return f"{mnemonic} R{Rsrc}, R{Raddr}"
        elif instr.fmt == "IR":
            if opcode == instr.opcode:
                # IR 格式（例如 TBITI）：位15-12: opcode, 11-8: Rsrc, 7-0: imm
                ext = (machine_code >> 4) & 0xF
                if instr.ext is not None and ext == instr.ext:
                    Rsrc = (machine_code >> 8) & 0xF
                    imm = machine_code & 0xFF
                    return f"{mnemonic} R{Rsrc}, 0x{imm:X}"
    # 如果无法识别，则返回错误信息
    return f"??? (0x{machine_code:04X})"

def disassemble_file(input_file, output_file):
    """
    读取输入文件中的机器码（每行 16 位十六进制数），
    反汇编后写入输出文件，每行一条汇编指令。
    """
    with open(input_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    assembly_lines = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            machine_code = int(line, 16)
        except ValueError:
            assembly_lines.append(f"; Invalid line: {line}")
            continue
        asm_line = disassemble_instruction(machine_code)
        assembly_lines.append(asm_line)

    with open(output_file, "w", encoding="utf-8") as f:
        for asm in assembly_lines:
            f.write(asm + "\n")
    print(f"Disassembly completed. {len(assembly_lines)} instructions written to {output_file}.")

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python disassembler.py input.hex output.asm")
        sys.exit(1)
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    disassemble_file(input_file, output_file)
