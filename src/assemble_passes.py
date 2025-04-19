# assemble_passes.py

import re

# 条件码助记符与数字的映射
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
    "NV": 15   # Never jump (有的资料写 (无名))
}

def first_pass(lines):
    """
    第一遍扫描：收集标签和指令行对应的地址。
    返回:
      symbol_table: { label(str, upper): address(int) }
      processed_lines: [(addr, original_line_str), ...]
    """
    symbol_table = {}
    processed_lines = []
    current_addr = 0  # 当前指令地址，从0开始

    for line in lines:
        # 去掉注释
        raw = line.split(";")[0].strip()
        if not raw:
            continue  # 空行直接跳过

        if ":" in raw:
            # 可能有 label
            parts = raw.split(":", 1)
            label = parts[0].strip()
            instr_part = parts[1].strip()  # 冒号后面的指令

            label_upper = label.upper()
            if label_upper in symbol_table:
                # 重复定义错误
                print(f"[WARN] Label {label} redefined!")
            symbol_table[label_upper] = current_addr

            if instr_part:
                processed_lines.append((current_addr, instr_part))
                current_addr += 1
        else:
            # 普通指令
            processed_lines.append((current_addr, raw))
            current_addr += 1

    return symbol_table, processed_lines


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
    
def assemble_line_label_aware(line, current_addr, symbol_table):
    """
    类似 assemble_line，但在遇到标签时根据指令类型计算地址/偏移量。
    - current_addr: 该行指令的地址
    - symbol_table: { label_upper: label_addr, ... }
    - line: 如 "Bcond 0, loop"
    """
    # 去除注释、空白
    line = line.split(";")[0].strip()
    if not line:
        return None  # 空行

    tokens = re.split(r'[,\s]+', line)
    mnemonic = tokens[0].upper()
    # print(mnemonic)
    if mnemonic not in instruction_set:
        raise ValueError(f"Unknown instruction: {mnemonic}")
    instr = instruction_set[mnemonic]
    # print(instr.fmt)

    # 准备解析操作数(可能包含标签)
    # 先将 tokens[1..] 里的潜在 label 替换成地址/偏移
    # 例如 Bcond cond, label => tokens[2] = symbol_table[label]
    # 但是 Bcond 需要相对地址 => offset = label_addr - (current_addr+1)
    operands = {}

    if instr.fmt == "RR":
        # tokens: [mnemonic, Rdest, Rsrc]
        if len(tokens) != 3:
            raise ValueError(f"{mnemonic} needs 2 operands, got {len(tokens)-1}")
        operands["Rdest"] = parse_register(tokens[1])
        operands["Rsrc"]  = parse_register(tokens[2])

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

    elif instr.fmt == "I4":
        # 用于 SETQ
        if len(tokens) != 2:
            raise ValueError(f"Instruction {mnemonic} requires 1 operands, got {len(tokens)-1}")
        imm = parse_immediate(tokens[1])
        operands["imm"] = imm

    elif instr.fmt == "Bcond":
        if len(tokens) != 3:
            raise ValueError(f"Instruction {mnemonic} requires 2 operands, got {len(tokens)-1}")
        
        # 解析条件码
        cond_token = tokens[1].upper()
        if cond_token in cond_map:
            cond_val = cond_map[cond_token]
        else:
            cond_val = parse_immediate(tokens[1])
        operands["cond"] = cond_val & 0xF

        # 解析位移量：如果 tokens[2] 是一个标签，则用符号表转换成偏移量
        disp_token = tokens[2].strip()
        if disp_token.upper() in symbol_table:
            label_addr = symbol_table[disp_token.upper()]
            # 计算相对偏移：offset = label_addr - (current_addr + 1)
            offset = label_addr - (current_addr + 1)
            operands["disp"] = offset & 0xFF
        else:
            operands["disp"] = parse_immediate(tokens[2]) & 0xFF


    elif instr.fmt == "Jcond":
        if len(tokens) != 3:
            raise ValueError(...)

        cond_token = tokens[1].upper()
        if cond_token in cond_map:
            cond_val = cond_map[cond_token]
        else:
            cond_val = parse_immediate(cond_token)
        operands["cond"] = cond_val & 0xF

        # 后面仍是获取 Rtarget
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

    # 最后根据 operands 组合机器码
    return build_machine_code(instr, operands)

def build_machine_code(instr, operands):
    """
    原先 assemble_line 中的机器码打包逻辑
    (可直接复制你 assembler.py 里对应的行)
    """
    machine_codes = []  # 改为列表
    machine_code = 0

    if instr.fmt in ("RR", "RI", "RI4", "Bcond", "Jcond", "RS", "IR", "I4"):
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
        elif instr.fmt == "I4":
            machine_code |= (instr.ext & 0xF) << 4
            machine_code |= (operands["imm"] & 0xF)
        elif instr.fmt == "Bcond":
            machine_code |= (operands["cond"] & 0xF) << 8
            machine_code |= (operands["disp"] & 0xFF)
            # 对于 Bcond，不仅返回当前指令，还加入一条 NOP（例如 0x0000）
            # machine_codes.append(machine_code)
            # machine_codes.append(0x0000)  # 加入一条 NOP 指令
            # return machine_codes
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
        vector = 0
        machine_code = (instr.fields["fixed"] & 0xFFF0) | (vector & 0xF)
    else:
        raise ValueError(f"Unsupported instruction format: {instr.fmt}")

    machine_codes.append(machine_code)
    return machine_codes