# User Manual

## Getting Started

### Loading Your First Program

1. **Open the simulator** at `http://localhost:5010`
2. **Enter assembly code** in the code editor (left panel)
3. **Click "Compile Code"** to load and validate your program
4. **Observe the datapath** visualization on the right

### Sample Program

```assembly
// Basic arithmetic example
ADDI X1, XZR, #10        // Load 10 into X1
ADDI X2, XZR, #5         // Load 5 into X2
ADD  X3, X1, X2          // Add X1 + X2, store in X3
STUR X3, [SP, #8]        // Store X3 to memory
LDUR X4, [SP, #8]        // Load from memory to X4
```

## Execution Modes

### 1. Micro-Step Mode

**Purpose**: Execute individual pipeline stages

**How to use**:

- Click **"Micro Step"** button
- Observe each stage: Fetch → Decode → Execute → Memory → Write Back
- Watch component highlighting and data flow animations

**Best for**: Understanding pipeline behavior and instruction flow

### 2. Full Instruction Mode

**Purpose**: Execute complete instructions at once

**How to use**:

- Click **"Full Instruction"** button
- All 5 micro-steps execute sequentially
- Final result is displayed

**Best for**: Seeing overall instruction effects

### 3. Auto Run Mode

**Purpose**: Continuous program execution

**How to use**:

- Click **"Run"** to start
- Adjust speed with the slider (1-10 seconds)
- Click **"Pause"** to stop

**Best for**: Running complete programs

### 4. Return Back Feature

**Purpose**: Navigate to previous instruction states

**How to use**:

- Click **"Return Back"** button
- System restores previous instruction state
- All registers, memory, and flags are restored

**Best for**: Debugging and understanding instruction effects

## Interface Overview

### Left Panel - Code Editor

- **Syntax highlighting** for LEGv8 assembly
- **Line numbers** for easy reference
- **Upload button** to load files
- **Compile button** to validate and load code

### Center Panel - Datapath Visualization

- **Interactive SVG** showing processor components
- **Component highlighting** during execution
- **Animated data paths** showing signal flow
- **Zoom controls** for better viewing

### Right Panel - System State

#### Registers Tab

- **32 general-purpose registers** (X0-X27)
- **Special registers**: SP, FP, LR, XZR
- **Hex and decimal** value display
- **Real-time updates** during execution

#### Memory Tab

- **Data memory contents**
- **Address and value** in hex/decimal
- **Automatic updates** when memory changes
- **Sorted by address** for easy browsing

#### Control Signals Tab

- **All control signals** in real-time
- **Color-coded states**: Active (green) / Inactive (red)
- **Signal descriptions** for learning

#### Log Tab

- **Execution history** with detailed logs
- **Error messages** and warnings
- **Step-by-step execution trace**

## Working with Programs

### Writing Assembly Code

**Basic syntax**:

```assembly
INSTRUCTION destination, source1, source2
```

**Examples**:

```assembly
ADD  X1, X2, X3         // X1 = X2 + X3
ADDI X1, X2, #5         // X1 = X2 + 5
LDUR X1, [X2, #8]       // X1 = Memory[X2 + 8]
STUR X1, [X2, #8]       // Memory[X2 + 8] = X1
CBZ  X1, label          // Branch to label if X1 == 0
```

### Using Labels

```assembly
main:
    ADDI X1, XZR, #10
  
loop:
    SUBI X1, X1, #1
    CBNZ X1, loop        // Branch to loop if X1 != 0
  
end:
    // Program end
```

### File Upload

1. **Create a .s .txt .asm file** with LEGv8 assembly code
2. **Click "Upload File"** button
3. **Select your file**
4. **Code appears** in the editor
5. **Click "Compile Code"** to load

## Monitoring Execution

### Watching Data Flow

- **Active components** are highlighted in pink
- **Data paths** show animated signal flow
- **Values** move along the paths during animation
- **Multiple paths** can be active simultaneously

### Understanding Flags

The flags register shows four condition flags:

- **N (Negative)**: Result is negative
- **Z (Zero)**: Result is zero
- **C (Carry)**: Carry occurred in arithmetic
- **V (Overflow)**: Signed overflow occurred

**Visual indicators**:

- **Pink highlight**: Flag is set (1)
- **Normal color**: Flag is clear (0)

### Reading Control Signals

Control signals determine processor behavior:

- **RegWrite**: Enable register writing
- **ALUSrc**: Select ALU input source
- **MemRead/MemWrite**: Memory access control
- **Branch**: Enable branch logic
- **And more...**

## Debugging Features

### Step-by-Step Debugging

1. **Set breakpoints** by stepping through manually
2. **Examine state** at each step
3. **Use Return Back** to go to previous states
4. **Check flags** after arithmetic operations
5. **Monitor memory** for load/store operations

### Common Issues

**Program won't load**:

- Check syntax errors in the log
- Verify instruction spelling
- Ensure proper register names

**Unexpected results**:

- Use micro-step mode to see details
- Check initial register values
- Verify memory addresses

**Visualization not working**:

- Ensure JavaScript is enabled
- Try refreshing the page
- Check browser console for errors
