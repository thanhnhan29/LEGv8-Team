# LEGv8 Processor Simulator

A comprehensive web-based simulator for the LEGv8 instruction set architecture, featuring real-time datapath visualization, micro-step execution, and interactive debugging capabilities.

## Introduction

This LEGv8 Simulator provides an educational platform for understanding processor architecture and instruction execution. Built with a Python Flask backend and JavaScript frontend, it offers detailed visualization of the LEGv8 datapath and supports comprehensive instruction-level simulation.

The simulator is designed for computer architecture students and educators who need to visualize how instructions flow through a processor's datapath, understand pipeline stages, and observe register/memory state changes in real-time.

## Key Features

### Execution Modes

- **Micro-Step Execution**: Execute individual pipeline stages (Fetch → Decode → Execute → Memory → Write Back)
- **Full Instruction Step**: Execute complete instructions with all micro-steps
- **Auto Run Mode**: Continuous execution with adjustable speed control
- **Return Back**: Navigate to previous instruction states for debugging

### Interactive Visualization

- **Real-time Datapath Animation**: Visual representation of data flow through processor components
- **Component Highlighting**: Active blocks and data paths are highlighted during execution
- **Signal Animation**: Animated data values moving along processor connections
- **Control Signal Display**: Real-time status of all control signals

### State Monitoring

- **Register File Viewer**: Complete view of all 32 registers (X0-X27, SP, FP, LR, XZR)
- **Memory Browser**: Data memory contents with hex and decimal displays
- **Flags Register**: Real-time N, Z, C, V flag status with visual indicators
- **PC Tracking**: Program Counter visualization and instruction addressing

### Development Tools

- **Syntax Highlighting**: LEGv8 assembly code editor with syntax coloring
- **Error Detection**: Comprehensive error reporting for invalid instructions
- **File Upload**: Load assembly programs from external files
- **History Navigation**: Step-by-step execution history with return capability

## Supported Instruction Types

### R-Type Instructions (Register Operations)

- **Arithmetic**: `ADD`, `ADDS`, `SUB`, `SUBS`
- **Logical**: `AND`, `ANDS`, `ORR`, `EOR`
- **Shift**: `LSL`, `LSR`

### I-Type Instructions (Immediate Operations)

- **Arithmetic**: `ADDI`, `SUBI`
- **Logical**: `ANDI`, `ORRI`, `EORI`

### D-Type Instructions (Data Transfer)

- **Load**: `LDUR` (Load Unscaled Register)
- **Store**: `STUR` (Store Unscaled Register)

### CB-Type Instructions (Conditional Branch)

- **Zero Branches**: `CBZ`, `CBNZ`
- **Flag Branches**: `B.EQ`, `B.NE`, `B.LT`, `B.LE`, `B.GT`, `B.GE`
- **Unsigned Branches**: `B.LO`, `B.LS`, `B.HI`, `B.HS`

### B-Type Instructions (Unconditional Branch)

- **Jump**: `B` (Unconditional branch)

### Flag-Setting Operations

- **Arithmetic with Flags**: `ADDS`, `SUBS` automatically update N, Z, C, V flags
- **Test Operations**: `ANDS` sets flags for logical testing

## Getting Started

### Prerequisites

- Python 3.8+
- Flask
- Modern web browser with JavaScript support

### Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/thanhnhan29/LEGv8-Team
   cd LEGv8-Team
   ```
2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```
3. **Run the simulator**

   ```bash
   python app.py
   ```
4. **Open your browser**
   Navigate to `http://localhost:5010`

### Quick Start Example

```assembly
// Sample LEGv8 Program
ADDI X1, XZR, #10        // X1 = 10
ADDI X2, XZR, #5         // X2 = 5
ADD  X3, X1, X2          // X3 = X1 + X2
STUR X3, [SP, #8]        // Store X3 to memory
LDUR X4, [SP, #8]        // Load from memory to X4

loop:
    SUBI X2, X2, #1      // X2--
    CBZ  X2, end         // Branch if X2 == 0
    B    loop            // Unconditional branch

end:
    // Program end
```

## Project Structure

```
LEGv8-Team/
├── app.py                    # Flask web server
├── simulator/               # Core simulation engine
│   ├── simulator_engine.py  # Main simulator logic
│   ├── instruction_handlers.py # Instruction implementation
│   ├── register_file.py     # Register file management
│   ├── memory.py            # Memory simulation
│   ├── alu.py              # ALU operations
│   ├── control_unit.py     # Control signal generation
│   └── flags_register.py   # Flags management
├── static/                 # Frontend assets
│   ├── script.js          # Main JavaScript logic
│   ├── style.css          # Styling
│   └── test2.svg          # Datapath visualization
├── templates/             # HTML templates
│   └── index.html         # Main interface
└── README.md              # This file
```

## Usage Guide

### Loading a Program

1. Enter LEGv8 assembly code in the editor or upload a `.s, .txt, .asm` file
2. Click "Compile Code" to load and validate the program
3. The datapath will initialize and show the first instruction

### Execution Modes

#### Micro-Step Mode

- Click "Micro Step" to execute individual pipeline stages
- Observe each stage: Fetch → Decode → Execute → Memory → Write Back
- Watch data flow animations and component highlighting

#### Full Instruction Mode

- Click "Full Instruction" to execute complete instructions
- All micro-steps execute sequentially with visual feedback
- Ideal for observing complete instruction behavior

#### Auto Run Mode

- Click "Run" to start continuous execution
- Adjust speed with the animation speed slider (1-10 seconds)
- Click "Pause" to stop at any time

#### Return Back Feature

- Click "Return Back" to navigate to the previous instruction state
- Useful for debugging and understanding instruction effects
- Complete state restoration including registers, memory, and flags

### Monitoring System State

#### Registers Tab

- View all 32 registers in real-time
- Displays values in both hexadecimal and signed decimal
- Special registers (SP, FP, LR, XZR) highlighted

#### Memory Tab

- Browse data memory contents
- Address and value display in hex/decimal
- Automatic updates when memory operations occur

#### Control Signals Tab

- Real-time display of all control signals
- Color-coded active/inactive states
- Helps understand instruction control flow

#### Flags Tab

- Visual representation of N, Z, C, V flags
- Real-time updates during flag-setting operations
- Essential for understanding conditional branches

## Advanced Features

### Animation System

- GSAP-powered smooth animations
- Configurable animation speed
- Toggle animations on/off for performance
- Signal flow visualization along datapaths

### History System

- Instruction-level state snapshots
- Complete system state preservation
- Return back to any previous instruction
- Memory and register state restoration

### Debugging Tools

- Step-by-step execution tracing
- Real-time state monitoring
- Execution log with detailed information
- Interactive datapath exploration

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Computer Architecture course materials
- LEGv8 instruction set specifications
- Open-source visualization libraries
- Educational computer architecture community

## Support

For questions, issues, or feature requests:

- Open an issue on GitHub
- Contact the development team
- Check the documentation wiki

---

**Happy Learning with LEGv8 Simulator!**
