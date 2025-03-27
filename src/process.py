#!/usr/bin/env python
import subprocess
import sys

def main():
    if len(sys.argv) < 2:
        print("用法: python process.py <inputfile>")
        sys.exit(1)

    input_file = sys.argv[1]
    hex_file = "tests/output.hex"
    asm_file = "tests/output.asm"
    sim_output = "tmp.txt"

    try:
        # 调用汇编器
        print("Running assembler...")
        subprocess.run(
            ["python3", "-m", "src.assembler", input_file, hex_file],
            check=True
        )

        # 调用反汇编器
        print("Running disassembler...")
        subprocess.run(
            ["python3", "-m", "src.disassembler", hex_file, asm_file],
            check=True
        )

        # 调用仿真器，输出重定向到文件
        print("Running simulator...")
        with open(sim_output, "w") as f:
            subprocess.run(
                ["python3", "./src/simulator.py", asm_file],
                check=True,
                stdout=f
            )

        print("所有步骤执行完成！")
    except subprocess.CalledProcessError as e:
        print("执行过程中出错：", e)
        sys.exit(1)

if __name__ == "__main__":
    main()