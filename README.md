Structure:

isa_translator/
├── README.md
├── .gitignore
├── setup.py         # 如果需要打包的话
├── src/
│   ├── __init__.py
│   ├── assembler.py      # 汇编器实现（汇编码转机器码）
│   ├── disassembler.py   # 反汇编器实现（机器码转汇编码）
│   └── mapping.py        # 存放指令映射表
├── tests/
│   ├── __init__.py
│   ├── test_assembler.py
│   └── test_disassembler.py
└── docs/
    └── design.md         # 项目设计文档
