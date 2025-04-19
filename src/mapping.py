# src/mapping.py

from collections import namedtuple

# 定义指令数据结构：包含操作码（opcode）、扩展码（ext）、格式（fmt）和字段信息（fields）
Instruction = namedtuple("Instruction", ["opcode", "ext", "fmt", "fields"])

# RR 格式：寄存器–寄存器型指令
rr_fields = {
    "Rdest": (8, 11),  # 目的寄存器位于 11-8
    "ext":   (4, 7),   # 扩展码位于 7-4
    "Rsrc":  (0, 3)    # 源寄存器位于 3-0
}

# RI 格式：寄存器–立即数型（8位立即数）
ri_fields = {
    "Rdest": (8, 11),
    "imm":   (0, 7)
}

# RI4 格式：用于 LSHI/ASHUI 指令（4位立即数 + 1位 s，位7-5固定为0，位4存 s，位3-0为 immed）
ri4_fields = {
    "Rdest": (8, 11),
    "s":     (4, 4),  # 单独的一位，用于存 s（指示移位方向）
    "imm":   (0, 3)
}

# I4 格式：用于 SETQ 指令（）
i4_fields = {
    "ext":   (4, 7),   # 扩展码位于 7-4
    "imm":   (0, 3)
}

# BCOND 格式：条件分支指令
bcond_fields = {
    "cond": (8, 11),  # 条件码占 11-8
    "disp": (0, 7)    # 8位位移量（2's complement）
}

# JCOND 格式：条件跳转指令
jcond_fields = {
    "cond": (8, 11),       # 条件码占 11-8
    "Rtarget": (0, 3)      # 目标寄存器占 3-0
}

# RS 格式：用于 STOR 指令（操作数顺序与 RR 略有不同）
store_fields = {
    "Rsrc":  (8, 11),  # 对于 STOR，Rsrc 占 11-8
    "ext":   (4, 7),
    "Raddr": (0, 3)
}

# IR 格式：用于 TBITI 指令（寄存器放 11-8，立即数占 0-7）
ir_fields = {
    "Rsrc": (8, 11),
    "imm":  (0, 7)
}

# TBIT 格式：用于 TBIT 指令（寄存器和偏移量）
tbit_fields = {
    "Rsrc":  (8, 11),
    "offset": (0, 3)
}

# FIX 格式：固定指令，直接给出16位机器码值
fix_fields = {
    "value": None  # 实际值在映射时直接赋值
}

# FIXV 格式：固定部分加上低4位变量（如 EXCP）
fixv_fields = {
    "fixed": None,     # 固定部分（低4位为0）
    "vector": (0, 3)   # 低4位变量
}

# 构建完整映射表（注意所有键都采用大写，与汇编器转换后的 mnemonic 匹配）
instruction_set = {
    # 寄存器–寄存器型指令（RR格式）
    "ADD":    Instruction(opcode=0b0000, ext=0b0101, fmt="RR", fields=rr_fields),
    "ADDU":   Instruction(opcode=0b0000, ext=0b0110, fmt="RR", fields=rr_fields),
    "ADDC":   Instruction(opcode=0b0000, ext=0b0111, fmt="RR", fields=rr_fields),
    "MUL":    Instruction(opcode=0b0000, ext=0b1110, fmt="RR", fields=rr_fields),
    "SUB":    Instruction(opcode=0b0000, ext=0b1001, fmt="RR", fields=rr_fields),
    "SUBC":   Instruction(opcode=0b0000, ext=0b1010, fmt="RR", fields=rr_fields),
    "CMP":    Instruction(opcode=0b0000, ext=0b1011, fmt="RR", fields=rr_fields),
    "AND":    Instruction(opcode=0b0000, ext=0b0001, fmt="RR", fields=rr_fields),
    "OR":     Instruction(opcode=0b0000, ext=0b0010, fmt="RR", fields=rr_fields),
    "XOR":    Instruction(opcode=0b0000, ext=0b0011, fmt="RR", fields=rr_fields),
    "MOV":    Instruction(opcode=0b0000, ext=0b1101, fmt="RR", fields=rr_fields),

    # 立即数型指令（RI格式）
    "ADDI":   Instruction(opcode=0b0101, ext=None, fmt="RI", fields=ri_fields),
    "ADDUI":  Instruction(opcode=0b0110, ext=None, fmt="RI", fields=ri_fields),
    "ADDCI":  Instruction(opcode=0b0111, ext=None, fmt="RI", fields=ri_fields),
    "MULI":   Instruction(opcode=0b1110, ext=None, fmt="RI", fields=ri_fields),
    "SUBI":   Instruction(opcode=0b1001, ext=None, fmt="RI", fields=ri_fields),
    "SUBCI":  Instruction(opcode=0b1010, ext=None, fmt="RI", fields=ri_fields),
    "CMPI":   Instruction(opcode=0b1011, ext=None, fmt="RI", fields=ri_fields),
    "ANDI":   Instruction(opcode=0b0001, ext=None, fmt="RI", fields=ri_fields),  # 零扩展立即数
    "ORI":    Instruction(opcode=0b0010, ext=None, fmt="RI", fields=ri_fields),  # 零扩展立即数
    "XORI":   Instruction(opcode=0b0011, ext=None, fmt="RI", fields=ri_fields),
    "MOVI":   Instruction(opcode=0b1101, ext=None, fmt="RI", fields=ri_fields),

    # 移位指令
    "LSH":    Instruction(opcode=0b1000, ext=0b0100, fmt="RR", fields=rr_fields),
    "LSHI":   Instruction(opcode=0b1000, ext=None, fmt="RI4", fields=ri4_fields),
    "ASHU":   Instruction(opcode=0b1000, ext=0b0110, fmt="RR", fields=rr_fields),
    "ASHUI":  Instruction(opcode=0b1000, ext=None, fmt="RI4", fields=ri4_fields),
    "LUI":    Instruction(opcode=0b1111, ext=None, fmt="RI", fields=ri_fields),

    # 内存访问
    "LOAD":   Instruction(opcode=0b0100, ext=0b0000, fmt="RR", fields=rr_fields),
    "STOR":   Instruction(opcode=0b0100, ext=0b0100, fmt="RS", fields=store_fields),

    # 数据转换
    "SNXB":   Instruction(opcode=0b0100, ext=0b0010, fmt="RR", fields=rr_fields),
    "ZRXB":   Instruction(opcode=0b0100, ext=0b0110, fmt="RR", fields=rr_fields),

    # 条件操作与跳转
    "SCOND":  Instruction(opcode=0b0100, ext=0b1101, fmt="RR", fields=rr_fields),
    "BCOND":  Instruction(opcode=0b1100, ext=None, fmt="Bcond", fields=bcond_fields),
    "JCOND":  Instruction(opcode=0b0100, ext=0b1100, fmt="Jcond", fields=jcond_fields),
    "JAL":    Instruction(opcode=0b0100, ext=0b1000, fmt="RR", fields=rr_fields),

    # 位操作
    "TBIT":   Instruction(opcode=0b0100, ext=0b1010, fmt="RR", fields=rr_fields),
    "TBITI":  Instruction(opcode=0b0100, ext=0b1110, fmt="IR", fields=ir_fields),

    # PSR操作
    "LPR":    Instruction(opcode=0b0100, ext=0b0001, fmt="RR", fields=rr_fields),
    "SPR":    Instruction(opcode=0b0100, ext=0b0101, fmt="RR", fields=rr_fields),

    # 中断与异常（固定指令）
    "DI":     Instruction(opcode=None, ext=None, fmt="FIX", fields={"value": 0x4030}),
    "EI":     Instruction(opcode=None, ext=None, fmt="FIX", fields={"value": 0x4070}),
    "RETX":   Instruction(opcode=None, ext=None, fmt="FIX", fields={"value": 0x4090}),
    "WAIT":   Instruction(opcode=None, ext=None, fmt="FIX", fields={"value": 0x0000}),
    "EXCP":   Instruction(opcode=None, ext=None, fmt="FIXV", fields={"fixed": 0x40B0, "vector": (0, 3)}),

    # 数据通路指令
    "STCR": Instruction(opcode=0b0000, ext=0b0100, fmt="RR", fields=rr_fields),  # Reg → CIM
    "STCM": Instruction(opcode=0b0000, ext=0b1000, fmt="RR", fields=rr_fields),  # DMEM → CIM
    "LDCR": Instruction(opcode=0b0000, ext=0b1100, fmt="RR", fields=rr_fields),  # CIM → Reg
    # 计算指令
    "CMPT": Instruction(opcode=0b0000, ext=0b1111, fmt="RR", fields=rr_fields),  # 激活寄存器 + DMEM addr寄存器

    # 量化设置
    "SETQ": Instruction(opcode=0b0100, ext=0b1111, fmt="I4", fields=i4_fields)
  

}

if __name__ == '__main__':
    # 打印所有指令的映射信息以供检查
    for mnemonic, instr in instruction_set.items():
        if instr.fmt in ("FIX", "FIXV"):
            if instr.fmt == "FIX":
                fixed_val = instr.fields["value"]
                print(f"{mnemonic}: FIX, value=0x{fixed_val:04X}")
            else:  # FIXV
                fixed_val = instr.fields["fixed"]
                print(f"{mnemonic}: FIXV, fixed=0x{fixed_val:04X}, vector field={instr.fields['vector']}")
        else:
            ext_str = format(instr.ext, '04b') if instr.ext is not None else "None"
            print(f"{mnemonic}: opcode={instr.opcode:04b}, ext={ext_str}, fmt={instr.fmt}, fields={instr.fields}")
