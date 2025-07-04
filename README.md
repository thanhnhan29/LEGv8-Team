# LEGv8 Processor Simulator

A comprehensive web-based simulator for the LEGv8 instruction set architecture with real-time datapath visualization and interactive debugging capabilities.

![LEGv8 Simulator](https://img.shields.io/badge/LEGv8-Simulator-blue)
![Python](https://img.shields.io/badge/Python-3.9+-green)
![JavaScript](https://img.shields.io/badge/JavaScript-ES6+-yellow)

## 🎯 Overview

This educational simulator provides an interactive platform for understanding processor architecture and instruction execution. Built with Python Flask backend and JavaScript frontend, it offers detailed visualization of the LEGv8 datapath with comprehensive instruction-level simulation.

## ✨ Key Features

- **🔄 Multiple Execution Modes**: Micro-step, full instruction, and auto-run
- **📊 Real-time Visualization**: Interactive datapath with component highlighting
- **🎛️ State Monitoring**: Registers, memory, flags, and control signals
- **⏪ Return Back**: Navigate to previous instruction states
- **🛠️ Debug Tools**: Syntax highlighting, error detection, execution history

## 🚀 Quick Start

1. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```
2. **Run the simulator**

   ```bash
   python app.py
   ```
3. **Open browser**
   Navigate to `http://localhost:5010`
4. **Try sample code**

   ```assembly
   ADDI X1, XZR, #10
   ADDI X2, XZR, #5
   ADD  X3, X1, X2
   ```

## 📚 Documentation

- **[Installation Guide](docs/INSTALLATION.md)** - Detailed setup instructions
- **[User Manual](docs/USER_MANUAL.md)** - How to use the simulator
- **[Instruction Reference](docs/INSTRUCTIONS.md)** - Supported LEGv8 instructions

## 🛠️ Supported Instructions

**R-Type**: `ADD`, `ADDS`, `SUB`, `SUBS`, `AND`, `ORR`, `EOR`, `LSL`, `LSR`
**I-Type**: `ADDI`, `SUBI`, `ANDI`, `ORRI`, `EORI`,
**D-Type**: `LDUR`, `STUR`
**CB-Type**: `CBZ`, `CBNZ`, `B.EQ`, `B.NE`, `B.LT`, `B.LE`, `B.GT`, `B.GE`
**B-Type**: `B`

## 📁 Project Structure

```
LEGv8-Team/
├── app.py              # Main Flask application
├── simulator/          # Core simulation engine
├── static/            # Frontend assets
├── templates/         # HTML templates
└── docs/             # Documentation
```

## 📄 License

This project is licensed under the MIT License.

---

**Get started with LEGv8 architecture learning!** 🎓
