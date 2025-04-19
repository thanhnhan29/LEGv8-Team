# -*- coding: utf-8 -*-
# SINGLE FILE ARMv8 SIMULATOR (Flask Web App)
# REFACTORED FOR BINARY OPCODES

from flask import Flask, render_template, request, jsonify
import re
import sys
import traceback
import copy

# ==============================================================================
# Binary Encoding Definitions & Helpers
# ==============================================================================

# --- Opcode Bit Patterns (Based on Slides/Standard ARMv8) ---
# Note: These are the primary identifying bits. Other fields fill the rest.
# Use masks to easily check formats.
OPCODE_MASK_R = 0b11111000000000000000000000000000 # Check bits 31-21
OPCODE_MASK_I = 0b11111110000000000000000000000000 # Check bits 31-23 (for ADDI/SUBI)
OPCODE_MASK_D = 0b11111000000000000000000000000000 # Check bits 31-21 (for LDUR/STUR)
OPCODE_MASK_CB = 0b11111111000000000000000000000000 # Check bits 31-24
OPCODE_MASK_B = 0b11111100000000000000000000000000 # Check bits 31-26

# Specific Opcodes (Using the values from Slide 28/29 where available)
# Shifted to align within a 32-bit word
OP_ADD = 0b10001011000 << 21
OP_SUB = 0b11001011000 << 21
OP_AND = 0b10001010000 << 21
OP_ORR = 0b10101010000 << 21
OP_MUL = 0b10011011000 << 21 # Assumed MADD Rd, Rn, Rm, XZR encoding
OP_DIV = 0b10011010110 << 21 # Assumed SDIV Rd, Rn, Rm encoding

# Assuming common patterns for others
OP_ADDI = 0b100100010 << 23 # Matches I-format mask
OP_SUBI = 0b110100010 << 23 # Matches I-format mask

OP_LDUR = 0b11111000010 << 21 # Matches D-format mask (64-bit)
OP_STUR = 0b11111000000 << 21 # Matches D-format mask (64-bit)

OP_CBZ = 0b10110100 << 24 # Matches CB-format mask
# For B, need to consider B vs BL. Assume B
OP_B = 0b000101 << 26 # Matches B-format mask

# NOP is often encoded specifically (e.g., HINT instruction or MOV XZR, XZR)
# Using a common HINT encoding for NOP
OP_NOP = 0xD503201F # Special case

# --- Register Name to Index Mapping ---
def reg_name_to_index(reg_name):
    """Converts register name (X0, XZR, SP) to its 5-bit index."""
    reg_name = reg_name.upper()
    if reg_name == "XZR": return 31
    if reg_name == "SP": return 28
    if reg_name.startswith("X"):
        try:
            idx = int(reg_name[1:])
            if 0 <= idx <= 30: # Allow X0-X30 explicitly
                 return idx
            # Note: X31 is technically valid but maps to XZR, handled above.
            # We *don't* allow direct use of "X31" string here.
            else:
                 raise ValueError(f"Invalid register index: {reg_name}")
        except ValueError:
            raise ValueError(f"Invalid register format: {reg_name}")
    raise ValueError(f"Unknown register name: {reg_name}")

# --- Encoding Functions ---
def encode_r(op_bits, rd_str, rn_str, rm_str):
    rd = reg_name_to_index(rd_str)
    rn = reg_name_to_index(rn_str)
    rm = reg_name_to_index(rm_str)
    shamt = 0 # Assuming shamt=0 for basic R-types
    instr = op_bits # Base opcode bits (already shifted)
    instr |= (rm & 0x1F) << 16
    instr |= (shamt & 0x3F) << 10
    instr |= (rn & 0x1F) << 5
    instr |= (rd & 0x1F) << 0
    return instr

def encode_i(op_bits, rd_str, rn_str, imm_val):
    rd = reg_name_to_index(rd_str)
    rn = reg_name_to_index(rn_str)
    # I-format immediate is 12 bits (bits 21-10)
    if not (-2048 <= imm_val <= 2047):
         print(f"[Warning] Immediate {imm_val} for I-format exceeds 12-bit signed range. Truncating.")
    instr = op_bits # Base opcode bits (already shifted)
    instr |= (imm_val & 0xFFF) << 10 # Mask to 12 bits
    instr |= (rn & 0x1F) << 5
    instr |= (rd & 0x1F) << 0
    return instr

def encode_d(op_bits, rt_str, rn_str, imm_val):
    rt = reg_name_to_index(rt_str) # Rt is target/source
    rn = reg_name_to_index(rn_str) # Rn is base address
    # D-format immediate is 9 bits (bits 20-12)
    if not (0 <= imm_val <= 511): # Usually unsigned for base LDUR/STUR offset
         print(f"[Warning] Immediate {imm_val} for D-format exceeds 9-bit unsigned range. Truncating.")
    op2 = 0 # op2 field (bits 11-10) = 0 for basic LDUR/STUR
    instr = op_bits # Base opcode bits (already shifted)
    instr |= (imm_val & 0x1FF) << 12 # Mask to 9 bits
    instr |= (op2 & 0x3) << 10
    instr |= (rn & 0x1F) << 5
    instr |= (rt & 0x1F) << 0
    return instr

def encode_cb(op_bits, rt_str, offset_val):
    rt = reg_name_to_index(rt_str)
    # CB-format offset is 19 bits (bits 23-5), signed, byte offset / 4
    imm19 = offset_val >> 2 # Convert byte offset to instruction offset
    if not (-(1 << 18) <= imm19 <= (1 << 18) - 1):
         print(f"[Warning] Branch offset {offset_val} (imm19={imm19}) exceeds 19-bit signed range. Truncating.")
    instr = op_bits # Base opcode bits (already shifted)
    instr |= (imm19 & 0x7FFFF) << 5 # Mask to 19 bits
    instr |= (rt & 0x1F) << 0
    return instr

def encode_b(op_bits, offset_val):
    # B-format offset is 26 bits (bits 25-0), signed, byte offset / 4
    imm26 = offset_val >> 2 # Convert byte offset to instruction offset
    if not (-(1 << 25) <= imm26 <= (1 << 25) - 1):
         print(f"[Warning] Branch offset {offset_val} (imm26={imm26}) exceeds 26-bit signed range. Truncating.")
    instr = op_bits # Base opcode bits (already shifted)
    instr |= (imm26 & 0x3FFFFFF) << 0 # Mask to 26 bits
    return instr

# ==============================================================================
# Binary Decoding Helpers
# ==============================================================================
def get_opcode_r(instr_bin): return instr_bin & OPCODE_MASK_R # Bits 31-21
def get_opcode_i(instr_bin): return instr_bin & OPCODE_MASK_I # Bits 31-23
def get_opcode_d(instr_bin): return instr_bin & OPCODE_MASK_D # Bits 31-21
def get_opcode_cb(instr_bin): return instr_bin & OPCODE_MASK_CB # Bits 31-24
def get_opcode_b(instr_bin): return instr_bin & OPCODE_MASK_B # Bits 31-26

def get_rd(instr_bin): return (instr_bin >> 0) & 0x1F
def get_rt(instr_bin): return (instr_bin >> 0) & 0x1F # Same field as Rd
def get_rn(instr_bin): return (instr_bin >> 5) & 0x1F
def get_rm(instr_bin): return (instr_bin >> 16) & 0x1F
def get_shamt(instr_bin): return (instr_bin >> 10) & 0x3F
def get_imm12_i(instr_bin): return (instr_bin >> 10) & 0xFFF
def get_imm9_d(instr_bin): return (instr_bin >> 12) & 0x1FF
def get_imm19_cb(instr_bin): return (instr_bin >> 5) & 0x7FFFF
def get_imm26_b(instr_bin): return (instr_bin >> 0) & 0x3FFFFFF

def reg_index_to_name(index):
    """Converts 5-bit index back to name (Xn, SP, XZR) for logging."""
    if index == 31: return "XZR"
    if index == 28: return "SP"
    if 0 <= index <= 30: return f"X{index}"
    return f"Invalid({index})"

# ==============================================================================
# Phần lõi mô phỏng: Helpers, Hardware Blocks, Muxes (Mostly Unchanged)
# ==============================================================================
# ... (Keep the existing pc_plus_4_adder, sign_extend, alu, branch_target_adder,
#       mux functions, MicroStepState class, branch_control_logic) ...
class MicroStepState:
    """ Represents the state of the datapath at a specific micro-step for visualization. """
    def __init__(self, stage, micro_step_index, log_msg="", blocks=None, paths=None, signals=None, controls=None):
        self.stage = stage                    # Name of the pipeline stage (e.g., "Fetch")
        self.micro_step_index = micro_step_index # Index within the instruction (0-4)
        self.log_entry = log_msg              # Descriptive log message for this step
        self.active_blocks = blocks if blocks else [] # IDs of highlighted hardware blocks
        self.active_paths = paths if paths else []   # IDs of highlighted data paths
        self.animated_signals = signals if signals else [] # Details for animating signals on paths
        self.control_signals = controls if controls else {} # Values of control signals for this instr

    def to_dict(self):
        """ Returns a JSON-serializable dictionary representation. """
        return {
            "stage": self.stage,
            "micro_step_index": self.micro_step_index,
            "log_entry": self.log_entry,
            "active_blocks": self.active_blocks,
            "active_paths": self.active_paths,
            "animated_signals": self.animated_signals,
            "control_signals": self.control_signals,
            # current_instruction_address/string are added later in the API endpoint
        }
# --- Modified Register/Memory Helpers ---
def read_register(registers_dict, reg_index):
    """ Reads a value from the register dictionary using index. """
    reg_name = reg_index_to_name(reg_index) # Convert index to name for internal dict key
    return read_register_by_name(registers_dict, reg_name) # Use existing name-based logic

def write_register(registers_dict, reg_index, value):
    """ Writes a value to the register dictionary using index. """
    reg_name = reg_index_to_name(reg_index)
    # Prevent writing to the Zero Register (Index 31)
    if reg_index != 31:
        # Ensure register name derived from index is valid before writing
        if reg_name.startswith("X") or reg_name == "SP":
             # Check if register exists (mainly for safety, X0-X30 and SP should exist)
             if reg_name == "SP": # Use the internal X28 key for SP
                  if "X28" in registers_dict:
                      written_value = int(value) & 0xFFFFFFFFFFFFFFFF
                      registers_dict["X28"] = written_value
                  else:
                       raise ValueError(f"Internal Error: Register 'X28' (for SP) not found.")
             elif reg_name in registers_dict:
                 written_value = int(value) & 0xFFFFFFFFFFFFFFFF
                 registers_dict[reg_name] = written_value
             else:
                  raise ValueError(f"Invalid register write target: Register '{reg_name}' (Index {reg_index}) does not exist.")
        else:
             # This case should ideally not be reached if reg_index_to_name is correct
             raise ValueError(f"Invalid register name derived from index: '{reg_name}' (Index {reg_index})")
    # else: Writes to XZR (Index 31) are silently ignored

# Keep original name-based functions for convenience if needed elsewhere,
# but core execution will use index-based wrappers.
def read_register_by_name(registers_dict, reg_name):
    reg_name = reg_name.upper()
    if reg_name == "XZR" or reg_name == "X31": return 0
    if reg_name == "SP": reg_name = "X28"
    val = registers_dict.get(reg_name)
    if val is None: raise ValueError(f"Invalid register read: Register '{reg_name}' does not exist.")
    return int(val) & 0xFFFFFFFFFFFFFFFF

def write_register_by_name(registers_dict, reg_name, value):
    reg_name = reg_name.upper()
    if reg_name not in ["XZR", "X31"]:
        if reg_name == "SP": reg_name = "X28"
        if reg_name in registers_dict:
            written_value = int(value) & 0xFFFFFFFFFFFFFFFF
            registers_dict[reg_name] = written_value
        else:
            raise ValueError(f"Invalid register write target: Register '{reg_name}' does not exist.")

def read_memory(data_mem_dict, address):
    address = int(address)
    value = data_mem_dict.get(address, 0)
    return int(value) & 0xFFFFFFFFFFFFFFFF

def write_memory(data_mem_dict, address, value):
    address = int(address)
    value = int(value)
    written_value = value & 0xFFFFFFFFFFFFFFFF
    data_mem_dict[address] = written_value

# ... (Rest of Hardware Blocks, Muxes, MicroStepState remain the same) ...
def pc_plus_4_adder(current_pc):
    """ Simulates the adder that calculates PC + 4. """
    # <<< THÊM MASK 64-BIT >>>
    return (current_pc + 4) & 0xFFFFFFFFFFFFFFFF

def fetch_instruction_from_mem(instr_mem_dict, address):
    """ Fetches the instruction string from the instruction memory dictionary. """
    instr = instr_mem_dict.get(address)
    if instr is None:
        raise ValueError(f"Fetch Error: No instruction found at PC=0x{address:X}")
    return instr

def sign_extend(value, bits):
    """ Performs sign extension of 'value' from 'bits' length to 64 bits. """
    value = int(value)
    if bits <= 0 or bits >= 64:
        return value & 0xFFFFFFFFFFFFFFFF

    value_mask = (1 << bits) - 1
    value_masked = value & value_mask # Get the value within the bit range

    sign_bit_mask = 1 << (bits - 1)

    # Check if the sign bit is set
    if (value_masked & sign_bit_mask) != 0: # Negative number
        # Extend with 1s.
        # Create a mask for the upper bits that need to be set to 1.
        # Example: bits=19 -> need to set bits 19 through 63 to 1.
        # Mask = 0xFF...FF shifted left by 'bits'.
        # Python's ~0 is -1, which represents all 1s.
        upper_bits_mask = (~0 << bits)

        # OR the masked value with the upper bits mask
        extended_value = value_masked | upper_bits_mask

        # --- DEBUGGING PRINT ADDED INSIDE sign_extend ---
        # print(f"DEBUG sign_extend (Negative): value={value}, bits={bits}, value_masked=0x{value_masked:X}, upper_mask=0x{upper_bits_mask:X}, extended=0x{extended_value:X}")
        # --- END DEBUGGING PRINT ---

    else: # Positive number
        # Extend with 0s (value_masked already represents this)
        extended_value = value_masked
        # --- DEBUGGING PRINT ADDED INSIDE sign_extend ---
        # print(f"DEBUG sign_extend (Positive): value={value}, bits={bits}, value_masked=0x{value_masked:X}, extended=0x{extended_value:X}")
        # --- END DEBUGGING PRINT ---


    # Final mask to 64 bits (important in case intermediate results exceed it somehow)
    return extended_value & 0xFFFFFFFFFFFFFFFF
def alu(operand1, operand2, operation):
    """ Simulates the Arithmetic Logic Unit (ALU). """
    op1_int, op2_int = int(operand1), int(operand2)
    result = 0
    if operation == 'add': result = op1_int + op2_int
    elif operation == 'sub': result = op1_int - op2_int
    elif operation == 'and': result = op1_int & op2_int
    elif operation == 'orr': result = op1_int | op2_int
    elif operation == 'pass1': result = op1_int # Used for CBZ to check zero flag of operand1
    elif operation == 'mul': result = op1_int * op2_int
    elif operation == 'div':
        if op2_int == 0:
            raise ValueError("ALU Error: Division by zero.")
        # Integer division, // truncates towards negative infinity.
        # Use standard behavior which truncates towards zero for positive/negative numbers.
        result = int(op1_int / op2_int)
    else: raise ValueError(f"ALU Error: Operation '{operation}' not supported.")

    # Ensure result is 64-bit
    result_64 = result & 0xFFFFFFFFFFFFFFFF
    # Calculate Zero flag (1 if result is 0, otherwise 0)
    zero_flag = 1 if result_64 == 0 else 0
    return result_64, zero_flag

def branch_target_adder(base_pc, byte_offset):
    """ Simulates the adder that calculates the branch target address (PC + Offset).
        Ensures the result wraps around within 64 bits. """
    result = base_pc + byte_offset
    # Mask the result to 64 bits to simulate hardware behavior
    return result & 0xFFFFFFFFFFFFFFFF # <<< THÊM MASK 64-BIT

# --- Các Bộ Chọn (Mux) Mô Phỏng ---
def alu_input2_mux(reg_read_data2, sign_extended_imm, alu_src_signal):
    """ Simulates the MUX selecting the second ALU input.
        alu_src_signal: 0 selects ReadData2, 1 selects Immediate. """
    return sign_extended_imm if alu_src_signal == 1 else reg_read_data2

def writeback_data_mux(alu_result_data, mem_read_data, mem_to_reg_signal):
    """ Simulates the MUX selecting the data to be written back to registers.
        mem_to_reg_signal: 0 selects ALU result, 1 selects Memory data, -1 indicates no WB. """
    if mem_to_reg_signal == 0: return alu_result_data
    elif mem_to_reg_signal == 1: return mem_read_data
    elif mem_to_reg_signal == -1: return None # Indicate no write back needed (e.g., for STUR)
    else: raise ValueError(f"Mux Error: Invalid MemToReg signal: {mem_to_reg_signal}")

def pc_source_mux(pc_plus_4_val, branch_target_addr, pc_src_signal):
    """ Simulates the MUX selecting the next PC value.
        pc_src_signal: 0 selects PC+4, 1 selects Branch Target Address. """
    return branch_target_addr if pc_src_signal == 1 else pc_plus_4_val

# --- Logic Điều Khiển Nhánh ---
def branch_control_logic(branch_signal, zero_flag, uncond_branch_signal):
    """ Determines the PCSrc signal based on branch conditions. """
    # PCSrc = (Branch & Zero) | UncondBranch
    # Branch: Control signal for conditional branches (like CBZ) -> Is 1 for CBZ
    # Zero: ALU zero flag result (relevant for CBZ) -> Is 1 if Rt == 0
    # UncondBranch: Control signal for unconditional branches (like B) -> Is 1 for B
    pc_src = (branch_signal & zero_flag) | uncond_branch_signal
    # print(f"DEBUG Branch Logic: Branch={branch_signal}, Zero={zero_flag}, Uncond={uncond_branch_signal} -> PCSrc={pc_src}") # Optional Verbose Debug
    return pc_src
# ==============================================================================
# Control Signal Logic (REWRITTEN for Binary Opcodes)
# ==============================================================================

def calculate_control_signals(instr_bin):
    """ Determines control signals based on the 32-bit instruction binary. """
    # Default to NOP signals
    signals = {'RegWrite': 0, 'ALUSrc': 0, 'MemRead': 0, 'MemWrite': 0, 'MemToReg': 0, 'Branch': 0, 'UncondBranch': 0, 'ALUOp': 'XX'}

    if instr_bin == OP_NOP: # Handle NOP explicitly
         return signals

    # --- Check Formats using Masks and Specific Opcode Bits ---
    opcode_r = get_opcode_r(instr_bin)
    opcode_i = get_opcode_i(instr_bin)
    opcode_d = get_opcode_d(instr_bin)
    opcode_cb = get_opcode_cb(instr_bin)
    opcode_b = get_opcode_b(instr_bin)

    # R-Format Check (ADD, SUB, AND, ORR, MUL, DIV)
    # Need to check specific patterns within the R-mask range
    if opcode_r in [OP_ADD, OP_SUB, OP_AND, OP_ORR, OP_MUL, OP_DIV]:
         signals = {'RegWrite': 1, 'ALUSrc': 0, 'MemRead': 0, 'MemWrite': 0, 'MemToReg': 0, 'Branch': 0, 'UncondBranch': 0, 'ALUOp': '10'} # R-type uses ALUOp='10'
         # print(f"DEBUG Control: Matched R-Format (Op=0x{opcode_r:X})")

    # I-Format Check (ADDI, SUBI)
    elif opcode_i in [OP_ADDI, OP_SUBI]:
         signals = {'RegWrite': 1, 'ALUSrc': 1, 'MemRead': 0, 'MemWrite': 0, 'MemToReg': 0, 'Branch': 0, 'UncondBranch': 0, 'ALUOp': '00'} # I-type ALUOp='00'
         # print(f"DEBUG Control: Matched I-Format (Op=0x{opcode_i:X})")

    # D-Format Check (LDUR, STUR)
    elif opcode_d == OP_LDUR:
         signals = {'RegWrite': 1, 'ALUSrc': 1, 'MemRead': 1, 'MemWrite': 0, 'MemToReg': 1, 'Branch': 0, 'UncondBranch': 0, 'ALUOp': '00'} # LDUR uses ALUOp='00', MemToReg=1
         # print(f"DEBUG Control: Matched LDUR (Op=0x{opcode_d:X})")
    elif opcode_d == OP_STUR:
         signals = {'RegWrite': 0, 'ALUSrc': 1, 'MemRead': 0, 'MemWrite': 1, 'MemToReg': -1, 'Branch': 0, 'UncondBranch': 0, 'ALUOp': '00'} # STUR uses ALUOp='00', no WB (-1)
         # print(f"DEBUG Control: Matched STUR (Op=0x{opcode_d:X})")

    # CB-Format Check (CBZ)
    elif opcode_cb == OP_CBZ:
         signals = {'RegWrite': 0, 'ALUSrc': 0, 'MemRead': 0, 'MemWrite': 0, 'MemToReg': 0, 'Branch': 1, 'UncondBranch': 0, 'ALUOp': '01'} # CBZ uses ALUOp='01' (pass Rt), Branch=1
         # print(f"DEBUG Control: Matched CBZ (Op=0x{opcode_cb:X})")

    # B-Format Check (B)
    elif opcode_b == OP_B:
         signals = {'RegWrite': 0, 'ALUSrc': 0, 'MemRead': 0, 'MemWrite': 0, 'MemToReg': 0, 'Branch': 0, 'UncondBranch': 1, 'ALUOp': 'XX'} # B is UncondBranch=1, ALUOp='XX'
         # print(f"DEBUG Control: Matched B (Op=0x{opcode_b:X})")

    else:
         print(f"[WARN] Control Logic: Unknown instruction binary 0x{instr_bin:08X}. Using NOP signals.")
         # Keep default NOP signals

    # print(f"DEBUG Control Signals for 0x{instr_bin:08X}: {signals}") # Optional Verbose Debug
    return signals


# ==============================================================================
# Instruction-Specific Handlers (ADAPTED for Binary Decode Info)
# ==============================================================================
# These handlers are now mostly for logging and defining ALU operations.
# The core decoding happens in the main generator.

def determine_alu_operation(instr_bin, alu_op_control):
    """ Determines the specific ALU function based on instr bits and ALUOp control. """
    if alu_op_control == '00': # ADDI, SUBI, LDUR, STUR
        # Check specific I/D opcodes if needed, but here they all do 'add' for address/imm calc
        # Or distinguish ADDI/SUBI based on their distinct opcodes
        opcode_i = get_opcode_i(instr_bin)
        if opcode_i == OP_ADDI: return 'add'
        if opcode_i == OP_SUBI: return 'sub'
        opcode_d = get_opcode_d(instr_bin) # Check D-type opcodes
        if opcode_d == OP_LDUR or opcode_d == OP_STUR: return 'add'
        return 'add' # Default for ALUOp 00 if specific match fails

    elif alu_op_control == '01': # CBZ
        return 'pass1' # Special ALU op for CBZ to pass Rt and check zero flag

    elif alu_op_control == '10': # R-type
        opcode_r = get_opcode_r(instr_bin)
        if opcode_r == OP_ADD: return 'add'
        if opcode_r == OP_SUB: return 'sub'
        if opcode_r == OP_AND: return 'and'
        if opcode_r == OP_ORR: return 'orr'
        if opcode_r == OP_MUL: return 'mul'
        if opcode_r == OP_DIV: return 'div'
        raise ValueError(f"Unknown R-type opcode 0x{opcode_r:X} for ALUOp='10'")

    elif alu_op_control == 'XX': # B, NOP
        return None # No ALU operation needed
    else:
        raise ValueError(f"Invalid ALUOp control signal: {alu_op_control}")

# Handlers are now simpler - primarily log generation based on decoded info
# (The complex logic moved to the main generator's Decode step)

def log_decode_r(decoded_info):
    return (f"  Decode: R-format (Op=0x{decoded_info['opcode_val']:X}, "
            f"Rd={reg_index_to_name(decoded_info['rd_idx'])}, "
            f"Rn={reg_index_to_name(decoded_info['rn_idx'])}, "
            f"Rm={reg_index_to_name(decoded_info['rm_idx'])}), shamt={decoded_info['shamt_val']}")

def log_decode_i(decoded_info):
     return (f"  Decode: I-format (Op=0x{decoded_info['opcode_val']:X}, "
             f"Rd={reg_index_to_name(decoded_info['rd_idx'])}, "
             f"Rn={reg_index_to_name(decoded_info['rn_idx'])}, "
             f"Imm(12b)=0x{decoded_info['imm_val']:X} ({decoded_info['imm_val']}))")

def log_decode_d(decoded_info):
     format_type = "Load" if decoded_info['is_load'] else "Store"
     return (f"  Decode: D-format {format_type} (Op=0x{decoded_info['opcode_val']:X}, "
             f"Rt={reg_index_to_name(decoded_info['rt_idx'])}, "
             f"Rn={reg_index_to_name(decoded_info['rn_idx'])}, "
             f"Imm(9b)=0x{decoded_info['imm_val']:X} ({decoded_info['imm_val']}))")

def log_decode_cb(decoded_info):
     return (f"  Decode: CB-format (Op=0x{decoded_info['opcode_val']:X}, "
             f"Rt={reg_index_to_name(decoded_info['rt_idx'])}, "
             f"Offset(19b)=0x{decoded_info['branch_offset_val']:X} ({decoded_info['branch_offset_val']}))")

def log_decode_b(decoded_info):
     return (f"  Decode: B-format (Op=0x{decoded_info['opcode_val']:X}, "
             f"Offset(26b)=0x{decoded_info['branch_offset_val']:X} ({decoded_info['branch_offset_val']}))")

def log_decode_nop(decoded_info):
     return f"  Decode: NOP instruction (0x{decoded_info['instr_bin']:08X})."


# ==============================================================================
# Main Execution Generator (REWRITTEN with Binary Decode)
# ==============================================================================
def execute_instruction_detailed_generator(current_pc, registers_dict, data_mem_dict, instr_mem_dict):
    """
    Generator REWRITTEN for BINARY instruction execution.
    Yields MicroStepState objects for visualization.
    Returns a dictionary {'next_pc': value, 'error': msg} upon completion or error.
    """
    instruction_bin = 0       # Fetched 32-bit instruction
    raw_instruction_str = "(Not Fetched)" # Original text version for display
    final_next_pc = current_pc + 4 # Default next PC assumption
    pc_p4 = 0 # Calculated PC+4 value

    # State variables carried between stages
    control_values = {}       # Control signals for the current instruction
    decoded_info = {}         # Dictionary holding fields extracted from instruction_bin
    exec_result = {}          # Result from the execute stage logic
    mem_result = {}           # Result from the memory stage logic
    wb_log = ""               # Log message for WB stage

    read_data1, read_data2 = 0, 0 # Data read from register file
    sign_extended_imm = 0     # Sign-extended immediate value (various sizes)
    alu_result = 0            # Result from ALU
    alu_zero_flag = 0         # Zero flag from ALU
    data_read_from_mem = None # Data read from memory (initially None)
    branch_target_addr = 0    # Calculated branch target address

    current_stage_name = "Start" # For error reporting
    current_micro_step_index = -1

    try:
        # --- Micro-Step 0: Instruction Fetch (IF) ---
        current_stage_name = "Fetch"
        current_micro_step_index = 0
        stage_log_if = f"[{current_stage_name} @ PC=0x{current_pc:X}]\n"
        active_blocks_if = ["block-pc", "block-imem", "block-adder1"]
        active_paths_if = ["path-pc-imem", "path-pc-adder1"]
        animated_signals_if = [
            {"path_id": "path-pc-imem", "bits": [1], "duration": 0.3},
            {"path_id": "path-pc-adder1", "bits": [1], "duration": 0.2},
        ]
        try:
            # Fetch the 32-bit BINARY instruction
            instruction_bin = instr_mem_dict.get(current_pc) # instr_mem_dict now holds integers
            if instruction_bin is None:
                 raise ValueError(f"Fetch Error: No instruction found at PC=0x{current_pc:X}")
            # Get the raw string version for display later
            raw_instruction_str = sim_state['raw_instruction_memory'].get(current_pc, "(Raw string missing)")
            stage_log_if += f"  Fetched Instruction: 0x{instruction_bin:08X} (Raw: '{raw_instruction_str}')\n"
        except ValueError as e:
            stage_log_if += f"  Error: {e}\n"
            yield MicroStepState(current_stage_name, current_micro_step_index, stage_log_if, active_blocks_if, active_paths_if, animated_signals_if).to_dict()
            return {"next_pc": current_pc, "error": str(e)}

        pc_p4 = pc_plus_4_adder(current_pc)
        stage_log_if += f"  PC+4 Adder -> 0x{pc_p4:X}"
        active_paths_if.append("path-adder1-mux4-in0")
        animated_signals_if.append({"path_id": "path-adder1-mux4-in0", "bits":[1], "duration": 0.2, "start_delay": 0.2})
        yield MicroStepState(current_stage_name, current_micro_step_index, stage_log_if, active_blocks_if, active_paths_if, animated_signals_if).to_dict()
        final_next_pc = pc_p4


        # --- Micro-Step 1: Instruction Decode / Register Fetch (ID) ---
        current_stage_name = "Decode"
        current_micro_step_index = 1
        stage_log_id = f"[{current_stage_name}]\n"
        stage_log_id += f"  Decoding Instruction: 0x{instruction_bin:08X}\n"
        active_blocks_id = ["block-control", "block-regs"]
        active_paths_id = ["path-imem-out", "path-instr-control", "path-instr-regs"]
        animated_signals_id = [
            {"path_id": "path-imem-out", "bits":[1], "duration": 0.1},
            {"path_id": "path-instr-control", "bits":[1], "duration": 0.2},
            {"path_id": "path-instr-regs", "bits":[1], "duration": 0.2},
        ]

        try:
            # 1. Get Control Signals FIRST based on binary
            control_values = calculate_control_signals(instruction_bin)
            # stage_log_id += f"  Control Signals: {control_values}\n" # Optional: Verbose

            # 2. Decode Fields based on likely format indicated by control signals or opcode patterns
            decoded_info = {'instr_bin': instruction_bin} # Store the binary itself
            imm_val_extracted = 0
            imm_bits_for_sign_extend = 0
            branch_offset_extracted = 0
            branch_offset_bits = 0
            read_reg1_idx = None
            read_reg2_idx = None

            # Determine Format and Extract Fields
            opcode_r = get_opcode_r(instruction_bin)
            opcode_i = get_opcode_i(instruction_bin)
            opcode_d = get_opcode_d(instruction_bin)
            opcode_cb = get_opcode_cb(instruction_bin)
            opcode_b = get_opcode_b(instruction_bin)

            decode_log_func = log_decode_nop # Default log function
            decoded_info['opcode_val'] = instruction_bin # Fallback opcode value

            if instruction_bin == OP_NOP:
                decoded_info['format'] = 'NOP'
                decode_log_func = log_decode_nop
            elif opcode_r in [OP_ADD, OP_SUB, OP_AND, OP_ORR, OP_MUL, OP_DIV]:
                decoded_info['format'] = 'R'
                decoded_info['opcode_val'] = opcode_r
                decoded_info['rd_idx'] = get_rd(instruction_bin)
                decoded_info['rn_idx'] = get_rn(instruction_bin)
                decoded_info['rm_idx'] = get_rm(instruction_bin)
                decoded_info['shamt_val'] = get_shamt(instruction_bin)
                read_reg1_idx = decoded_info['rn_idx']
                read_reg2_idx = decoded_info['rm_idx']
                decode_log_func = log_decode_r
            elif opcode_i in [OP_ADDI, OP_SUBI]:
                decoded_info['format'] = 'I'
                decoded_info['opcode_val'] = opcode_i
                decoded_info['rd_idx'] = get_rd(instruction_bin)
                decoded_info['rn_idx'] = get_rn(instruction_bin)
                imm_val_extracted = get_imm12_i(instruction_bin)
                imm_bits_for_sign_extend = 12
                read_reg1_idx = decoded_info['rn_idx']
                # Sign extension happens below
                decode_log_func = log_decode_i
            elif opcode_d in [OP_LDUR, OP_STUR]:
                decoded_info['format'] = 'D'
                decoded_info['opcode_val'] = opcode_d
                decoded_info['rt_idx'] = get_rt(instruction_bin) # Rt is dest/src
                decoded_info['rn_idx'] = get_rn(instruction_bin) # Rn is base
                imm_val_extracted = get_imm9_d(instruction_bin)
                imm_bits_for_sign_extend = 9 # Usually unsigned, but sign_extend handles positive correctly
                read_reg1_idx = decoded_info['rn_idx'] # Read base register
                decoded_info['is_load'] = (opcode_d == OP_LDUR)
                if not decoded_info['is_load']: # STUR also reads Rt
                     read_reg2_idx = decoded_info['rt_idx']
                # Sign extension happens below
                decode_log_func = log_decode_d
            elif opcode_cb == OP_CBZ:
                decoded_info['format'] = 'CB'
                decoded_info['opcode_val'] = opcode_cb
                decoded_info['rt_idx'] = get_rt(instruction_bin)
                branch_offset_extracted = get_imm19_cb(instruction_bin)
                branch_offset_bits = 19
                read_reg1_idx = decoded_info['rt_idx'] # Read Rt for comparison
                # Branch offset sign extension happens in Execute
                decode_log_func = log_decode_cb
            elif opcode_b == OP_B:
                 decoded_info['format'] = 'B'
                 decoded_info['opcode_val'] = opcode_b
                 branch_offset_extracted = get_imm26_b(instruction_bin)
                 branch_offset_bits = 26
                 # Branch offset sign extension happens in Execute
                 decode_log_func = log_decode_b
            else:
                 decoded_info['format'] = 'Unknown'
                 # Keep NOP defaults
                 print(f"[WARN] Decode: Instruction 0x{instruction_bin:08X} did not match known format opcodes.")


            # Store extracted immediates before sign extension for logging
            if imm_bits_for_sign_extend > 0:
                 decoded_info['imm_val'] = imm_val_extracted
            if branch_offset_bits > 0:
                 decoded_info['branch_offset_val'] = branch_offset_extracted

            # Call the appropriate logging function
            stage_log_id += decode_log_func(decoded_info) + "\n"


            # 3. Perform Register Reads using INDICES
            if read_reg1_idx is not None:
                read_data1 = read_register(registers_dict, read_reg1_idx) # Use index-based read
                stage_log_id += f"  Read Register 1 ({reg_index_to_name(read_reg1_idx)}): 0x{read_data1:X}\n"
                active_paths_id.append("path-regs-rdata1")
                animated_signals_id.append({"path_id": "path-regs-rdata1", "bits":[1], "duration": 0.3, "start_delay": 0.2})
            if read_reg2_idx is not None:
                read_data2 = read_register(registers_dict, read_reg2_idx)
                stage_log_id += f"  Read Register 2 ({reg_index_to_name(read_reg2_idx)}): 0x{read_data2:X}\n"
                active_paths_id.append("path-regs-rdata2")
                animated_signals_id.append({"path_id": "path-regs-rdata2", "bits":[1], "duration": 0.3, "start_delay": 0.2})

            # 4. Perform Sign Extension (for I/D formats)
            if imm_bits_for_sign_extend > 0:
                sign_extended_imm = sign_extend(imm_val_extracted, imm_bits_for_sign_extend)
                decoded_info['imm_val_extended'] = sign_extended_imm # Store extended value
                stage_log_id += f"  Sign Extend Immediate ({imm_bits_for_sign_extend}b): Val=0x{imm_val_extracted:X} -> 0x{sign_extended_imm:X}\n"
                if "block-signext" not in active_blocks_id: active_blocks_id.append("block-signext")
                active_paths_id.extend(["path-instr-signext", "path-signext-out-mux2"])
                animated_signals_id.extend([
                    {"path_id": "path-instr-signext", "bits":[1], "duration": 0.2, "start_delay": 0.1},
                    {"path_id": "path-signext-out-mux2", "bits":[1], "duration": 0.3, "start_delay": 0.3}
                ])

            # Log branch offset info (extension happens in Execute)
            if branch_offset_bits > 0:
                 stage_log_id += f"  Branch Offset Value (from instruction): {branch_offset_extracted} ({branch_offset_bits}b)\n"
                 if "block-signext" not in active_blocks_id: active_blocks_id.append("block-signext")
                 active_paths_id.append("path-instr-signext-br")
                 animated_signals_id.append({"path_id": "path-instr-signext-br", "bits":[1], "duration": 0.2, "start_delay": 0.1})


            yield MicroStepState(current_stage_name, current_micro_step_index, stage_log_id, active_blocks_id, active_paths_id, animated_signals_id, control_values).to_dict()

        except (IndexError, ValueError, TypeError, KeyError) as e:
            stage_log_id += f"  Error: {e}\n traceback: {traceback.format_exc()}\n"
            yield MicroStepState(current_stage_name, current_micro_step_index, stage_log_id, active_blocks_id, active_paths_id, animated_signals_id, control_values).to_dict()
            return {"next_pc": pc_p4, "error": f"Decode Error: {e}"}


        # --- Micro-Step 2: Execute (EX) ---
        current_stage_name = "Execute"
        current_micro_step_index = 2
        stage_log_ex = f"[{current_stage_name}]\n"
        active_blocks_ex = ["block-alu", "block-alucontrol", "block-mux2"]
        active_paths_ex = []
        animated_signals_ex = []

        try:
            # 1. Determine ALU Inputs
            alu_src = control_values.get('ALUSrc', 0)
            alu_input1_val = read_data1
            # Use the sign-extended immediate if needed (stored in decoded_info)
            alu_input2_mux_imm = decoded_info.get('imm_val_extended', 0)
            alu_input2_val = alu_input2_mux(read_data2, alu_input2_mux_imm, alu_src)

            # Log ALU inputs
            rn_name = reg_index_to_name(decoded_info.get('rn_idx', -1)) if 'rn_idx' in decoded_info else 'N/A'
            rm_name = reg_index_to_name(decoded_info.get('rm_idx', -1)) if 'rm_idx' in decoded_info else 'N/A'
            stage_log_ex += f"  ALU Input 1 (from {rn_name}): 0x{alu_input1_val:X}\n"
            active_paths_ex.append("path-rdata1-alu")
            animated_signals_ex.append({"path_id": "path-rdata1-alu", "bits":[1], "duration": 0.2})
            if alu_src == 0:
                stage_log_ex += f"  ALU Input 2 (from {rm_name}): 0x{alu_input2_val:X} (Mux2 Sel=0)\n"
                active_paths_ex.extend(["path-regs-rdata2-mux2", "path-mux2-alu", "mux-alusrc-in0"])
                animated_signals_ex.extend([
                    {"path_id": "path-regs-rdata2-mux2", "bits":[1], "duration": 0.1},
                    {"path_id": "path-mux2-alu", "bits":[1], "duration": 0.1, "start_delay": 0.1}
                ])
            else:
                stage_log_ex += f"  ALU Input 2 (from Imm): 0x{alu_input2_val:X} (Mux2 Sel=1)\n"
                active_paths_ex.extend(["path-signext-mux2", "path-mux2-alu", "mux-alusrc-in1"])
                animated_signals_ex.extend([
                    {"path_id": "path-signext-mux2", "bits":[1], "duration": 0.1},
                    {"path_id": "path-mux2-alu", "bits":[1], "duration": 0.1, "start_delay": 0.1}
                ])

            # 2. Determine ALU Operation
            alu_op_control = control_values.get('ALUOp', 'XX')
            alu_operation_str = determine_alu_operation(instruction_bin, alu_op_control)

            # 3. Perform ALU Operation (if needed)
            if alu_operation_str:
                alu_result, alu_zero_flag = alu(alu_input1_val, alu_input2_val, alu_operation_str)
                exec_result['log'] = (f"  Execute: ALU Op='{alu_operation_str}' -> Result=0x{alu_result:X}, Zero={alu_zero_flag}\n")
                exec_result['alu_result'] = alu_result
                exec_result['alu_zero_flag'] = alu_zero_flag
                active_paths_ex.append("path-alu-result")
                animated_signals_ex.append({"path_id": "path-alu-result", "bits":[1], "duration": 0.3, "start_delay": 0.2})
                active_paths_ex.append("path-alu-zero")
                animated_signals_ex.append({"path_id": "path-alu-zero", "bits":[alu_zero_flag], "duration": 0.1, "start_delay": 0.2})
            else:
                exec_result['log'] = "  Execute: No ALU operation required.\n"
                exec_result['alu_result'] = 0 # Default
                exec_result['alu_zero_flag'] = 0 # Default

            # 4. Calculate Branch Target Address (if applicable)
            if decoded_info.get('format') in ['CB', 'B']:
                 offset_raw = decoded_info['branch_offset_val']
                 offset_bits = branch_offset_bits # Set during decode
                 branch_offset_extended = sign_extend(offset_raw, offset_bits)
                 # CB/B offsets are instruction offsets, need byte offset for adder
                 byte_offset = branch_offset_extended * 4
                 branch_target_addr = branch_target_adder(current_pc, byte_offset)
                 exec_result['branch_target_addr'] = branch_target_addr
                 exec_result['log'] += f"  Execute: Calculate Branch Target: PC(0x{current_pc:X}) + ByteOffset({byte_offset}) = 0x{branch_target_addr:X}"

                 # Visualization
                 if "block-adder2" not in active_blocks_ex: active_blocks_ex.append("block-adder2")
                 active_paths_ex.extend(["path-pc-adder2", "path-signext-br-adder2", "path-adder2-mux4-in1"])
                 animated_signals_ex.extend([
                    {"path_id": "path-pc-adder2", "bits":[1], "duration": 0.2},
                    {"path_id": "path-signext-br-adder2", "bits":[1], "duration": 0.2}, # Offset path
                    {"path_id": "path-adder2-mux4-in1", "bits":[1], "duration": 0.2, "start_delay": 0.2} # Adder output
                 ])
            else:
                 exec_result['branch_target_addr'] = 0 # Not a branch

            # Update stage log and retrieve results
            stage_log_ex += exec_result.get('log', "")
            alu_result = exec_result.get('alu_result', 0)
            alu_zero_flag = exec_result.get('alu_zero_flag', 0)
            branch_target_addr = exec_result.get('branch_target_addr', 0)

            yield MicroStepState(current_stage_name, current_micro_step_index, stage_log_ex, active_blocks_ex, active_paths_ex, animated_signals_ex, control_values).to_dict()

        except (ValueError, TypeError) as e:
            stage_log_ex += f"  Error: {e}\n traceback: {traceback.format_exc()}\n"
            yield MicroStepState(current_stage_name, current_micro_step_index, stage_log_ex, active_blocks_ex, active_paths_ex, animated_signals_ex, control_values).to_dict()
            return {"next_pc": pc_p4, "error": f"Execute Error: {e}"}

        # --- Micro-Step 3: Memory Access (MEM) ---
        current_stage_name = "Memory"
        current_micro_step_index = 3
        stage_log_mem = f"[{current_stage_name}]\n"
        active_blocks_mem = []
        active_paths_mem = []
        animated_signals_mem = []
        data_read_from_mem = None # Reset for this stage

        try:
            mem_read = control_values.get('MemRead', 0)
            mem_write = control_values.get('MemWrite', 0)
            mem_address = alu_result # Address always comes from ALU result for D-format

            if mem_read == 1: # LDUR
                if "block-datamem" not in active_blocks_mem: active_blocks_mem.append("block-datamem")
                data_read_from_mem = read_memory(data_mem_dict, mem_address)
                stage_log_mem += f"  Memory Read: Accessing Addr=0x{mem_address:X} -> Read Data=0x{data_read_from_mem:X}\n"
                active_paths_mem.extend(["path-alu-memaddr", "control-memread-enable", "path-mem-readdata"])
                animated_signals_mem.extend([
                    {"path_id": "path-alu-memaddr", "bits":[1], "duration": 0.2},
                    {"path_id": "control-memread-enable", "bits":[1], "duration": 0.1},
                    {"path_id": "path-mem-readdata", "bits":[1], "duration": 0.3, "start_delay": 0.2}
                ])
            elif mem_write == 1: # STUR
                if "block-datamem" not in active_blocks_mem: active_blocks_mem.append("block-datamem")
                data_to_write = read_data2 # Data comes from Rt (read in Decode)
                rt_name = reg_index_to_name(decoded_info.get('rt_idx', -1))
                write_memory(data_mem_dict, mem_address, data_to_write)
                stage_log_mem += (f"  Memory Write: Addr=0x{mem_address:X}, Writing Data=0x{data_to_write:X} "
                                  f"(from {rt_name}) -> Success.\n")
                active_paths_mem.extend(["path-alu-memaddr", "path-rdata2-memwrite", "control-memwrite-enable"])
                animated_signals_mem.extend([
                     {"path_id": "path-alu-memaddr", "bits":[1], "duration": 0.2},
                     {"path_id": "path-rdata2-memwrite", "bits":[1], "duration": 0.3, "start_delay": 0.1},
                     {"path_id": "control-memwrite-enable", "bits":[1], "duration": 0.1}
                ])
            else: # No memory operation
                stage_log_mem += "  Memory: No memory operation required.\n"

            yield MicroStepState(current_stage_name, current_micro_step_index, stage_log_mem, active_blocks_mem, active_paths_mem, animated_signals_mem, control_values).to_dict()

        except (ValueError, TypeError, KeyError) as e:
            stage_log_mem += f"  Error: {e}\n traceback: {traceback.format_exc()}\n"
            yield MicroStepState(current_stage_name, current_micro_step_index, stage_log_mem, active_blocks_mem, active_paths_mem, animated_signals_mem, control_values).to_dict()
            return {"next_pc": pc_p4, "error": f"Memory Error: {e}"}


        # --- Micro-Step 4: Write Back (WB) & PC Update ---
        current_stage_name = "Write Back / PC Update"
        current_micro_step_index = 4
        stage_log_wb = f"[{current_stage_name}]\n"
        active_blocks_wb = []
        active_paths_wb = []
        animated_signals_wb = []
        wb_log = "" # Reset log for this stage

        try:
            # --- Part 1: Write Back ---
            reg_write = control_values.get('RegWrite', 0)
            mem_to_reg = control_values.get('MemToReg', 0)
            data_to_write_back = None
            write_occurred = False
            dest_reg_idx = -1

            if reg_write == 1:
                active_blocks_wb.append("block-mux3")
                data_to_write_back = writeback_data_mux(alu_result, data_read_from_mem, mem_to_reg)

                # Determine destination register index
                if decoded_info.get('format') in ['R', 'I']:
                     dest_reg_idx = decoded_info.get('rd_idx')
                elif decoded_info.get('format') == 'D' and decoded_info.get('is_load'):
                     dest_reg_idx = decoded_info.get('rt_idx')

                dest_reg_name = reg_index_to_name(dest_reg_idx) if dest_reg_idx is not None else "N/A"

                if data_to_write_back is not None and dest_reg_idx is not None:
                    wb_log += f"  Write Back Stage: RegWrite=1 for {dest_reg_name} (Index {dest_reg_idx}).\n"
                    active_paths_wb.extend(["control-regwrite-enable", "path-instr-regwriteaddr"]) # Enable + Addr path
                    animated_signals_wb.extend([{"path_id": "control-regwrite-enable", "bits":[1],"duration":0.1},
                                                {"path_id": "path-instr-regwriteaddr", "bits":[1],"duration":0.2}])

                    wb_path_mux_out = "path-mux3-wb"
                    wb_path_to_regs = "path-wb-regwrite"
                    active_paths_wb.extend([wb_path_mux_out, wb_path_to_regs])
                    mux3_in_path, mux3_sel_path = "", ""

                    if mem_to_reg == 0: # Data from ALU
                        wb_log += f"  Write Back Stage: Mux3 selects ALU Result (0x{data_to_write_back:X}).\n"
                        mux3_in_path = "path-alu-mux3-in0"
                        mux3_sel_path = "mux-memtoreg-in0"
                    elif mem_to_reg == 1: # Data from Memory
                        wb_log += f"  Write Back Stage: Mux3 selects Memory Data (0x{data_to_write_back:X}).\n"
                        mux3_in_path = "path-mem-readdata-mux3"
                        mux3_sel_path = "mux-memtoreg-in1"

                    if mux3_in_path: active_paths_wb.append(mux3_in_path)
                    if mux3_sel_path: active_paths_wb.append(mux3_sel_path)
                    animated_signals_wb.extend([
                        {"path_id": mux3_in_path, "bits":[1], "duration": 0.1},
                        {"path_id": wb_path_mux_out, "bits":[1], "duration": 0.2, "start_delay": 0.1},
                        {"path_id": wb_path_to_regs, "bits":[1], "duration": 0.1, "start_delay": 0.3},
                    ])

                    try:
                        write_register(registers_dict, dest_reg_idx, data_to_write_back) # Use index-based write
                        wb_log += f"  Write Back Stage: Successfully wrote 0x{data_to_write_back:X} to {dest_reg_name}.\n"
                        write_occurred = True
                    except ValueError as e:
                        raise ValueError(f"Write Back Error: {e}")

                elif reg_write == 1:
                     wb_log += f"  Write Back Stage: RegWrite=1 but no data/destination determined (MemToReg={mem_to_reg}, DestIdx={dest_reg_idx}).\n"

            if not write_occurred and reg_write == 0:
                wb_log += "  Write Back Stage: No register write needed (RegWrite=0).\n"

            stage_log_wb += wb_log


            # --- Part 2: PC Update ---
            active_blocks_wb.append("block-mux4")
            branch_signal = control_values.get('Branch', 0)
            uncond_branch_signal = control_values.get('UncondBranch', 0)
            pc_update_log = f"  PC Update Logic Input: BranchSig={branch_signal}, UncondBranchSig={uncond_branch_signal}, ALUZeroFlag={alu_zero_flag}\n"

            pc_src_signal = branch_control_logic(branch_signal, alu_zero_flag, uncond_branch_signal)
            pc_update_log += f"  PC Update Logic Result: PCSrc Signal = {pc_src_signal}.\n"

            final_next_pc = pc_source_mux(pc_p4, branch_target_addr, pc_src_signal)
            pc_update_log += f"  PC Source Mux Output: Selected Next PC = 0x{final_next_pc:X}"
            pc_update_log += f" (Source: {'Branch Target' if pc_src_signal == 1 else 'PC+4'})\n"
            stage_log_wb += pc_update_log

            # Visualization
            path_mux4_out = "path-mux4-pc"
            active_paths_wb.append(path_mux4_out)
            mux4_in_path, mux4_sel_path = "", ""
            if pc_src_signal == 1:
                mux4_in_path = "path-adder2-mux4-in1"
                mux4_sel_path = "mux-pcsrc-in1"
            else:
                mux4_in_path = "path-adder1-mux4-in0"
                mux4_sel_path = "mux-pcsrc-in0"

            active_paths_wb.extend([mux4_in_path, mux4_sel_path])
            animated_signals_wb.extend([
                {"path_id": mux4_in_path, "bits":[1], "duration": 0.1 },
                {"path_id": path_mux4_out, "bits":[1], "duration": 0.2, "start_delay": 0.1}
            ])

            yield MicroStepState(current_stage_name, current_micro_step_index, stage_log_wb, active_blocks_wb, active_paths_wb, animated_signals_wb, control_values).to_dict()
            return {"next_pc": final_next_pc} # Instruction finished successfully

        except (ValueError, TypeError) as e:
            stage_log_wb += f"  Error: {e}\n traceback: {traceback.format_exc()}\n"
            yield MicroStepState(current_stage_name, current_micro_step_index, stage_log_wb, active_blocks_wb, active_paths_wb, animated_signals_wb, control_values).to_dict()
            return {"next_pc": pc_p4, "error": f"Write Back / PC Update Error: {e}"}

    except StopIteration:
        raise # Should not happen here
    except Exception as e:
        error_msg = (f"Unexpected Runtime Error in Generator for instruction 0x{instruction_bin:X} at PC=0x{current_pc:X} "
                     f"(Stage: {current_stage_name}, Step: {current_micro_step_index}): {e}\n"
                     f"{traceback.format_exc()}")
        print(f"FATAL GENERATOR ERROR: {error_msg}")
        try:
            last_ctrl = control_values if 'control_values' in locals() else {}
            yield MicroStepState(current_stage_name, current_micro_step_index, error_msg, [], [], [], last_ctrl).to_dict()
        except Exception: pass
        return {"next_pc": current_pc, "error": error_msg}


# ==============================================================================
# Flask Application Setup and API Endpoints (MODIFIED for Binary)
# ==============================================================================
app = Flask(__name__)
sim_state = {}

def initialize_sim_state():
    global sim_state
    sim_state = {
        'pc': 0,
        'registers': {f"X{i}": 0 for i in range(31)}, # X0-X30
        'data_memory': {},
        'instruction_memory': {}, # Key: address, Value: 32-bit instruction INTEGER
        'raw_instruction_memory': {}, # Key: address, Value: original instruction STRING
        'label_table': {},
        'current_instruction_generator': None,
        'simulation_loaded': False,
        'error_state': None,
        'current_instr_addr': -1,
        'current_instr_bin': 0, # Store the binary being executed
        'current_instr_str': "", # Store the raw string being executed
        'micro_step_index': -1,
        'instruction_completed_flag': False
    }
    sim_state['registers']["XZR"] = 0
    sim_state['registers']["X28"] = 0x7FFFFFFF00 # SP
    print("--- Simulation state reset (Binary Mode). ---")

def format_cpu_state_api():
    """ Formats the current CPU state (PC, registers, memory) for API responses. """
    if not sim_state: return {"error": "Simulation state not initialized"}

    regs_copy = sim_state.get('registers', {})
    # Start with SP alias display using X28 value
    sp_val = regs_copy.get('X28', 0)
    regs_display = {"SP": f"0x{sp_val:X} ({sp_val})"}

    # Add other registers X0-X30 and XZR
    for i in range(32): # Iterate 0 to 31
        if i == 31:
            reg_name = "XZR"
            val = 0 # XZR is always 0
        else:
             reg_name = f"X{i}"
             # Skip X28 as it's displayed as SP
             if i == 28: continue
             val = regs_copy.get(reg_name, 0)

        # Format display: Show non-zero values with hex and decimal
        if reg_name == "XZR":
             regs_display[reg_name] = f"0x{val:X}" # Always show XZR as 0x0
        elif val != 0:
             regs_display[reg_name] = f"0x{val:X} ({val})"
        # Optional: Show zero registers uncommenting the else block
        # else:
        #    regs_display[reg_name] = f"0x{val:X}" # Show zero value

    # Sort registers numerically X0-X30, then SP, then XZR
    def reg_sort_key(item):
        name = item[0]
        if name == "SP": return 28.5 # Sort SP after X28 (conceptually)
        if name == "XZR": return 31
        try: return int(name[1:]) # Sort X0-X30 numerically
        except: return 99 # Fallback
    sorted_regs = dict(sorted(regs_display.items(), key=reg_sort_key))

    # Format data memory, showing non-zero values, sorted by address
    mem_copy = sim_state.get('data_memory', {})
    mem_display = {
        f"0x{addr:X}": f"0x{val:X} ({val})"
        for addr, val in mem_copy.items() if val != 0 # Only display non-zero memory
    }
    sorted_mem = dict(sorted(mem_display.items(), key=lambda item: int(item[0], 16)))

    return {
        "pc": f"0x{sim_state.get('pc', 0):X}",
        "registers": sorted_regs,
        "data_memory": sorted_mem
    }

@app.route('/')
def index():
    """ Serves the main HTML page. """
    return render_template('index.html')

@app.route('/api/load', methods=['POST'])
def api_load():
    """
    Loads ARMv8 assembly code, performs two passes for label resolution
    and ENCODES instructions to binary.
    """
    print("\n>>> Received /api/load request (Binary Encoding) <<<")
    initialize_sim_state()
    try:
        data = request.get_json()
        code = data['code']
        lines = code.splitlines()
        current_address = 0
        label_table = {}
        raw_instructions_list = [] # Stores {'address': int, 'text': str, 'original': str}
        sim_state['instruction_memory'] = {} # Stores {address: instruction_binary_int}
        sim_state['raw_instruction_memory'] = {} # Stores {address: original_text_str}

        # --- Pass 1: Build Label Table & Store Raw Info ---
        print("--- Load Pass 1: Finding labels and addresses ---")
        line_num = 0
        for line in lines:
            line_num += 1
            original_line = line
            cleaned_line = line.split('//')[0].strip()
            if not cleaned_line: continue

            label_match = re.match(r'^([a-zA-Z_][a-zA-Z0-9_]*):\s*(.*)', cleaned_line)
            instruction_part = cleaned_line
            if label_match:
                label = label_match.group(1)
                instruction_part = label_match.group(2).strip()
                if label in label_table: raise ValueError(f"Duplicate label '{label}' on line {line_num}")
                label_table[label] = current_address
                print(f"  Label Found: '{label}' => Address 0x{current_address:X}")

            if instruction_part and not instruction_part.startswith(('.', '#')):
                raw_instructions_list.append({
                    'address': current_address,
                    'text': instruction_part,
                    'original': original_line.strip()
                })
                sim_state['raw_instruction_memory'][current_address] = original_line.strip()
                current_address += 4

        sim_state['label_table'] = label_table
        print(f"--- Load Pass 1 Complete. Labels: {label_table} ---")

        # --- Pass 2: Encode Instructions to Binary ---
        print("--- Load Pass 2: Encoding instructions to binary ---")
        instr_count = 0
        for instr_info in raw_instructions_list:
            addr = instr_info['address']
            text = instr_info['text']
            print(f"  Encoding @ 0x{addr:X}: '{text}'")

            parts = re.split(r'[,\s()\[\]]+', text) # Split for parsing args
            parts = [p for p in parts if p]
            opcode_str = parts[0].upper()
            args = parts[1:]
            instr_bin = 0

            try:
                if opcode_str == "NOP": instr_bin = OP_NOP
                elif opcode_str == "ADD": instr_bin = encode_r(OP_ADD, args[0], args[1], args[2])
                elif opcode_str == "SUB": instr_bin = encode_r(OP_SUB, args[0], args[1], args[2])
                elif opcode_str == "AND": instr_bin = encode_r(OP_AND, args[0], args[1], args[2])
                elif opcode_str == "ORR": instr_bin = encode_r(OP_ORR, args[0], args[1], args[2])
                elif opcode_str == "MUL": instr_bin = encode_r(OP_MUL, args[0], args[1], args[2])
                elif opcode_str == "DIV": instr_bin = encode_r(OP_DIV, args[0], args[1], args[2])
                elif opcode_str == "ADDI": instr_bin = encode_i(OP_ADDI, args[0], args[1], int(args[2].lstrip('#')))
                elif opcode_str == "SUBI": instr_bin = encode_i(OP_SUBI, args[0], args[1], int(args[2].lstrip('#')))
                elif opcode_str == "LDUR": instr_bin = encode_d(OP_LDUR, args[0], args[1], int(args[2].lstrip('#')))
                elif opcode_str == "STUR": instr_bin = encode_d(OP_STUR, args[0], args[1], int(args[2].lstrip('#')))
                elif opcode_str == "CBZ":
                    target = args[1]
                    offset = 0
                    if target in label_table: offset = label_table[target] - addr
                    else: offset = int(target) # Assume numeric offset if not label
                    instr_bin = encode_cb(OP_CBZ, args[0], offset)
                elif opcode_str == "B":
                    target = args[0]
                    offset = 0
                    if target in label_table: offset = label_table[target] - addr
                    else: offset = int(target) # Assume numeric offset if not label
                    instr_bin = encode_b(OP_B, offset)
                else:
                    raise ValueError(f"Unsupported instruction mnemonic: '{opcode_str}'")

                sim_state['instruction_memory'][addr] = instr_bin
                print(f"    Encoded as: 0x{instr_bin:08X}")
                instr_count += 1
            except (ValueError, IndexError, KeyError) as e:
                 # Catch parsing errors, bad immediates, bad registers, missing labels
                 raise ValueError(f"Encoding Error at 0x{addr:X} ('{text}'): {e}") from e


        sim_state['pc'] = 0
        sim_state['simulation_loaded'] = True
        sim_state['error_state'] = None
        sim_state['current_instruction_generator'] = None
        sim_state['micro_step_index'] = -1
        sim_state['instruction_completed_flag'] = False
        sim_state['current_instr_addr'] = sim_state['pc']
        sim_state['current_instr_str'] = sim_state['raw_instruction_memory'].get(sim_state['pc'], "(No instruction)")
        sim_state['current_instr_bin'] = sim_state['instruction_memory'].get(sim_state['pc'], 0)


        print(f"--- Load Pass 2 Complete. {instr_count} instructions encoded. ---")
        return jsonify({
            "status": "success",
            "message": f"{instr_count} instructions loaded and encoded successfully. Ready to run.",
            "cpu_state": format_cpu_state_api(),
            "initial_instr_addr": f"0x{sim_state['current_instr_addr']:X}",
            "initial_instr_str": sim_state['current_instr_str']
        })

    except Exception as e:
        print(f"[ERROR] /api/load failed: {e}")
        traceback.print_exc()
        initialize_sim_state()
        return jsonify({"status": "error", "message": f"Load failed: {e}"}), 400


@app.route('/api/micro_step', methods=['POST'])
def api_micro_step():
    """ Executes the next micro-step using the BINARY instruction generator. """
    global sim_state
    print(f"\n>>> Received /api/micro_step request (Binary Mode, PC=0x{sim_state.get('pc', -1):X}) <<<")

    if not sim_state.get('simulation_loaded', False):
        error_msg = sim_state.get('error_state', 'Simulation not loaded or has ended.')
        print(f"Micro-step request rejected: {error_msg}")
        return jsonify({"status": "error", "message": error_msg, "cpu_state": format_cpu_state_api()}), 400

    try:
        current_pc = sim_state['pc']

        if sim_state['instruction_completed_flag']:
            print("--- Transitioning to next instruction ---")
            sim_state['instruction_completed_flag'] = False
            sim_state['current_instruction_generator'] = None
            sim_state['micro_step_index'] = -1
            sim_state['current_instr_addr'] = current_pc
            sim_state['current_instr_str'] = sim_state['raw_instruction_memory'].get(current_pc, "(No instruction)")
            sim_state['current_instr_bin'] = sim_state['instruction_memory'].get(current_pc, 0) # Get binary for next instr display if needed
            print(f"Ready to start instruction at new PC=0x{current_pc:X}: '{sim_state['current_instr_str']}' (0x{sim_state['current_instr_bin']:08X})")

        # Check PC Validity (using instruction_memory which holds binary)
        if current_pc not in sim_state['instruction_memory']:
            sim_state['simulation_loaded'] = False
            sim_state['error_state'] = f"Program terminated: No instruction found at PC=0x{current_pc:X}"
            print(f"Execution Halt: {sim_state['error_state']}")
            return jsonify({
                "status": "finished_program",
                "message": sim_state['error_state'],
                "cpu_state": format_cpu_state_api()
            })

        if sim_state['current_instruction_generator'] is None:
            sim_state['current_instr_addr'] = current_pc
            sim_state['current_instr_str'] = sim_state['raw_instruction_memory'].get(current_pc, "(Raw missing)")
            sim_state['current_instr_bin'] = sim_state['instruction_memory'][current_pc] # The binary instruction to execute

            print(f"--- Creating Generator for Instruction at PC=0x{current_pc:X} ---")
            print(f"  Raw Display: '{sim_state['current_instr_str']}'")
            print(f"  Executing Binary: 0x{sim_state['current_instr_bin']:08X}")

            # Pass a view containing only the current BINARY instruction
            temp_instr_mem_for_gen = {current_pc: sim_state['current_instr_bin']}

            sim_state['current_instruction_generator'] = execute_instruction_detailed_generator(
                current_pc,
                sim_state['registers'],
                sim_state['data_memory'],
                temp_instr_mem_for_gen
            )
            sim_state['micro_step_index'] = -1

        # --- Execute Micro-Step ---
        try:
            print(f"--- Executing Micro-Step {sim_state['micro_step_index'] + 1} ---")
            step_data_dict = next(sim_state['current_instruction_generator'])
            sim_state['micro_step_index'] += 1
            current_stage_name = step_data_dict.get("stage", "Unknown")
            print(f"  Generator yielded state for Stage: {current_stage_name}")

            # Add current instruction info (BINARY and RAW) to the response data
            step_data_dict['current_instruction_address'] = f"0x{sim_state['current_instr_addr']:X}"
            step_data_dict['current_instruction_string'] = sim_state['current_instr_str']
            # Optionally add binary to response if UI wants to display it
            # step_data_dict['current_instruction_binary'] = f"0x{sim_state['current_instr_bin']:08X}"

            if 'log_entry' in step_data_dict and step_data_dict['log_entry']:
                 log_lines = step_data_dict['log_entry'].strip().split('\n')
                 print("\n".join(f"    {line.strip()}" for line in log_lines))

            return jsonify({
                "status": "success",
                "step_data": step_data_dict,
                "cpu_state": format_cpu_state_api(),
                "enable_next": True
            })

        except StopIteration as e:
            # --- Instruction Completed ---
            completed_instr_str = sim_state['current_instr_str']
            completed_instr_addr = sim_state['current_instr_addr']
            completed_instr_bin = sim_state['current_instr_bin']
            print(f"--- Instruction Completed: '{completed_instr_str}' (0x{completed_instr_bin:08X}) at 0x{completed_instr_addr:X} ---")
            sim_state['instruction_completed_flag'] = True
            sim_state['current_instruction_generator'] = None

            result = e.value if hasattr(e, 'value') and isinstance(e.value, dict) else {}
            next_pc = result.get('next_pc')
            error_msg = result.get('error')

            if next_pc is None and not error_msg:
                 error_msg = "Internal Simulator Error: Generator finished unexpectedly without returning next_pc."
                 print(f"[ERROR] {error_msg}")
                 next_pc = completed_instr_addr # Halt
                 sim_state['simulation_loaded'] = False

            print(f"  Generator Final Result: next_pc=0x{next_pc:X}, error='{error_msg}'")
            sim_state['pc'] = next_pc # Update PC

            if error_msg:
                sim_state['error_state'] = f"Execution Error at 0x{completed_instr_addr:X} ('{completed_instr_str}'): {error_msg}"
                sim_state['simulation_loaded'] = False
                print(f"[EXECUTION HALTED] {sim_state['error_state']}")
                return jsonify({ "status": "error", "message": sim_state['error_state'], "cpu_state": format_cpu_state_api() }), 500

            # Check if next PC is valid
            if next_pc not in sim_state['instruction_memory']:
                 sim_state['simulation_loaded'] = False
                 final_message = (f"Program finished normally after instruction at 0x{completed_instr_addr:X}. "
                                  f"Next PC=0x{next_pc:X} is outside loaded instructions.")
                 sim_state['error_state'] = final_message
                 print(f"--- Program Finished Normally --- \n  {final_message}")
                 return jsonify({ "status": "finished_program", "message": final_message, "cpu_state": format_cpu_state_api() })
            else:
                 # Instruction finished, next is valid
                 next_instr_str = sim_state['raw_instruction_memory'].get(next_pc, "(Invalid PC)")
                 print(f"  Ready for next instruction request at PC=0x{next_pc:X}: '{next_instr_str}'")
                 return jsonify({
                     "status": "instruction_completed",
                     "message": f"Instruction '{completed_instr_str}' completed. Next PC 0x{next_pc:X}.",
                     "cpu_state": format_cpu_state_api(),
                     "next_pc": f"0x{next_pc:X}",
                     "next_instruction": next_instr_str,
                     "enable_next": True,
                 })

    except Exception as e:
        print(f"[FATAL API ERROR] /api/micro_step: {e}")
        traceback.print_exc()
        sim_state['error_state'] = f"Unexpected server error: {e}"
        sim_state['simulation_loaded'] = False
        return jsonify({ "status": "error", "message": sim_state['error_state'], "cpu_state": format_cpu_state_api() }), 500


@app.route('/api/reset', methods=['POST'])
def api_reset_state():
    """ Resets the simulation state. """
    print("\n>>> Received /api/reset request <<<")
    initialize_sim_state()
    return jsonify({
        "status": "success",
        "message": "Simulator reset.",
        "cpu_state": format_cpu_state_api()
    })

# ==============================================================================
# Main Application Runner
# ==============================================================================
if __name__ == '__main__':
    initialize_sim_state()
    print("=================================================")
    print(" Starting ARMv8 Simulator Flask Web Server (BINARY MODE)")
    print(" Access at: http://localhost:5010 (or equivalent)")
    print("=================================================")
    app.run(debug=True, host='0.0.0.0', port=5010, threaded=False)

    