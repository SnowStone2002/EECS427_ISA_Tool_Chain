# assembler.py
import sys
import os
import re

from src.assemble_passes import first_pass, assemble_line_label_aware
# or just inline them

def assemble_file(input_file, output_file):
    with open(input_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # 第一遍：构建符号表和(地址->指令)列表
    symbol_table, processed_lines = first_pass(lines)

    # 第二遍：对每个行进行assemble_line_label_aware，生成机器码
    machine_codes = []
    for (addr, line) in processed_lines:
        mc = assemble_line_label_aware(line, addr, symbol_table)
        if mc is not None:
            machine_codes.append(mc)

    # 写入hex
    with open(output_file, "w", encoding="utf-8") as f:
        for sublist in machine_codes:
            for code in sublist:
                f.write(f"{code:04X}\n")

    print(f"Assembly completed. {len(machine_codes)} instructions written to {output_file}.")

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python assembler.py input.asm output.hex")
        sys.exit(1)
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    assemble_file(input_file, output_file)
