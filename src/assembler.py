#!/usr/bin/env python3
"""
简单的 EECS 427 处理器汇编器示例

用法：
    python assembler.py input.asm output.hex

输入文件是一个纯文本汇编文件，每行一个指令。支持注释（以 ";" 开始）。
输出文件中每行保存一条机器码（16位十六进制格式）。
"""

import re
import sys
from src.mapping import instruction_set

def parse_register(token):
    """
    解析寄存器标记（形如 R0, R1, ...）
    """
    token = token.strip().upper()
    if token.startswith("R"):
        try:
            return int(token[1:])
        except ValueError:
            raise ValueError(f"Invalid register token: {token}")
    else:
        raise ValueError(f"Expected register, got: {token}")

def parse_immediate(token):
    """
    解析立即数，可以是十进制或以 0x 开头的十六进制数。
    """
    token = token.strip()
    try:
        if token.startswith("0x") or token.startswith("0X"):
            return int(token, 16)
        else:
            return int(token, 10)
    except ValueError:
        raise ValueError(f"Invalid immediate value: {token}")

def assemble_line(line):
    """
    解析一行汇编代码，并返回 16 位机器码（整数形式）。
    忽略空行和注释（假设注释以 ';' 开始）。
    """
    # 去除注释并修剪空白字符
    line = line.split(";")[0].strip()
    if not line:
        return None  # 空行直接跳过

    # 使用正则表达式分割（支持空格和逗号分隔）
    tokens = re.split(r'[,\s]+', line)
    mnemonic = tokens[0].upper()
    if mnemonic not in instruction_set:
        raise ValueError(f"Unknown instruction: {mnemonic}")
    instr = instruction_set[mnemonic]

    operands = {}
    # 根据指令格式解析操作数
    if instr.fmt == "RR":
        # 期望两个操作数：Rdest, Rsrc
        if len(tokens) != 3:
            raise ValueError(f"Instruction {mnemonic} requires 2 operands, got {len(tokens)-1}")
        operands["Rdest"] = parse_register(tokens[1])
        operands["Rsrc"] = parse_register(tokens[2])
    elif instr.fmt == "RI":
        # 期望两个操作数：Rdest, immediate
        if len(tokens) != 3:
            raise ValueError(f"Instruction {mnemonic} requires 2 operands, got {len(tokens)-1}")
        operands["Rdest"] = parse_register(tokens[1])
        operands["imm"] = parse_immediate(tokens[2])
    elif instr.fmt == "RI4":
        # 用于 LSHI / ASHUI：两个操作数：Rdest, immediate
        if len(tokens) != 3:
            raise ValueError(f"Instruction {mnemonic} requires 2 operands, got {len(tokens)-1}")
        operands["Rdest"] = parse_register(tokens[1])
        imm = parse_immediate(tokens[2])
        # 根据规格：s = sign（假定：非负立即数 s = 0；负数 s = 1，并取绝对值）
        if imm < 0:
            s = 1
            imm = abs(imm)
        else:
            s = 0
        if not (0 <= imm < 16):
            raise ValueError(f"Immediate value out of range for {mnemonic}: {imm}")
        operands["s"] = s
        operands["imm"] = imm
    elif instr.fmt == "Bcond":
        # 条件分支：两个操作数：条件码、位移（disp）
        if len(tokens) != 3:
            raise ValueError(f"Instruction {mnemonic} requires 2 operands, got {len(tokens)-1}")
        operands["cond"] = parse_immediate(tokens[1])
        operands["disp"] = parse_immediate(tokens[2])
    elif instr.fmt == "Jcond":
        # 条件跳转：两个操作数：条件码、目标寄存器（Rtarget）
        if len(tokens) != 3:
            raise ValueError(f"Instruction {mnemonic} requires 2 operands, got {len(tokens)-1}")
        operands["cond"] = parse_immediate(tokens[1])
        operands["Rtarget"] = parse_register(tokens[2])
    elif instr.fmt == "RS":
        # STOR 指令：两个操作数：Rsrc, Raddr
        if len(tokens) != 3:
            raise ValueError(f"Instruction {mnemonic} requires 2 operands, got {len(tokens)-1}")
        operands["Rsrc"] = parse_register(tokens[1])
        operands["Raddr"] = parse_register(tokens[2])
    elif instr.fmt == "IR":
        # TBITI 指令：两个操作数：Rsrc, immediate
        if len(tokens) != 3:
            raise ValueError(f"Instruction {mnemonic} requires 2 operands, got {len(tokens)-1}")
        operands["Rsrc"] = parse_register(tokens[1])
        operands["imm"] = parse_immediate(tokens[2])
    elif instr.fmt in ("FIX", "FIXV"):
        # 固定指令，无操作数
        if len(tokens) != 1:
            raise ValueError(f"Instruction {mnemonic} takes no operands")
    else:
        raise ValueError(f"Unsupported instruction format: {instr.fmt}")

    # 根据指令格式和解析的操作数生成 16 位机器码
    machine_code = 0
    if instr.fmt in ("RR", "RI", "RI4", "Bcond", "Jcond", "RS", "IR"):
        # 将 opcode 放入高 4 位
        machine_code |= (instr.opcode & 0xF) << 12

        if instr.fmt == "RR":
            machine_code |= (operands["Rdest"] & 0xF) << 8
            machine_code |= (instr.ext & 0xF) << 4
            machine_code |= (operands["Rsrc"] & 0xF)
        elif instr.fmt == "RI":
            machine_code |= (operands["Rdest"] & 0xF) << 8
            machine_code |= (operands["imm"] & 0xFF)
        elif instr.fmt == "RI4":
            machine_code |= (operands["Rdest"] & 0xF) << 8
            # 假定 RI4 格式：位7-5 固定为0，位4 存 s，位3-0 为 immed
            s_bit = (operands["s"] & 0x1) << 4
            machine_code |= s_bit
            machine_code |= (operands["imm"] & 0xF)
        elif instr.fmt == "Bcond":
            machine_code |= (operands["cond"] & 0xF) << 8
            machine_code |= (operands["disp"] & 0xFF)
        elif instr.fmt == "Jcond":
            machine_code |= (operands["cond"] & 0xF) << 8
            machine_code |= (instr.ext & 0xF) << 4
            machine_code |= (operands["Rtarget"] & 0xF)
        elif instr.fmt == "RS":
            machine_code |= (operands["Rsrc"] & 0xF) << 8
            machine_code |= (instr.ext & 0xF) << 4
            machine_code |= (operands["Raddr"] & 0xF)
        elif instr.fmt == "IR":
            machine_code |= (operands["Rsrc"] & 0xF) << 8
            machine_code |= (operands["imm"] & 0xFF)
    elif instr.fmt == "FIX":
        machine_code = instr.fields["value"] & 0xFFFF
    elif instr.fmt == "FIXV":
        # 对于 FIXV 格式（如 EXCP），这里简单将 vector 设为 0
        vector = 0
        machine_code = (instr.fields["fixed"] & 0xFFF0) | (vector & 0xF)
    else:
        raise ValueError(f"Unsupported instruction format: {instr.fmt}")

    return machine_code

def assemble_file(input_file, output_file):
    """
    读取 asm 文件，将每一行翻译成机器码，并写入输出文件（每行一条机器码，十六进制格式）
    """
    machine_codes = []
    with open(input_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    for lineno, line in enumerate(lines, 1):
        try:
            mc = assemble_line(line)
            if mc is not None:
                machine_codes.append(mc)
        except Exception as e:
            print(f"Error on line {lineno}: {line.strip()}")
            print(e)
    with open(output_file, "w", encoding="utf-8") as f:
        for code in machine_codes:
            f.write(f"{code:04X}\n")
    print(f"Assembly completed. {len(machine_codes)} instructions written to {output_file}.")


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python assembler.py input.asm output.hex")
        sys.exit(1)
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    assemble_file(input_file, output_file)
