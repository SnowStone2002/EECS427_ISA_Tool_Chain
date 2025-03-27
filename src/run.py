#!/usr/bin/env python
import subprocess
import sys
import os

def main():
    if len(sys.argv) < 2:
        print("用法: python run.py <inputfile>")
        sys.exit(1)

    input_file = sys.argv[1]

    # 提取基础文件名，不包含目录和扩展名
    base_name = os.path.splitext(os.path.basename(input_file))[0]

    # 输出目录
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)

    # 构造输出文件路径
    hex_file = os.path.join(output_dir, f"{base_name}.hex")
    asm_file = os.path.join(output_dir, f"{base_name}_no_label.asm")
    sim_output = os.path.join(output_dir, "simulation.out")

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

        # 调用仿真器，输出重定向到 simulation.out 文件
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
