# LEGv8 Instruction Reference

## Overview

This document provides a comprehensive reference for all LEGv8 instructions supported by the simulator.

## Instruction Format Types

### R-Type (Register Format)

**Format**: `INSTRUCTION Rd, Rn, Rm`

- `Rd`: Destination register
- `Rn`: First source register
- `Rm`: Second source register

### I-Type (Immediate Format)

**Format**: `INSTRUCTION Rd, Rn, #imm`

- `Rd`: Destination register
- `Rn`: Source register
- `#imm`: Immediate value

### D-Type (Data Transfer Format)

**Format**: `INSTRUCTION Rt, [Rn, #offset]`

- `Rt`: Transfer register
- `Rn`: Base address register
- `#offset`: Address offset

### CB-Type (Conditional Branch Format)

**Format**: `INSTRUCTION Rt, label`

- `Rt`: Register to test
- `label`: Branch target

### B-Type (Branch Format)

**Format**: `INSTRUCTION label`

- `label`: Branch target

## Arithmetic Instructions

### ADD - Add (R-Type)

**Syntax**: `ADD Rd, Rn, Rm`
**Operation**: `Rd = Rn + Rm`
**Flags**: None
**Example**:

```assembly
ADD X1, X2, X3    // X1 = X2 + X3
```

### ADDS - Add and Set Flags (R-Type)

**Syntax**: `ADDS Rd, Rn, Rm`
**Operation**: `Rd = Rn + Rm`
**Flags**: Updates N, Z, C, V
**Example**:

```assembly
ADDS X1, X2, X3   // X1 = X2 + X3, set flags
```

### ADDI - Add Immediate (I-Type)

**Syntax**: `ADDI Rd, Rn, #imm`
**Operation**: `Rd = Rn + imm`
**Flags**: None
**Range**: -2048 to +2047
**Example**:

```assembly
ADDI X1, X2, #10  // X1 = X2 + 10
```

### SUB - Subtract (R-Type)

**Syntax**: `SUB Rd, Rn, Rm`
**Operation**: `Rd = Rn - Rm`
**Flags**: None
**Example**:

```assembly
SUB X1, X2, X3    // X1 = X2 - X3
```

### SUBS - Subtract and Set Flags (R-Type)

**Syntax**: `SUBS Rd, Rn, Rm`
**Operation**: `Rd = Rn - Rm`
**Flags**: Updates N, Z, C, V
**Example**:

```assembly
SUBS X1, X2, X3   // X1 = X2 - X3, set flags
```

### SUBI - Subtract Immediate (I-Type)

**Syntax**: `SUBI Rd, Rn, #imm`
**Operation**: `Rd = Rn - imm`
**Flags**: None
**Range**: -2048 to +2047
**Example**:

```assembly
SUBI X1, X2, #5   // X1 = X2 - 5
```

## Logical Instructions

### AND - Bitwise AND (R-Type)

**Syntax**: `AND Rd, Rn, Rm`
**Operation**: `Rd = Rn & Rm`
**Flags**: None
**Example**:

```assembly
AND X1, X2, X3    // X1 = X2 & X3
```

### ANDS - Bitwise AND and Set Flags (R-Type)

**Syntax**: `ANDS Rd, Rn, Rm`
**Operation**: `Rd = Rn & Rm`
**Flags**: Updates N, Z (C=0, V unchanged)
**Example**:

```assembly
ANDS X1, X2, X3   // X1 = X2 & X3, set flags
```

### ANDI - Bitwise AND Immediate (I-Type)

**Syntax**: `ANDI Rd, Rn, #imm`
**Operation**: `Rd = Rn & imm`
**Flags**: None
**Range**: 0 to 4095
**Example**:

```assembly
ANDI X1, X2, #15  // X1 = X2 & 15
```

### ORR - Bitwise OR (R-Type)

**Syntax**: `ORR Rd, Rn, Rm`
**Operation**: `Rd = Rn | Rm`
**Flags**: None
**Example**:

```assembly
ORR X1, X2, X3    // X1 = X2 | X3
```

### ORRI - Bitwise OR Immediate (I-Type)

**Syntax**: `ORRI Rd, Rn, #imm`
**Operation**: `Rd = Rn | imm`
**Flags**: None
**Range**: 0 to 4095
**Example**:

```assembly
ORRI X1, X2, #7   // X1 = X2 | 7
```

### EOR - Bitwise XOR (R-Type)

**Syntax**: `EOR Rd, Rn, Rm`
**Operation**: `Rd = Rn ^ Rm`
**Flags**: None
**Example**:

```assembly
EOR X1, X2, X3    // X1 = X2 ^ X3
```

### EORI - Bitwise XOR Immediate (I-Type)

**Syntax**: `EORI Rd, Rn, #imm`
**Operation**: `Rd = Rn ^ imm`
**Flags**: None
**Range**: 0 to 4095
**Example**:

```assembly
EORI X1, X2, #255 // X1 = X2 ^ 255
```

## Shift Instructions

### LSL - Logical Shift Left (R-Type)

**Syntax**: `LSL Rd, Rn, #shamt`
**Operation**: `Rd = Rn << shamt`
**Flags**: None
**Range**: 0 to 63
**Example**:

```assembly
LSL X1, X2, #4    // X1 = X2 << 4
```

### LSR - Logical Shift Right (R-Type)

**Syntax**: `LSR Rd, Rn, #shamt`
**Operation**: `Rd = Rn >> shamt` (unsigned)
**Flags**: None
**Range**: 0 to 63
**Example**:

```assembly
LSR X1, X2, #2    // X1 = X2 >> 2
```

## Data Transfer Instructions

### LDUR - Load Unscaled Register (D-Type)

**Syntax**: `LDUR Rt, [Rn, #offset]`
**Operation**: `Rt = Memory[Rn + offset]`
**Flags**: None
**Range**: -256 to +255
**Example**:

```assembly
LDUR X1, [X2, #8] // X1 = Memory[X2 + 8]
```

### STUR - Store Unscaled Register (D-Type)

**Syntax**: `STUR Rt, [Rn, #offset]`
**Operation**: `Memory[Rn + offset] = Rt`
**Flags**: None
**Range**: -256 to +255
**Example**:

```assembly
STUR X1, [X2, #8] // Memory[X2 + 8] = X1
```

## Branch Instructions

### B - Unconditional Branch (B-Type)

**Syntax**: `B label`
**Operation**: `PC = label`
**Flags**: None
**Example**:

```assembly
B loop            // Jump to loop
```

### CBZ - Compare and Branch if Zero (CB-Type)

**Syntax**: `CBZ Rt, label`
**Operation**: `if (Rt == 0) PC = label`
**Flags**: None
**Example**:

```assembly
CBZ X1, end       // Branch to end if X1 == 0
```

### CBNZ - Compare and Branch if Not Zero (CB-Type)

**Syntax**: `CBNZ Rt, label`
**Operation**: `if (Rt != 0) PC = label`
**Flags**: None
**Example**:

```assembly
CBNZ X1, loop     // Branch to loop if X1 != 0
```

## Conditional Branch Instructions

### B.EQ - Branch if Equal

**Syntax**: `B.EQ label`
**Operation**: `if (Z == 1) PC = label`
**Condition**: Last result was zero
**Example**:

```assembly
CMP X1, X2
B.EQ equal        // Branch if X1 == X2
```

### B.NE - Branch if Not Equal

**Syntax**: `B.NE label`
**Operation**: `if (Z == 0) PC = label`
**Condition**: Last result was not zero
**Example**:

```assembly
CMP X1, X2
B.NE not_equal    // Branch if X1 != X2
```

### B.LT - Branch if Less Than (Signed)

**Syntax**: `B.LT label`
**Operation**: `if (N != V) PC = label`
**Condition**: Signed less than
**Example**:

```assembly
CMP X1, X2
B.LT less         // Branch if X1 < X2 (signed)
```

### B.LE - Branch if Less Than or Equal (Signed)

**Syntax**: `B.LE label`
**Operation**: `if (Z == 1 || N != V) PC = label`
**Condition**: Signed less than or equal
**Example**:

```assembly
CMP X1, X2
B.LE less_equal   // Branch if X1 <= X2 (signed)
```

### B.GT - Branch if Greater Than (Signed)

**Syntax**: `B.GT label`
**Operation**: `if (Z == 0 && N == V) PC = label`
**Condition**: Signed greater than
**Example**:

```assembly
CMP X1, X2
B.GT greater      // Branch if X1 > X2 (signed)
```

### B.GE - Branch if Greater Than or Equal (Signed)

**Syntax**: `B.GE label`
**Operation**: `if (N == V) PC = label`
**Condition**: Signed greater than or equal
**Example**:

```assembly
CMP X1, X2
B.GE greater_equal // Branch if X1 >= X2 (signed)
```

```## Register Reference

### General Purpose Registers

- **X0-X27**: General purpose (64-bit)
- **X28 (SP)**: Stack pointer
- **X29 (FP)**: Frame pointer
- **X30 (LR)**: Link register
- **XZR**: Zero register (always 0)

### Flags Register

- **N**: Negative flag
- **Z**: Zero flag
- **C**: Carry flag
- **V**: Overflow flag

## Instruction Usage Examples

### Simple Program

```assembly
// Load values
ADDI X1, XZR, #10
ADDI X2, XZR, #5

// Arithmetic
ADD X3, X1, X2
SUB X4, X1, X2

// Memory operations
STUR X3, [SP, #0]
LDUR X5, [SP, #0]
```
### Loop Example

```assembly
// Initialize counter
ADDI X1, XZR, #10

loop:
    // Loop body
    SUBI X1, X1, #1
  
    // Continue if not zero
    CBNZ X1, loop
  
// End of program
```

```
