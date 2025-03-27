# EECS 427 ISA 指令集说明

该文档详细介绍了 EECS 427 处理器仿真器支持的所有指令，文档结构和格式类似于 asm 文件注释，供开发和教学使用。

---

## 处理器组件说明

- **IMEM**: 存储汇编代码的指令内存，每条指令作为一行文本存储。  
- **DMEM**: 数据内存，共 512 个 16 位有符号数。  
- **RegFile**: 寄存器文件，共 16 个 16 位有符号寄存器。  
- **PSR**: 程序状态寄存器，包含标志位：  
  - **F**: 溢出标志  
  - **N**: 负数标志  
  - **Z**: 零标志  
  另外还可能使用 **C**（进位）和 **L**（比较辅助标志）用于条件码判断。  
- **PC**: 程序计数器，指向下一条要执行的指令。

**仿真停止条件：**  
1. PC 超出程序范围。  

---

## 指令分类与说明

### 1. 寄存器-寄存器型指令
这些指令均以两个寄存器为操作数，形式为：`INSTR Rdest, Rsrc`。

- **ADD Rdest, Rsrc**  
  执行加法操作：`Rdest = Rdest + Rsrc`。更新目标寄存器，并根据结果更新标志位（负、零、溢出）。

- **SUB Rdest, Rsrc**  
  执行减法操作：`Rdest = Rdest - Rsrc`。仅用于修改寄存器值，更新标志。

- **CMP Rdest, Rsrc**  
  比较操作：计算 `Rdest - Rsrc`，仅更新标志（不写回结果），用于后续条件分支判断。

- **AND Rdest, Rsrc**  
  按位与：`Rdest = Rdest & Rsrc`。

- **OR Rdest, Rsrc**  
  按位或：`Rdest = Rdest | Rsrc`。

- **XOR Rdest, Rsrc**  
  按位异或：`Rdest = Rdest ^ Rsrc`。

- **MOV Rdest, Rsrc**  
  复制操作：`Rdest = Rsrc`。

---

### 2. 寄存器-立即数型指令
这类指令操作数为一个寄存器和一个立即数，形式为：`INSTR Rdest, imm`。

- **ADDI Rdest, imm**  
  加法操作：`Rdest = Rdest + imm`（立即数按有符号数处理），更新标志及溢出判断。

- **SUBI Rdest, imm**  
  减法操作：`Rdest = Rdest - imm`。

- **CMPI Rdest, imm**  
  比较操作：计算 `Rdest - imm`，仅更新标志，不修改寄存器内容。

- **ANDI Rdest, imm**  
  按位与：`Rdest = Rdest & zero_extend(imm)`。立即数零扩展至 16 位后操作。

- **ORI Rdest, imm**  
  按位或：`Rdest = Rdest | zero_extend(imm)`。

- **XORI Rdest, imm**  
  按位异或：`Rdest = Rdest ^ zero_extend(imm)`。

- **MOVI Rdest, imm**  
  立即数赋值：`Rdest = zero_extend(imm)`，直接将立即数赋值给目标寄存器。

---

### 3. 移位指令
用于对寄存器中的值进行位移操作。

- **LSH Rdest, Rsrc**  
  左移操作：`Rdest = Rdest << Rsrc`。移位位数由寄存器 Rsrc 中的值决定；当 Rsrc 为负时，将取其低 4 位进行左移。

- **LSHI Rdest, imm**  
  左移操作：`Rdest = Rdest << imm`。立即数指定移位位数，仅支持正数移位。

- **LUI Rdest, imm**  
  装载高位：`Rdest = imm << 8`。将立即数左移 8 位后存入目标寄存器。

---

### 4. 内存访问指令
通过寄存器中的值确定数据内存中的地址来进行加载或存储操作。

- **LOAD Rdest, Raddr**  
  数据加载：从 DMEM 中读取数据，将 `DMEM[ Raddr ]`（地址为寄存器 Raddr 的值，取低 9 位）存入 Rdest。

- **STOR Rsrc, Raddr**  
  数据存储：将 Rsrc 中的值存入 DMEM 中，地址由 Raddr 中的值确定（取低 9 位）。

---

### 5. 分支与跳转指令
用于控制程序流程，根据条件码判断和跳转位移或地址。

- **BCOND cond, disp**  
  条件分支：若条件 `cond` 为真，则 `PC = PC + disp`。  
  - **cond** 可以是条件助记符（例如 EQ、NE、...）或立即数。  
  - **disp** 为立即数（8 位 2's complement）。

- **JCOND cond, Rtarget**  
  条件跳转：若条件 `cond` 为真，则将 PC 设置为寄存器 Rtarget 的值。

- **JAL Rlink, Rtarget**  
  跳转并链接：  
  - 先将当前 PC+1 的值存入 Rtarget。  
  - 然后将 PC 存入寄存器 Rlink。

- **WAIT**  
  等待指令，通常用于同步或暂停操作。当前仿真器中，该指令会打印调试信息，并可根据需求用于终止或暂停模拟。

---

### 6. 条件码（Condition Codes）
在分支与跳转指令中，可使用以下条件码助记符，其对应的含义如下：

- **EQ**: Equal (Z = 1)  
- **NE**: Not Equal (Z = 0)  
- **CS**: Carry Set (C = 1)  
- **CC**: Carry Clear (C = 0)  
- **HI**: Higher Than (L = 1)  
- **LS**: Lower or Same (L = 0)  
- **GT**: Greater Than (N = 1)  
- **LE**: Less or Equal (N = 0)  
- **FS**: Flag Set (F = 1)  
- **FC**: Flag Clear (F = 0)  
- **LO**: Lower Than (L = 0 且 Z = 0)  
- **HS**: Higher or Same (L = 1 或 Z = 1)  
- **LT**: Less Than (N = 0 且 Z = 0)  
- **GE**: Greater or Equal (N = 1 或 Z = 1)  
- **UC**: Unconditional (无条件跳转)  
- **NV**: Never Jump (永不跳转)

---

## 使用示例

假设有一段汇编代码 `Fibonacci.asm`，可以通过以下步骤使用仿真器执行：

1. **汇编**：使用 `assembler.py` 将 `Fibonacci.asm` 转换为机器码文件（`.hex`）。
2. **反汇编**：使用 `disassembler.py` 将 `.hex` 文件转换回汇编代码（无标签版本）。
3. **仿真**：使用 `simulator.py` 执行反汇编后的汇编代码，并生成仿真日志。

为了简化流程，可使用 [src/process.py](./src/process.py) 脚本，该脚本整合了上述步骤，只需指定输入文件名即可：

```bash
python3 ./src/process.py tests/Fibonacci.asm
