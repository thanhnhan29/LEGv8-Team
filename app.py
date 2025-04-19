# -*- coding: utf-8 -*-
# SINGLE FILE ARMv8 SIMULATOR (Flask Web App)
# Includes refactored execution logic using dispatch tables and detailed CBZ logging.

from flask import Flask, render_template, request, jsonify
import re
import sys
import traceback
import copy # To create state copies if needed (currently not heavily used, but good practice)

# ==============================================================================
# Phần lõi mô phỏng: Helpers, Hardware Blocks, Muxes
# ==============================================================================

# --- Hàm trợ giúp Register ---
def read_register(registers_dict, reg_name):
    """ Reads a value from the register dictionary, handling XZR and SP aliases. """
    reg_name = reg_name.upper()
    # Special handling for Zero Register (XZR/X31)
    if reg_name == "XZR" or reg_name == "X31":
        # print(f"DEBUG READ REG: Reading XZR/X31 -> Returning 0") # Optional Verbose Debug
        return 0
    # Alias SP to X28 for internal access
    if reg_name == "SP":
        reg_name = "X28"
    val = registers_dict.get(reg_name)
    # Check if register exists
    if val is None:
        raise ValueError(f"Invalid register read: Register '{reg_name}' does not exist.")
    # Ensure value is treated as a 64-bit integer
    # print(f"DEBUG READ REG: Reading {reg_name} -> Value = {val} (0x{int(val):X})") # Optional Verbose Debug
    return int(val) & 0xFFFFFFFFFFFFFFFF

def write_register(registers_dict, reg_name, value):
    """ Writes a value to the register dictionary, handling XZR and SP aliases. """
    reg_name = reg_name.upper()
    # Prevent writing to the Zero Register
    if reg_name not in ["XZR", "X31"]:
        # Alias SP to X28 for internal access
        if reg_name == "SP":
            reg_name = "X28"
        # Check if register exists before writing
        if reg_name in registers_dict:
            # Ensure written value is 64-bit
            written_value = int(value) & 0xFFFFFFFFFFFFFFFF
            # print(f"DEBUG WRITE REG: Writing to {reg_name} -> Value = {written_value} (0x{written_value:X})") # Optional Verbose Debug
            registers_dict[reg_name] = written_value
        else:
            raise ValueError(f"Invalid register write target: Register '{reg_name}' does not exist.")
    # else: Writes to XZR/X31 are silently ignored by hardware

# --- Hàm trợ giúp Memory ---
def read_memory(data_mem_dict, address):
    """ Reads a 64-bit value from the data memory dictionary. Defaults to 0 if address not found. """
    address = int(address)
    # Default to 0 if address not found (common behavior for simulators)
    value = data_mem_dict.get(address, 0)
    # Ensure value is treated as a 64-bit integer
    # print(f"DEBUG READ MEM: Reading Addr 0x{address:X} -> Value = {value} (0x{int(value):X})") # Optional Verbose Debug
    return int(value) & 0xFFFFFFFFFFFFFFFF

def write_memory(data_mem_dict, address, value):
    """ Writes a 64-bit value to the data memory dictionary. """
    address = int(address)
    value = int(value)
    # Ensure written value is 64-bit
    written_value = value & 0xFFFFFFFFFFFFFFFF
    # print(f"DEBUG WRITE MEM: Writing Addr 0x{address:X} <- Value = {written_value} (0x{written_value:X})") # Optional Verbose Debug
    data_mem_dict[address] = written_value

# --- Các Khối Phần Cứng Mô Phỏng ---
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

# --- Cấu trúc dữ liệu cho trạng thái Micro-step ---
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

# ==============================================================================
# Phần Điều Khiển và Bảng Lệnh
# ==============================================================================

# --- Instruction Table & Control Signal Calculation ---
# Defines control signals for each supported instruction.
# ALUOp: '10'=R-type, '00'=I/D-type Add/Sub, '01'=Branch Compare, 'XX'=Not Used
# MemToReg: 0=ALU, 1=Mem, -1=No Write Back
INSTRUCTION_TABLE = {
    # Opcode: { 'control': { Signal: Value, ... } }
    'ADD':  {'control': {'RegWrite': 1, 'ALUSrc': 0, 'MemRead': 0, 'MemWrite': 0, 'MemToReg': 0, 'Branch': 0, 'UncondBranch': 0, 'ALUOp': '10'}},
    'SUB':  {'control': {'RegWrite': 1, 'ALUSrc': 0, 'MemRead': 0, 'MemWrite': 0, 'MemToReg': 0, 'Branch': 0, 'UncondBranch': 0, 'ALUOp': '10'}},
    'AND':  {'control': {'RegWrite': 1, 'ALUSrc': 0, 'MemRead': 0, 'MemWrite': 0, 'MemToReg': 0, 'Branch': 0, 'UncondBranch': 0, 'ALUOp': '10'}},
    'ORR':  {'control': {'RegWrite': 1, 'ALUSrc': 0, 'MemRead': 0, 'MemWrite': 0, 'MemToReg': 0, 'Branch': 0, 'UncondBranch': 0, 'ALUOp': '10'}},
    'ADDI': {'control': {'RegWrite': 1, 'ALUSrc': 1, 'MemRead': 0, 'MemWrite': 0, 'MemToReg': 0, 'Branch': 0, 'UncondBranch': 0, 'ALUOp': '00'}},
    'SUBI': {'control': {'RegWrite': 1, 'ALUSrc': 1, 'MemRead': 0, 'MemWrite': 0, 'MemToReg': 0, 'Branch': 0, 'UncondBranch': 0, 'ALUOp': '00'}},
    'LDUR': {'control': {'RegWrite': 1, 'ALUSrc': 1, 'MemRead': 1, 'MemWrite': 0, 'MemToReg': 1, 'Branch': 0, 'UncondBranch': 0, 'ALUOp': '00'}},
    'STUR': {'control': {'RegWrite': 0, 'ALUSrc': 1, 'MemRead': 0, 'MemWrite': 1, 'MemToReg': -1,'Branch': 0, 'UncondBranch': 0, 'ALUOp': '00'}},
    'CBZ':  {'control': {'RegWrite': 0, 'ALUSrc': 0, 'MemRead': 0, 'MemWrite': 0, 'MemToReg': 0, 'Branch': 1, 'UncondBranch': 0, 'ALUOp': '01'}},
    'B':    {'control': {'RegWrite': 0, 'ALUSrc': 0, 'MemRead': 0, 'MemWrite': 0, 'MemToReg': 0, 'Branch': 0, 'UncondBranch': 1, 'ALUOp': 'XX'}},
    'NOP':  {'control': {'RegWrite': 0, 'ALUSrc': 0, 'MemRead': 0, 'MemWrite': 0, 'MemToReg': 0, 'Branch': 0, 'UncondBranch': 0, 'ALUOp': 'XX'}},
    'MUL':  {'control': {'RegWrite': 1, 'ALUSrc': 0, 'MemRead': 0, 'MemWrite': 0, 'MemToReg': 0, 'Branch': 0, 'UncondBranch': 0, 'ALUOp': '10'}}, # R-type ALU
    'DIV':  {'control': {'RegWrite': 1, 'ALUSrc': 0, 'MemRead': 0, 'MemWrite': 0, 'MemToReg': 0, 'Branch': 0, 'UncondBranch': 0, 'ALUOp': '10'}}, # R-type ALU
}

def calculate_control_signals(opcode):
    """ Looks up control signals for a given opcode from INSTRUCTION_TABLE. """
    instr_info = INSTRUCTION_TABLE.get(opcode.upper())
    if instr_info is None:
        # Default to NOP signals for unknown opcodes
        print(f"[WARN] Control Logic: Unknown opcode '{opcode}'. Using NOP signals.")
        return INSTRUCTION_TABLE['NOP']['control'].copy()
    # print(f"DEBUG Control Logic: Signals for {opcode}: {instr_info['control']}") # Optional Verbose Debug
    return instr_info['control'].copy()

# ==============================================================================
# Instruction-Specific Handlers (Refactored Structure)
# ==============================================================================

# --- Decode Handlers ---
# Input: parts (list of string components from the instruction)
# Output: Dictionary containing decoded info (log, registers, immediates, read addresses)

def decode_nop(parts):
    """ Decodes a NOP instruction. """
    return {'log': "  Decode: NOP instruction (no operands).", 'read_reg1_addr': None, 'read_reg2_addr': None}

def decode_r_format(parts):
    """ Decodes R-format instructions (ADD, SUB, AND, ORR). """
    if len(parts) < 4: raise ValueError("Decode Error: Invalid R-format instruction syntax")
    rd, rn, rm = parts[1], parts[2], parts[3]
    return {'log': f"  Decode: R-format (Rd={rd}, Rn={rn}, Rm={rm})",
            'rd': rd, 'rn': rn, 'rm': rm,
            'read_reg1_addr': rn, 'read_reg2_addr': rm}

def decode_i_format(parts):
    """ Decodes I-format instructions (ADDI, SUBI). """
    if len(parts) < 4: raise ValueError("Decode Error: Invalid I-format instruction syntax")
    rd, rn, imm_str = parts[1], parts[2], parts[3].lstrip('#')
    try:
        imm_val = int(imm_str)
    except ValueError:
        raise ValueError(f"Decode Error: Invalid immediate value for I-format: '{imm_str}'")
    return {'log': f"  Decode: I-format (Rd={rd}, Rn={rn}, Imm={imm_str} [12b])",
            'rd': rd, 'rn': rn, 'imm_val': imm_val, 'imm_bits': 12,
            'read_reg1_addr': rn, 'read_reg2_addr': None}

def decode_d_format_load(parts):
    """ Decodes D-format Load instructions (LDUR). """
    if len(parts) < 4: raise ValueError("Decode Error: Invalid D-format LDUR instruction syntax")
    rt, rn, imm_str = parts[1], parts[2], parts[3].lstrip('#')
    try:
        imm_val = int(imm_str)
    except ValueError:
        raise ValueError(f"Decode Error: Invalid immediate value for D-format: '{imm_str}'")
    return {'log': f"  Decode: D-format Load (Rt={rt}, Rn={rn}, Imm={imm_str} [9b])",
            'rt': rt, 'rd': rt, # Use 'rd' alias for consistency in WB stage logic if needed
            'rn': rn, 'imm_val': imm_val, 'imm_bits': 9,
            'read_reg1_addr': rn, # Read base register Rn
            'read_reg2_addr': None}

def decode_d_format_store(parts):
    """ Decodes D-format Store instructions (STUR). """
    if len(parts) < 4: raise ValueError("Decode Error: Invalid D-format STUR instruction syntax")
    rt, rn, imm_str = parts[1], parts[2], parts[3].lstrip('#')
    try:
        imm_val = int(imm_str)
    except ValueError:
        raise ValueError(f"Decode Error: Invalid immediate value for D-format: '{imm_str}'")
    return {'log': f"  Decode: D-format Store (Rt={rt}, Rn={rn}, Imm={imm_str} [9b])",
            'rt': rt, 'rn': rn, 'imm_val': imm_val, 'imm_bits': 9,
            'read_reg1_addr': rn, # Read base register Rn
            'read_reg2_addr': rt} # Read data register Rt

def decode_cb_format(parts):
    """ Decodes CB-format instructions (CBZ). """
    if len(parts) < 3: raise ValueError("Decode Error: Invalid CB-format instruction syntax")
    rt, offset_str = parts[1], parts[2]
    try:
        # Offset is already calculated as bytes during loading
        offset_val = int(offset_str)
    except ValueError:
        raise ValueError(f"Decode Error: Invalid branch offset for CB-format: '{offset_str}'")
    return {'log': f"  Decode: CB-format (Rt={rt}, ByteOffset={offset_str} [19b origin])",
            'rt': rt, 'branch_offset_val': offset_val, 'branch_offset_bits': 19,
            'read_reg1_addr': rt, # Read register Rt to compare with zero
            'read_reg2_addr': None}

def decode_b_format(parts):
    """ Decodes B-format instructions (B). """
    if len(parts) < 2: raise ValueError("Decode Error: Invalid B-format instruction syntax")
    offset_str = parts[1]
    try:
        # Offset is already calculated as bytes during loading
        offset_val = int(offset_str)
    except ValueError:
        raise ValueError(f"Decode Error: Invalid branch offset for B-format: '{offset_str}'")
    return {'log': f"  Decode: B-format (ByteOffset={offset_str} [26b origin])",
            'branch_offset_val': offset_val, 'branch_offset_bits': 26,
            'read_reg1_addr': None, 'read_reg2_addr': None}


# --- Execute Handlers ---
# Input: decoded_info, controls, read_data1, read_data2, sign_ext_imm, current_pc
# Output: Dictionary containing execution results (log, alu_result, alu_zero_flag, branch_target_addr)

def execute_alu_op(decoded_info, alu_op_map, alu_input1, alu_input2):
    """ Helper for standard ALU operations based on opcode. """
    opcode = decoded_info['opcode']
    operation = alu_op_map.get(opcode)
    if not operation:
        raise ValueError(f"Execute Error: ALU operation mapping missing for {opcode}")
    alu_result, alu_zero_flag = alu(alu_input1, alu_input2, operation)
    # Provide detailed log of the operation
    log_msg = (f"  Execute: ALU Op='{operation}' "
               f"(In1=0x{int(alu_input1):X}, In2=0x{int(alu_input2):X}) -> "
               f"Result=0x{alu_result:X}, Zero={alu_zero_flag}")
    return {'log': log_msg,
            'alu_result': alu_result, 'alu_zero_flag': alu_zero_flag}

def execute_r_type(decoded_info, controls, read_data1, read_data2, sign_ext_imm, current_pc):
    """ Executes R-format ALU operations. """
    alu_op_map = {'ADD': 'add', 'SUB': 'sub', 'AND': 'and', 'ORR': 'orr'}
    # Input 2 comes from read_data2 (Rm)
    return execute_alu_op(decoded_info, alu_op_map, read_data1, read_data2)

def execute_i_type(decoded_info, controls, read_data1, read_data2, sign_ext_imm, current_pc):
    """ Executes I-format ALU operations. """
    alu_op_map = {'ADDI': 'add', 'SUBI': 'sub'}
    # Input 2 comes from sign-extended immediate
    return execute_alu_op(decoded_info, alu_op_map, read_data1, sign_ext_imm)

def execute_d_type(decoded_info, controls, read_data1, read_data2, sign_ext_imm, current_pc):
    """ Executes D-format ALU operation (for address calculation). """
    alu_op_map = {'LDUR': 'add', 'STUR': 'add'} # Both use ALU to add base (Rn=read_data1) + offset (imm=sign_ext_imm)
    return execute_alu_op(decoded_info, alu_op_map, read_data1, sign_ext_imm)

def execute_cb_type(decoded_info, controls, read_data1, read_data2, sign_ext_imm, current_pc):
    """ Executes CB-format logic with EXTENSIVE logging for branch target calculation. """
    rt_reg_name = decoded_info.get('rt', 'N/A')
    offset_val_in = decoded_info.get('branch_offset_val', 'MISSING_OFFSET_VAL') # Get raw offset from decode
    offset_bits = decoded_info.get('branch_offset_bits', 'MISSING_OFFSET_BITS')   # Get bits from decode

    execute_log = f"  Execute: CBZ checking {rt_reg_name}=0x{read_data1:X}.\n"
    assert isinstance(read_data1, int), f"Rt value {read_data1} is not int: {type(read_data1)}"
    _, alu_zero_flag = alu(read_data1, 0, 'pass1')
    execute_log += f"  Execute: ALU Zero Flag = {alu_zero_flag}.\n"

    # --- Log inputs BEFORE sign_extend ---
    execute_log += f"  Execute: PRE-SIGN_EXTEND: offset_val_in={offset_val_in} (Type: {type(offset_val_in)}), offset_bits={offset_bits} (Type: {type(offset_bits)})\n"
    branch_offset_extended = -99999 # Initialize with an obviously wrong value

    try:
        # Ensure inputs are integers before calling sign_extend
        offset_val_int = int(offset_val_in)
        offset_bits_int = int(offset_bits)
        branch_offset_extended = sign_extend(offset_val_int, offset_bits_int)
        # --- Log output AFTER sign_extend ---
        execute_log += f"  Execute: POST-SIGN_EXTEND: branch_offset_extended = {branch_offset_extended} (0x{branch_offset_extended:X}) (Type: {type(branch_offset_extended)})\n"
    except Exception as se_err:
        execute_log += f"  Execute: *** ERROR during sign_extend call: {se_err} ***\n"
        # Optionally re-raise or handle, for now just log and continue to see adder input
        branch_offset_extended = 0 # Use 0 offset if sign_extend failed

    # --- Log inputs BEFORE branch_target_adder ---
    assert isinstance(current_pc, int), f"current_pc {current_pc} is not int: {type(current_pc)}"
    assert isinstance(branch_offset_extended, int), f"branch_offset_extended {branch_offset_extended} is not int: {type(branch_offset_extended)}"
    execute_log += f"  Execute: PRE-ADDER: current_pc=0x{current_pc:X} (Type: {type(current_pc)}), branch_offset_extended=0x{branch_offset_extended:X} (Type: {type(branch_offset_extended)})\n"
    branch_target_addr = -88888 # Initialize with an obviously wrong value

    try:
        branch_target_addr = branch_target_adder(current_pc, branch_offset_extended)
         # --- Log output AFTER branch_target_adder ---
        execute_log += f"  Execute: POST-ADDER: branch_target_addr = {branch_target_addr} (0x{branch_target_addr:X}) (Type: {type(branch_target_addr)})"
    except Exception as add_err:
         execute_log += f"  Execute: *** ERROR during branch_target_adder call: {add_err} ***"
         branch_target_addr = current_pc # Default to current PC if adder failed

    return {'log': execute_log,
            'alu_result': read_data1,
            'alu_zero_flag': alu_zero_flag,
            'branch_target_addr': branch_target_addr} # Return the calculated (or error default) target

def execute_b_type(decoded_info, controls, read_data1, read_data2, sign_ext_imm, current_pc):
    """ Executes B-format logic (branch target calculation only). """
    # ALU is not used for B instruction (ALUOp='XX')
    execute_log = "  Execute: B instruction - ALU not used.\n"

    # Branch target calculation: PC + sign_extended(byte_offset)
    branch_offset_extended = sign_extend(decoded_info['branch_offset_val'], decoded_info['branch_offset_bits'])
    branch_target_addr = branch_target_adder(current_pc, branch_offset_extended)
    execute_log += f"  Execute: Calculate Branch Target: PC(0x{current_pc:X}) + Offset({branch_offset_extended}) = 0x{branch_target_addr:X}"

    return {'log': execute_log,
            'alu_result': 0, # ALU result not applicable
            'alu_zero_flag': 0, # Zero flag not applicable
            'branch_target_addr': branch_target_addr}

def execute_nop(decoded_info, controls, read_data1, read_data2, sign_ext_imm, current_pc):
     """ Executes NOP (no operation). """
     return {'log': "  Execute: NOP - No operation performed.", 'alu_result': 0, 'alu_zero_flag': 0}
# (Đặt các hàm này gần các hàm execute khác)

def execute_mul(decoded_info, controls, read_data1, read_data2, sign_ext_imm, current_pc):
    """ Executes MUL (R-format multiplication). """
    # Input 1: Rn (read_data1), Input 2: Rm (read_data2)
    alu_result, alu_zero_flag = alu(read_data1, read_data2, 'mul')
    log_msg = (f"  Execute: ALU Op='mul' "
               f"(In1=0x{int(read_data1):X}, In2=0x{int(read_data2):X}) -> "
               f"Result=0x{alu_result:X}, Zero={alu_zero_flag}")
    return {'log': log_msg,
            'alu_result': alu_result, 'alu_zero_flag': alu_zero_flag}

def execute_div(decoded_info, controls, read_data1, read_data2, sign_ext_imm, current_pc):
    """ Executes DIV (R-format division). Handles division by zero via ALU. """
    # Input 1: Rn (read_data1, dividend), Input 2: Rm (read_data2, divisor)
    try:
        alu_result, alu_zero_flag = alu(read_data1, read_data2, 'div')
        log_msg = (f"  Execute: ALU Op='div' "
                   f"(Dividend=0x{int(read_data1):X}, Divisor=0x{int(read_data2):X}) -> "
                   f"Quotient=0x{alu_result:X}, Zero={alu_zero_flag}")
        return {'log': log_msg,
                'alu_result': alu_result, 'alu_zero_flag': alu_zero_flag}
    except ValueError as e: # Catch division by zero from ALU
         log_msg = (f"  Execute: ALU Op='div' "
                    f"(Dividend=0x{int(read_data1):X}, Divisor=0x{int(read_data2):X}) -> "
                    f"ERROR: {e}")
         # Raise the error again to halt execution in the main generator
         raise ValueError(log_msg) from e

# --- Memory Handlers ---
# Input: decoded_info, controls, alu_result (memory address), read_data2 (data for store), data_mem_dict
# Output: Dictionary containing memory stage results (log, data_read_from_mem)

def memory_noop(decoded_info, controls, alu_result, read_data2, data_mem_dict):
    """ Handles instructions with no memory access. """
    return {'log': "  Memory: No memory operation required.", 'data_read_from_mem': None}

def memory_read(decoded_info, controls, alu_result, read_data2, data_mem_dict):
    """ Handles memory read (LDUR). """
    mem_address = alu_result # Address comes from ALU result (Base + Offset)
    try:
        data = read_memory(data_mem_dict, mem_address)
        log_msg = f"  Memory Read: Accessing Addr=0x{mem_address:X} -> Read Data=0x{data:X}"
        return {'log': log_msg, 'data_read_from_mem': data}
    except Exception as e:
        # Catch potential errors during memory interaction (though read_memory handles missing keys)
        raise ValueError(f"Memory Stage Error during read at 0x{mem_address:X}: {e}")

def memory_write(decoded_info, controls, alu_result, read_data2, data_mem_dict):
    """ Handles memory write (STUR). """
    mem_address = alu_result # Address comes from ALU result (Base + Offset)
    data_to_write = read_data2 # Data comes from Rt (read in Decode stage)
    rt_reg_name = decoded_info.get('rt', 'N/A') # Get Rt name for logging
    try:
        write_memory(data_mem_dict, mem_address, data_to_write)
        log_msg = (f"  Memory Write: Accessing Addr=0x{mem_address:X}, Writing Data=0x{data_to_write:X} "
                   f"(from reg {rt_reg_name}) -> Write successful.")
        return {'log': log_msg} # No data read during write
    except Exception as e:
        raise ValueError(f"Memory Stage Error during write at 0x{mem_address:X}: {e}")


# --- Write Back Handlers ---
# These handlers primarily generate log messages for the WB stage.
# The actual register writing happens in the main generator after Mux selection.
# Input: decoded_info, controls, alu_result, data_read_from_mem, registers_dict
# Output: Dictionary containing write back log message.

def writeback_alu_result(decoded_info, controls, alu_result, data_read_from_mem, registers_dict):
    """ Logs write back for instructions writing ALU result (R-type, I-type). """
    dest_reg = decoded_info.get('rd')
    if controls.get('RegWrite') == 1 and dest_reg:
        # Assumes Mux3 selected ALU result (MemToReg=0)
        return {'log': f"  Write Back: Intending to write ALU Result (0x{alu_result:X}) to {dest_reg}."}
    else:
        return {'log': "  Write Back: No register write intended by this instruction type or RegWrite=0."}

def writeback_mem_data(decoded_info, controls, alu_result, data_read_from_mem, registers_dict):
    """ Logs write back for instructions writing Memory data (LDUR). """
    dest_reg = decoded_info.get('rt') # Destination for LDUR is Rt
    if controls.get('RegWrite') == 1 and dest_reg and data_read_from_mem is not None:
         # Assumes Mux3 selected Memory data (MemToReg=1)
        return {'log': f"  Write Back: Intending to write Memory Data (0x{data_read_from_mem:X}) to {dest_reg}."}
    elif controls.get('RegWrite') == 1 and dest_reg:
         return {'log': f"  Write Back: RegWrite=1 for {dest_reg} but no data was read from memory (data_read_from_mem is None)."}
    else:
        return {'log': "  Write Back: No register write intended by this instruction type or RegWrite=0."}

def writeback_noop(decoded_info, controls, alu_result, data_read_from_mem, registers_dict):
    """ Logs write back for instructions that don't write back (STUR, B, CBZ, NOP). """
    return {'log': "  Write Back: No register write performed by this instruction."}


# --- Instruction Handler Dispatch Table ---
# Maps opcode strings to their corresponding handler functions for each stage.
INSTRUCTION_HANDLERS = {
    # Opcode: {'decode': fn, 'execute': fn, 'memory': fn, 'writeback': fn_for_logging }
    'ADD':  {'decode': decode_r_format,      'execute': execute_r_type,   'memory': memory_noop,   'writeback': writeback_alu_result},
    'SUB':  {'decode': decode_r_format,      'execute': execute_r_type,   'memory': memory_noop,   'writeback': writeback_alu_result},
    'AND':  {'decode': decode_r_format,      'execute': execute_r_type,   'memory': memory_noop,   'writeback': writeback_alu_result},
    'ORR':  {'decode': decode_r_format,      'execute': execute_r_type,   'memory': memory_noop,   'writeback': writeback_alu_result},

    'MUL':  {'decode': decode_r_format,      'execute': execute_mul,      'memory': memory_noop,   'writeback': writeback_alu_result},
    'DIV':  {'decode': decode_r_format,      'execute': execute_div,      'memory': memory_noop,   'writeback': writeback_alu_result},

    'ADDI': {'decode': decode_i_format,      'execute': execute_i_type,   'memory': memory_noop,   'writeback': writeback_alu_result},
    'SUBI': {'decode': decode_i_format,      'execute': execute_i_type,   'memory': memory_noop,   'writeback': writeback_alu_result},
    'LDUR': {'decode': decode_d_format_load, 'execute': execute_d_type,   'memory': memory_read,   'writeback': writeback_mem_data},
    'STUR': {'decode': decode_d_format_store,'execute': execute_d_type,   'memory': memory_write,  'writeback': writeback_noop},
    'CBZ':  {'decode': decode_cb_format,     'execute': execute_cb_type,  'memory': memory_noop,   'writeback': writeback_noop},
    'B':    {'decode': decode_b_format,      'execute': execute_b_type,   'memory': memory_noop,   'writeback': writeback_noop},
    'NOP':  {'decode': decode_nop,           'execute': execute_nop,      'memory': memory_noop,   'writeback': writeback_noop},
}


# ==============================================================================
# Main Execution Generator (REFACTORED with Dispatch Table)
# ==============================================================================
def execute_instruction_detailed_generator(current_pc, registers_dict, data_mem_dict, instr_mem_dict):
    """
    Generator REFACTORED to use dispatch tables for instruction handling.
    Yields MicroStepState objects for visualization.
    Returns a dictionary {'next_pc': value, 'error': msg} upon completion or error.
    """
    instruction_str = "NOP" # Raw instruction string fetched
    final_next_pc = current_pc + 4 # Default next PC assumption
    pc_p4 = 0 # Calculated PC+4 value

    # State variables carried between stages
    control_values = {}       # Control signals for the current instruction
    decoded_info = {}         # Result from the decode handler
    exec_result = {}          # Result from the execute handler
    mem_result = {}           # Result from the memory handler
    wb_log_result = {}        # Result from the writeback handler (log message only)

    read_data1, read_data2 = 0, 0 # Data read from register file
    sign_extended_imm = 0     # Sign-extended immediate value
    alu_result = 0            # Result from ALU
    alu_zero_flag = 0         # Zero flag from ALU
    data_read_from_mem = None # Data read from memory (initially None)
    branch_target_addr = 0    # Calculated branch target address

    current_stage_name = "Start" # For error reporting if crash happens early
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
            # Fetch instruction using the provided PC and instruction memory view
            instruction_str = fetch_instruction_from_mem(instr_mem_dict, current_pc)
            stage_log_if += f"  Fetched Instruction: '{instruction_str}'\n"
        except ValueError as e:
            stage_log_if += f"  Error: {e}\n"
            # Yield error state and terminate generator
            yield MicroStepState(current_stage_name, current_micro_step_index, stage_log_if, active_blocks_if, active_paths_if, animated_signals_if).to_dict()
            return {"next_pc": current_pc, "error": str(e)} # Return current PC on fetch error

        # Calculate PC + 4
        pc_p4 = pc_plus_4_adder(current_pc)
        stage_log_if += f"  PC+4 Adder -> 0x{pc_p4:X}"
        active_paths_if.append("path-adder1-mux4-in0") # Path from Adder1 output
        animated_signals_if.append({"path_id": "path-adder1-mux4-in0", "bits":[1], "duration": 0.2, "start_delay": 0.2}) # Animate signal
        yield MicroStepState(current_stage_name, current_micro_step_index, stage_log_if, active_blocks_if, active_paths_if, animated_signals_if).to_dict()
        final_next_pc = pc_p4 # Update default next PC


        # --- Micro-Step 1: Instruction Decode / Register Fetch (ID) ---
        current_stage_name = "Decode"
        current_micro_step_index = 1
        stage_log_id = f"[{current_stage_name}]\n"
        active_blocks_id = ["block-control", "block-regs"] # Control unit and Register file are active
        active_paths_id = ["path-imem-out", "path-instr-control", "path-instr-regs"] # Paths from IMEM to Control and Regs
        animated_signals_id = [
            {"path_id": "path-imem-out", "bits":[1], "duration": 0.1}, # Signal out of IMEM
            {"path_id": "path-instr-control", "bits":[1], "duration": 0.2}, # To Control
            {"path_id": "path-instr-regs", "bits":[1], "duration": 0.2}, # To RegFile read addresses
        ]
        try:
            # 1. Parse instruction string
            instruction_str_upper = instruction_str.strip().upper()
            # Split by comma, whitespace, parentheses, brackets - removing empty parts
            parts = re.split(r'[,\s()\[\]]+', instruction_str_upper)
            parts = [p for p in parts if p]
            opcode = parts[0].upper() if parts else "NOP" # Ensure uppercase opcode
            stage_log_id += f"  Opcode Detected: {opcode}\n"

            # 2. Get Control Signals using the detected opcode
            control_values = calculate_control_signals(opcode)
            # stage_log_id += f"  Control Signals: {control_values}\n" # Optional: Very verbose log

            # 3. Find and Call the Decode Handler
            handlers = INSTRUCTION_HANDLERS.get(opcode)
            if not handlers or 'decode' not in handlers:
                raise ValueError(f"Unsupported instruction or missing decode handler for opcode: {opcode}")
            decode_handler = handlers['decode']
            decoded_info = decode_handler(parts)
            decoded_info['opcode'] = opcode # Ensure opcode is stored in decoded info
            stage_log_id += decoded_info.get('log', "  (No decode log)") + "\n"

            # 4. Perform Register Reads based on addresses from decode_handler
            read_reg1_addr = decoded_info.get('read_reg1_addr')
            read_reg2_addr = decoded_info.get('read_reg2_addr')
            if read_reg1_addr:
                read_data1 = read_register(registers_dict, read_reg1_addr)
                stage_log_id += f"  Read Register 1 ({read_reg1_addr}): 0x{read_data1:X}\n"
                active_paths_id.append("path-regs-rdata1") # Path for read data 1 output
                animated_signals_id.append({"path_id": "path-regs-rdata1", "bits":[1], "duration": 0.3, "start_delay": 0.2})
            if read_reg2_addr:
                read_data2 = read_register(registers_dict, read_reg2_addr)
                stage_log_id += f"  Read Register 2 ({read_reg2_addr}): 0x{read_data2:X}\n"
                active_paths_id.append("path-regs-rdata2") # Path for read data 2 output
                animated_signals_id.append({"path_id": "path-regs-rdata2", "bits":[1], "duration": 0.3, "start_delay": 0.2})

            # 5. Perform Sign Extension (if immediate value exists)
            imm_val = decoded_info.get('imm_val')
            if imm_val is not None:
                imm_bits = decoded_info.get('imm_bits', 0)
                sign_extended_imm = sign_extend(imm_val, imm_bits)
                stage_log_id += f"  Sign Extend Immediate ({imm_bits}b): Val={imm_val} -> {sign_extended_imm} (0x{sign_extended_imm:X})\n"
                if "block-signext" not in active_blocks_id: active_blocks_id.append("block-signext")
                # Visualize path from instruction bits (conceptually) to sign extender
                active_paths_id.extend(["path-instr-signext"])
                animated_signals_id.extend([{"path_id": "path-instr-signext", "bits":[1], "duration": 0.2, "start_delay": 0.1}])
                # Visualize output path of sign extender (to Mux2)
                active_paths_id.extend(["path-signext-out-mux2"])
                animated_signals_id.extend([{"path_id": "path-signext-out-mux2", "bits":[1], "duration": 0.3, "start_delay": 0.3}])

            # Sign extension for branch offsets happens in Execute stage.
            # Log the raw offset value here if it exists.
            branch_offset_val = decoded_info.get('branch_offset_val')
            if branch_offset_val is not None:
                 branch_offset_bits = decoded_info.get('branch_offset_bits', 0)
                 stage_log_id += f"  Branch Offset Value (from instruction): {branch_offset_val} ({branch_offset_bits}b original)\n"
                 # Visualize path from instruction to Sign Extender (Branch Path)
                 if "block-signext" not in active_blocks_id: active_blocks_id.append("block-signext")
                 active_paths_id.append("path-instr-signext-br") # Specific path for branch immediate
                 animated_signals_id.append({"path_id": "path-instr-signext-br", "bits":[1], "duration": 0.2, "start_delay": 0.1})
                 # Output path visualization (signext-br-adder2) is handled in Execute stage

            yield MicroStepState(current_stage_name, current_micro_step_index, stage_log_id, active_blocks_id, active_paths_id, animated_signals_id, control_values).to_dict()

        except (IndexError, ValueError, TypeError, KeyError) as e:
            # Catch parsing errors, invalid register names, type errors, etc.
            stage_log_id += f"  Error: {e}\n traceback: {traceback.format_exc()}\n"
            yield MicroStepState(current_stage_name, current_micro_step_index, stage_log_id, active_blocks_id, active_paths_id, animated_signals_id, control_values).to_dict()
            return {"next_pc": pc_p4, "error": f"Decode Error: {e}"} # Use PC+4 on decode error


        # --- Micro-Step 2: Execute (EX) ---
        current_stage_name = "Execute"
        current_micro_step_index = 2
        stage_log_ex = f"[{current_stage_name}]\n"
        # ALU, ALU Control, Mux2 are potentially active
        active_blocks_ex = ["block-alu", "block-alucontrol", "block-mux2"]
        active_paths_ex = []
        animated_signals_ex = []

        try:
            # 1. Determine ALU Inputs using ALUSrc mux
            alu_src = control_values.get('ALUSrc', 0)
            alu_input1_val = read_data1 # ALU Input 1 always comes from ReadData1
            alu_input2_val = alu_input2_mux(read_data2, sign_extended_imm, alu_src)

            # Visualize ALU Input 1 path
            reg1_source_name = decoded_info.get('read_reg1_addr', 'N/A')
            stage_log_ex += f"  ALU Input 1 (from {reg1_source_name}): 0x{alu_input1_val:X}\n"
            active_paths_ex.append("path-rdata1-alu")
            animated_signals_ex.append({"path_id": "path-rdata1-alu", "bits":[1], "duration": 0.2})

            # Visualize ALU Input 2 path and Mux2 selection
            if alu_src == 0: # Source is ReadData2
                reg2_source_name = decoded_info.get('read_reg2_addr','N/A')
                stage_log_ex += f"  ALU Input 2 (from {reg2_source_name}): 0x{alu_input2_val:X} (Mux2 Sel=0)\n"
                active_paths_ex.extend(["path-regs-rdata2-mux2", "path-mux2-alu", "mux-alusrc-in0"]) # Path from Regs->Mux, Mux->ALU, Control Sig
                animated_signals_ex.extend([
                    {"path_id": "path-regs-rdata2-mux2", "bits":[1], "duration": 0.1},
                    {"path_id": "path-mux2-alu", "bits":[1], "duration": 0.1, "start_delay": 0.1}
                ])
            else: # Source is Sign Extended Immediate
                stage_log_ex += f"  ALU Input 2 (from Imm): {alu_input2_val} (0x{alu_input2_val:X}) (Mux2 Sel=1)\n"
                active_paths_ex.extend(["path-signext-mux2", "path-mux2-alu", "mux-alusrc-in1"]) # Path from SignExt->Mux, Mux->ALU, Control Sig
                animated_signals_ex.extend([
                    {"path_id": "path-signext-mux2", "bits":[1], "duration": 0.1},
                    {"path_id": "path-mux2-alu", "bits":[1], "duration": 0.1, "start_delay": 0.1}
                ])

            # 2. Find and Call the Execute Handler
            opcode = decoded_info['opcode']
            handlers = INSTRUCTION_HANDLERS.get(opcode)
            if not handlers or 'execute' not in handlers:
                raise ValueError(f"Missing execute handler for opcode: {opcode}")
            execute_handler = handlers['execute']

            # Pass necessary info to the handler
            exec_result = execute_handler(decoded_info, control_values, alu_input1_val, alu_input2_val, sign_extended_imm, current_pc)
            stage_log_ex += exec_result.get('log', "  (No execute log)") + "\n"

            # 3. Store results from execution handler
            alu_result = exec_result.get('alu_result', 0) # Default to 0 if not returned
            alu_zero_flag = exec_result.get('alu_zero_flag', 0) # Default to 0
            branch_target_addr = exec_result.get('branch_target_addr', 0) # Default to 0

            # 4. Common Execute Stage Visualization
            # Visualize ALU result path (if ALU was used, indicated by non-'XX' ALUOp)
            if control_values.get('ALUOp') != 'XX':
                active_paths_ex.append("path-alu-result") # Path from ALU output
                animated_signals_ex.append({"path_id": "path-alu-result", "bits":[1], "duration": 0.3, "start_delay": 0.2})
                # Also visualize Zero flag output path to branch logic control
                active_paths_ex.append("path-alu-zero")
                animated_signals_ex.append({"path_id": "path-alu-zero", "bits":[alu_zero_flag], "duration": 0.1, "start_delay": 0.2})

            # Visualize Branch Target Address Calculation path (if applicable)
            if branch_target_addr != 0: # Branch target was calculated
                 if "block-adder2" not in active_blocks_ex: active_blocks_ex.append("block-adder2")
                 # Input 1: PC
                 active_paths_ex.append("path-pc-adder2")
                 animated_signals_ex.append({"path_id": "path-pc-adder2", "bits":[1], "duration": 0.2})
                 # Input 2: Sign-extended branch offset (output from Sign Extender block - branch path)
                 active_paths_ex.append("path-signext-br-adder2") # Path from SignExt (branch) to Adder2
                 animated_signals_ex.append({"path_id": "path-signext-br-adder2", "bits":[1], "duration": 0.2})
                 # Output: Branch Adder (Adder2) output path to Mux4
                 active_paths_ex.append("path-adder2-mux4-in1")
                 animated_signals_ex.append({"path_id": "path-adder2-mux4-in1", "bits":[1], "duration": 0.2, "start_delay": 0.2})

            yield MicroStepState(current_stage_name, current_micro_step_index, stage_log_ex, active_blocks_ex, active_paths_ex, animated_signals_ex, control_values).to_dict()

        except (ValueError, TypeError) as e:
            stage_log_ex += f"  Error: {e}\n traceback: {traceback.format_exc()}\n"
            yield MicroStepState(current_stage_name, current_micro_step_index, stage_log_ex, active_blocks_ex, active_paths_ex, animated_signals_ex, control_values).to_dict()
            return {"next_pc": pc_p4, "error": f"Execute Error: {e}"}


        # --- Micro-Step 3: Memory Access (MEM) ---
        current_stage_name = "Memory"
        current_micro_step_index = 3
        stage_log_mem = f"[{current_stage_name}]\n"
        active_blocks_mem = [] # Data Memory block might be active
        active_paths_mem = []
        animated_signals_mem = []

        try:
            # 1. Get Memory Control Signals
            mem_read = control_values.get('MemRead', 0)
            mem_write = control_values.get('MemWrite', 0)

            # 2. Find and Call the Memory Handler
            opcode = decoded_info['opcode']
            handlers = INSTRUCTION_HANDLERS.get(opcode)
            if not handlers or 'memory' not in handlers:
                raise ValueError(f"Missing memory handler for opcode: {opcode}")
            memory_handler = handlers['memory']

            # Pass ALU result (potential address) and ReadData2 (for store)
            mem_result = memory_handler(decoded_info, control_values, alu_result, read_data2, data_mem_dict)
            stage_log_mem += mem_result.get('log', "  (No memory log)") + "\n"

            # 3. Store result from memory handler
            data_read_from_mem = mem_result.get('data_read_from_mem') # Will be None if no read occurred

            # 4. Common Memory Stage Visualization
            mem_address = alu_result # Address for LDUR/STUR comes from ALU result

            if mem_read == 1:
                if "block-datamem" not in active_blocks_mem: active_blocks_mem.append("block-datamem")
                # Visualize address path from ALU to Data Memory
                active_paths_mem.extend(["path-alu-memaddr"])
                animated_signals_mem.extend([{"path_id": "path-alu-memaddr", "bits":[1], "duration": 0.2}])
                # Visualize MemRead control signal enable
                active_paths_mem.extend(["control-memread-enable"])
                animated_signals_mem.extend([{"path_id": "control-memread-enable", "bits":[1], "duration": 0.1}])
                # Visualize data path from Data Memory output
                if data_read_from_mem is not None:
                    active_paths_mem.append("path-mem-readdata")
                    animated_signals_mem.append({"path_id": "path-mem-readdata", "bits":[1], "duration": 0.3, "start_delay": 0.2})
            elif mem_write == 1:
                if "block-datamem" not in active_blocks_mem: active_blocks_mem.append("block-datamem")
                 # Visualize address path from ALU to Data Memory
                active_paths_mem.extend(["path-alu-memaddr"])
                animated_signals_mem.extend([{"path_id": "path-alu-memaddr", "bits":[1], "duration": 0.2}])
                 # Visualize data path from ReadData2 to Data Memory Write Data port
                active_paths_mem.extend(["path-rdata2-memwrite"])
                animated_signals_mem.extend([{"path_id": "path-rdata2-memwrite", "bits":[1], "duration": 0.3, "start_delay": 0.1}])
                 # Visualize MemWrite control signal enable
                active_paths_mem.extend(["control-memwrite-enable"])
                animated_signals_mem.extend([{"path_id": "control-memwrite-enable", "bits":[1], "duration": 0.1}])

            yield MicroStepState(current_stage_name, current_micro_step_index, stage_log_mem, active_blocks_mem, active_paths_mem, animated_signals_mem, control_values).to_dict()

        except (ValueError, TypeError, KeyError) as e: # KeyError for potential memory access errors
            stage_log_mem += f"  Error: {e}\n traceback: {traceback.format_exc()}\n"
            yield MicroStepState(current_stage_name, current_micro_step_index, stage_log_mem, active_blocks_mem, active_paths_mem, animated_signals_mem, control_values).to_dict()
            return {"next_pc": pc_p4, "error": f"Memory Error: {e}"}


        # --- Micro-Step 4: Write Back (WB) & PC Update ---
        current_stage_name = "Write Back / PC Update"
        current_micro_step_index = 4
        stage_log_wb = f"[{current_stage_name}]\n"
        active_blocks_wb = [] # Mux3 (WB Mux), Mux4 (PC Mux) potentially active
        active_paths_wb = []
        animated_signals_wb = []

        try:
            # --- Part 1: Write Back to Register File ---
            reg_write = control_values.get('RegWrite', 0)
            mem_to_reg = control_values.get('MemToReg', 0) # Default to 0 (ALU->WB)
            data_to_write_back = None
            write_occurred = False
            wb_specific_log = "" # Accumulate WB specific log messages

            if reg_write == 1:
                active_blocks_wb.append("block-mux3") # Activate Write Back Mux
                # Determine data source using Mux3 logic
                data_to_write_back = writeback_data_mux(alu_result, data_read_from_mem, mem_to_reg)

                # Find destination register (Rd for R/I, Rt for LDUR)
                dest_reg = decoded_info.get('rd') or decoded_info.get('rt')

                if data_to_write_back is not None and dest_reg:
                    wb_specific_log += f"  Write Back Stage: RegWrite=1 for {dest_reg}.\n"
                    # Visualize RegWrite control signal and destination address path
                    active_paths_wb.extend(["control-regwrite-enable", "path-instr-regwriteaddr"])
                    animated_signals_wb.extend([
                        {"path_id": "control-regwrite-enable", "bits":[1],"duration":0.1},
                        {"path_id": "path-instr-regwriteaddr", "bits":[1],"duration":0.2} # Path for Rd/Rt address
                    ])

                    # Visualize Mux3 selection and data path to Register File Write Port
                    wb_path_mux_out = "path-mux3-wb"   # Path out of Mux3
                    wb_path_to_regs = "path-wb-regwrite" # Path from Mux3 output to RegFile write data input
                    active_paths_wb.extend([wb_path_mux_out, wb_path_to_regs])
                    mux3_in_path, mux3_sel_path = "", ""

                    if mem_to_reg == 0: # Data from ALU Result
                        wb_specific_log += f"  Write Back Stage: Mux3 selects ALU Result (0x{data_to_write_back:X}).\n"
                        mux3_in_path = "path-alu-mux3-in0" # Path from ALU result to Mux3 input 0
                        mux3_sel_path = "mux-memtoreg-in0" # Control signal selecting input 0
                    elif mem_to_reg == 1: # Data from Memory Read
                        wb_specific_log += f"  Write Back Stage: Mux3 selects Memory Data (0x{data_to_write_back:X}).\n"
                        mux3_in_path = "path-mem-readdata-mux3" # Path from Memory data to Mux3 input 1
                        mux3_sel_path = "mux-memtoreg-in1" # Control signal selecting input 1
                    # else: mem_to_reg == -1 handled by data_to_write_back being None

                    if mux3_in_path: active_paths_wb.append(mux3_in_path)
                    if mux3_sel_path: active_paths_wb.append(mux3_sel_path)
                    animated_signals_wb.extend([
                        {"path_id": mux3_in_path, "bits":[1], "duration": 0.1},
                        {"path_id": wb_path_mux_out, "bits":[1], "duration": 0.2, "start_delay": 0.1},
                        {"path_id": wb_path_to_regs, "bits":[1], "duration": 0.1, "start_delay": 0.3},
                    ])

                    # Perform the actual register write
                    try:
                        write_register(registers_dict, dest_reg, data_to_write_back)
                        wb_specific_log += f"  Write Back Stage: Successfully wrote 0x{data_to_write_back:X} to {dest_reg}.\n"
                        write_occurred = True
                    except ValueError as e:
                        raise ValueError(f"Write Back Error: {e}") # Propagate write error

                elif reg_write == 1: # RegWrite=1 but data is None (e.g., STUR) or dest_reg missing
                     wb_specific_log += f"  Write Back Stage: RegWrite=1 but no data determined for write back (MemToReg={mem_to_reg}) or missing destination register '{dest_reg}'.\n"

            # Call Write Back Handler just for consistent logging based on instruction type's intent
            opcode = decoded_info['opcode']
            handlers = INSTRUCTION_HANDLERS.get(opcode)
            if handlers and 'writeback' in handlers:
                 wb_log_result = handlers['writeback'](decoded_info, control_values, alu_result, data_read_from_mem, registers_dict)
                 wb_specific_log += wb_log_result.get('log', "  (No WB handler log)") + "\n"

            if not write_occurred and reg_write == 0 :
                 wb_specific_log += "  Write Back Stage: No register write needed (RegWrite=0).\n"

            # Add accumulated WB log to the main stage log
            stage_log_wb += wb_specific_log


            # --- Part 2: PC Update ---
            active_blocks_wb.append("block-mux4") # Activate PC Source Mux
            branch_signal = control_values.get('Branch', 0)         # For CBZ = 1
            uncond_branch_signal = control_values.get('UncondBranch', 0) # For B = 1
            opcode_for_debug = decoded_info.get('opcode', 'N/A') # Get opcode for logging

            # --- DETAILED PC Update LOG ---
            pc_update_log = f"  PC Update Logic Input: Opcode='{opcode_for_debug}', BranchSig={branch_signal}, UncondBranchSig={uncond_branch_signal}, ALUZeroFlag={alu_zero_flag}\n"

            # Determine PCSrc signal using branch logic
            pc_src_signal = branch_control_logic(branch_signal, alu_zero_flag, uncond_branch_signal)
            pc_update_log += f"  PC Update Logic Result: PCSrc Signal = {pc_src_signal} (1 => Branch Taken/Target Address, 0 => PC+4).\n"

            # Determine final next PC value using Mux4 logic
            final_next_pc = pc_source_mux(pc_p4, branch_target_addr, pc_src_signal)
            pc_update_log += f"  PC Source Mux Output: Selected Next PC = 0x{final_next_pc:X}"
            if pc_src_signal == 1 and branch_target_addr != 0:
                pc_update_log += f" (from Branch Target Addr 0x{branch_target_addr:X})\n"
            elif pc_src_signal == 0:
                 pc_update_log += f" (from PC+4 Addr 0x{pc_p4:X})\n"
            else: # Should not happen if branch target addr was 0 but PCSrc was 1
                 pc_update_log += " (Source unclear based on PCSrc/BranchTarget)\n"
            # --- END DETAILED PC Update LOG ---

            # Add PC update log to the main stage log
            stage_log_wb += pc_update_log

            # --- Visualization for Mux4 ---
            path_mux4_out = "path-mux4-pc" # Common path out of Mux4 to PC register
            active_paths_wb.append(path_mux4_out)
            mux4_in_path, mux4_sel_path = "", ""
            if pc_src_signal == 1: # Select Branch Target Address
                mux4_in_path = "path-adder2-mux4-in1" # Path from Branch Adder output to Mux4 input 1
                mux4_sel_path = "mux-pcsrc-in1" # Control signal selecting input 1
            else: # Select PC+4
                mux4_in_path = "path-adder1-mux4-in0" # Path from PC+4 Adder output to Mux4 input 0
                mux4_sel_path = "mux-pcsrc-in0" # Control signal selecting input 0

            active_paths_wb.extend([mux4_in_path, mux4_sel_path])
            animated_signals_wb.extend([
                {"path_id": mux4_in_path, "bits":[1], "duration": 0.1 },
                {"path_id": path_mux4_out, "bits":[1], "duration": 0.2, "start_delay": 0.1}
            ])
            # --- End Visualization for Mux4 ---

            yield MicroStepState(current_stage_name, current_micro_step_index, stage_log_wb, active_blocks_wb, active_paths_wb, animated_signals_wb, control_values).to_dict()

            # Instruction finished successfully, return the calculated next PC
            return {"next_pc": final_next_pc}

        except (ValueError, TypeError) as e:
            # Catch errors during WB Mux logic or PC update logic
            stage_log_wb += f"  Error: {e}\n traceback: {traceback.format_exc()}\n"
            yield MicroStepState(current_stage_name, current_micro_step_index, stage_log_wb, active_blocks_wb, active_paths_wb, animated_signals_wb, control_values).to_dict()
            # On WB/PCUpdate error, proceed with PC+4 as a safer default? Or halt? Let's use PC+4.
            return {"next_pc": pc_p4, "error": f"Write Back / PC Update Error: {e}"}

    except StopIteration:
        # This should not be caught here if the generator yields correctly
        raise # Re-raise to be handled by the caller API endpoint
    except Exception as e:
        # Catch any unexpected runtime errors during any stage
        error_msg = (f"Unexpected Runtime Error in Generator for instruction at PC=0x{current_pc:X} "
                     f"(Stage: {current_stage_name}, Step: {current_micro_step_index}): {e}\n"
                     f"{traceback.format_exc()}")
        print(f"FATAL GENERATOR ERROR: {error_msg}")
        # Attempt to yield a final error state
        try:
            last_ctrl = control_values if 'control_values' in locals() else {}
            yield MicroStepState(current_stage_name, current_micro_step_index, error_msg, [], [], [], last_ctrl).to_dict()
        except Exception: pass # Ignore errors during error reporting yield
        # Stop execution by returning the current PC and the error message
        return {"next_pc": current_pc, "error": error_msg}


# ==============================================================================
# Flask Application Setup and API Endpoints
# ==============================================================================
app = Flask(__name__)

# --- Global Simulation State ---
# Stores the entire state of the simulator (PC, registers, memory, etc.)
sim_state = {}

# --- State Initialization and Formatting ---
def initialize_sim_state():
    """ Resets the simulation state to its initial default values. """
    global sim_state
    sim_state = {
        'pc': 0,
        'registers': {f"X{i}": 0 for i in range(31)}, # X0-X30 initialized
        'data_memory': {}, # Key: address (int), Value: data (int)
        'instruction_memory': {}, # Key: address (int), Value: processed instruction string (numeric offsets)
        'raw_instruction_memory': {}, # Key: address (int), Value: original instruction string (with labels)
        'label_table': {}, # Key: label name (str), Value: address (int)
        'current_instruction_generator': None, # Holds the active generator object
        'simulation_loaded': False, # Flag indicating if code is loaded
        'error_state': None, # Stores error message if simulation halts
        'current_instr_addr': -1, # Address of the instruction being executed
        'current_instr_str': "",  # Raw string of the instruction being executed
        'micro_step_index': -1,   # Index of the last completed micro-step
        'instruction_completed_flag': False # Flag set when an instruction finishes
    }
    # Explicitly handle XZR and SP initialization
    sim_state['registers']["XZR"] = 0 # Ensure XZR exists and is 0
    sp_initial_value = 0x7FFFFFFF00 # Example high memory address for stack
    sim_state['registers']["X28"] = sp_initial_value # Initialize SP (X28)
    print("--- Simulation state reset to defaults. ---")

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


# --- API Endpoints ---
@app.route('/')
def index():
    """ Serves the main HTML page. """
    return render_template('index.html')

@app.route('/api/load', methods=['POST'])
def api_load():
    """
    Loads ARMv8 assembly code, performs two passes for label resolution,
    and initializes the simulation state.
    Pass 1: Find labels and assign addresses. Store raw instructions.
    Pass 2: Resolve branch labels to numeric byte offsets. Store processed instructions.
    """
    print("\n>>> Received /api/load request <<<")
    initialize_sim_state() # Reset state before loading new code
    try:
        data = request.get_json()
        if not data or 'code' not in data: raise ValueError("Missing 'code' field in request")
        code = data['code']
        if not isinstance(code, str): raise ValueError("'code' field must be a string")

        lines = code.splitlines()
        current_address = 0
        label_table = {}          # label_name -> address
        raw_instructions_list = [] # Temp list to hold info before Pass 2
        # Reset memory stores in global state
        sim_state['instruction_memory'] = {} # address -> processed_instruction (numeric offset)
        sim_state['raw_instruction_memory'] = {} # address -> original_instruction (with label)
        sim_state['label_table'] = {}

        # --- Pass 1: Build Label Table & Store Raw Instruction Info ---
        print("--- Load Pass 1: Finding labels and addresses ---")
        line_num = 0
        for line in lines:
            line_num += 1
            original_line = line
            # Remove comments (//...) and leading/trailing whitespace
            cleaned_line = line.split('//')[0].strip()
            if not cleaned_line: continue # Skip empty or comment-only lines

            # Check for label definition (label_name:)
            label_match = re.match(r'^([a-zA-Z_][a-zA-Z0-9_]*):\s*(.*)', cleaned_line)
            instruction_part = cleaned_line # Assume line is instruction unless label found

            if label_match:
                label = label_match.group(1)
                instruction_part = label_match.group(2).strip() # Text after the label
                if label in label_table:
                    raise ValueError(f"Duplicate label '{label}' defined on line {line_num}")
                label_table[label] = current_address
                print(f"  Label Found: '{label}' => Address 0x{current_address:X}")

            # If there's an instruction part (after label or if no label)
            if instruction_part:
                # Basic check to ignore common assembler directives (can be expanded)
                if not instruction_part.startswith(('.', '#')): # Ignore lines starting with . or #
                    raw_instructions_list.append({
                        'address': current_address,
                        'text': instruction_part, # Instruction text only (no label def)
                        'original': original_line # Full original line for display
                    })
                    # Store the *original* line text in raw memory immediately for display later
                    sim_state['raw_instruction_memory'][current_address] = original_line.strip()
                    current_address += 4 # Increment address for next instruction
                else:
                     print(f"  Skipping directive/comment: '{instruction_part}'")

        sim_state['label_table'] = label_table
        print(f"--- Load Pass 1 Complete. Labels: {label_table} ---")

        # --- Pass 2: Resolve Branch Labels to Byte Offsets ---
        print("--- Load Pass 2: Resolving branch labels to byte offsets ---")
        branch_opcodes = {"CBZ", "B"} # Opcodes that use labels for branching
        instr_count = 0

        for instr_info in raw_instructions_list:
            address = instr_info['address']
            instr_text = instr_info['text'] # Instruction part without label def

            processed_instr_text = instr_text # Start with the original instruction text
            # Parse for opcode check
            parts_process = re.split(r'[,\s()\[\]]+', instr_text.upper())
            parts_process = [p for p in parts_process if p]
            opcode_process = parts_process[0].upper() if parts_process else None

            # Check if this instruction is a branch that needs label resolution
            if opcode_process in branch_opcodes:
                potential_label = None
                label_to_replace_in_text = None

                # Try to extract the label operand using regex on the *original case* text
                label_match = None
                if opcode_process == "CBZ" and len(parts_process) >= 3:
                    # Regex: find comma, optional whitespace, then label name at the end
                    label_match = re.search(r'[,]\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*$', instr_text.strip())
                elif opcode_process == "B" and len(parts_process) >= 2:
                    # Regex: find whitespace, then label name at the end
                    label_match = re.search(r'\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*$', instr_text.strip())

                if label_match:
                    potential_label = label_match.group(1) # The matched label name (original case)
                    label_to_replace_in_text = potential_label
                    # print(f"  Checking label '{potential_label}' in '{instr_text}' at 0x{address:X}") # Debug

                    # Look up the label in the table (case-insensitive comparison for lookup key)
                    label_upper = potential_label.upper()
                    target_address = None
                    actual_label_key = None
                    for k, v in label_table.items():
                         if k.upper() == label_upper:
                              target_address = v
                              actual_label_key = k # Store the actual case used in definition
                              break

                    if target_address is not None:
                        # Calculate byte offset: Target Address - Current Instruction Address
                        offset = target_address - address
                        print(f"  Label '{actual_label_key}' in '{instr_text}' resolved to 0x{target_address:X}. Calculated Byte Offset = {offset}")

                        # Replace the label name with the numeric byte offset in the instruction string
                        if opcode_process == "CBZ":
                            processed_instr_text = re.sub(r'[,]\s*' + re.escape(label_to_replace_in_text) + r'\s*$', f', {offset}', instr_text.strip())
                        elif opcode_process == "B":
                            processed_instr_text = re.sub(r'\s+' + re.escape(label_to_replace_in_text) + r'\s*$', f' {offset}', instr_text.strip())
                        # print(f"    Processed instruction text: '{processed_instr_text}'") # Debug

                    else: # Label was found in instruction text but not in the label table
                        raise ValueError(f"Undefined label '{potential_label}' used in instruction: '{instr_text}' at 0x{address:X}")
                elif len(parts_process) >= (3 if opcode_process == "CBZ" else 2):
                    # If regex didn't match but structure seems like branch, check if last part is number or unresolved label
                    last_part = instr_text.split()[-1].lstrip(',') # Get last word/number, remove potential leading comma for CBZ
                    try:
                        int(last_part) # If it's already a number, assume it's the offset
                        print(f"  Branch instruction '{instr_text}' at 0x{address:X} appears to use numeric offset directly.")
                        processed_instr_text = instr_text # Keep as is
                    except ValueError:
                        # It's not a number, and didn't match a label -> error
                        raise ValueError(f"Syntax error or unresolved label '{last_part}' in branch instruction at 0x{address:X}: '{instr_text}'")

            # Store the processed instruction (with numeric offset) for execution
            sim_state['instruction_memory'][address] = processed_instr_text.strip()
            instr_count += 1

        # Finalize simulation state after successful loading
        sim_state['pc'] = 0 # Start execution at address 0
        sim_state['simulation_loaded'] = True
        sim_state['error_state'] = None
        sim_state['current_instruction_generator'] = None
        sim_state['micro_step_index'] = -1
        sim_state['instruction_completed_flag'] = False
        # Set initial instruction display info
        sim_state['current_instr_addr'] = sim_state['pc']
        sim_state['current_instr_str'] = sim_state['raw_instruction_memory'].get(sim_state['pc'], "(No instruction at PC=0)")

        print(f"--- Load Pass 2 Complete. {instr_count} instructions processed and loaded. ---")
        # print(f"DEBUG: Final Instruction Memory (Processed): {sim_state['instruction_memory']}") # Very Verbose
        # print(f"DEBUG: Final Raw Instruction Memory (Original): {sim_state['raw_instruction_memory']}") # Very Verbose

        return jsonify({
            "status": "success",
            "message": f"{instr_count} instructions loaded successfully. Ready to run.",
            "cpu_state": format_cpu_state_api(),
            "initial_instr_addr": f"0x{sim_state['current_instr_addr']:X}",
            "initial_instr_str": sim_state['current_instr_str']
        })

    except Exception as e:
        print(f"[ERROR] /api/load failed: {e}")
        traceback.print_exc()
        initialize_sim_state() # Ensure state is reset on load failure
        return jsonify({"status": "error", "message": f"Load failed: {e}"}), 400


@app.route('/api/micro_step', methods=['POST'])
def api_micro_step():
    """
    Executes the next micro-step of the current instruction using the generator.
    Handles generator initialization, execution, completion, and errors.
    """
    global sim_state # We modify sim_state elements
    print(f"\n>>> Received /api/micro_step request (Current PC=0x{sim_state.get('pc', -1):X}) <<<")

    # Check if simulation is in a runnable state
    if not sim_state.get('simulation_loaded', False):
        error_msg = sim_state.get('error_state', 'Simulation not loaded or has ended.')
        print(f"Micro-step request rejected: {error_msg}")
        return jsonify({"status": "error", "message": error_msg, "cpu_state": format_cpu_state_api()}), 400

    try:
        current_pc = sim_state['pc']

        # --- Handle State Between Instructions ---
        # If the previous instruction just completed, clear the old generator
        # and prepare display info for the *new* instruction at the current PC.
        if sim_state['instruction_completed_flag']:
            print("--- Transitioning to next instruction ---")
            sim_state['instruction_completed_flag'] = False
            sim_state['current_instruction_generator'] = None
            sim_state['micro_step_index'] = -1
            # Update current instruction display info for the *next* instruction
            sim_state['current_instr_addr'] = current_pc
            sim_state['current_instr_str'] = sim_state['raw_instruction_memory'].get(current_pc, "(No instruction)")
            print(f"Ready to start instruction at new PC=0x{current_pc:X}: '{sim_state['current_instr_str']}'")


        # --- Check PC Validity ---
        # Is there an instruction loaded at the current PC?
        if current_pc not in sim_state['instruction_memory']:
            sim_state['simulation_loaded'] = False # Stop simulation
            sim_state['error_state'] = f"Program terminated: No instruction found at PC=0x{current_pc:X}"
            print(f"Execution Halt: {sim_state['error_state']}")
            return jsonify({
                "status": "finished_program", # Use a specific status for normal termination
                "message": sim_state['error_state'],
                "cpu_state": format_cpu_state_api()
            })

        # --- Initialize Generator if needed ---
        # Create a new generator instance if we are starting a new instruction
        if sim_state['current_instruction_generator'] is None:
            sim_state['current_instr_addr'] = current_pc
            sim_state['current_instr_str'] = sim_state['raw_instruction_memory'].get(current_pc, "(Raw instruction missing)")
            # Fetch the *processed* instruction (with numeric offsets) to execute
            instruction_to_execute = sim_state['instruction_memory'][current_pc]

            print(f"--- Creating Generator for Instruction at PC=0x{current_pc:X} ---")
            print(f"  Raw Display: '{sim_state['current_instr_str']}'")
            print(f"  Executing:   '{instruction_to_execute}'")

            # Create a temporary view of instruction memory containing only the current instruction
            temp_instr_mem_for_gen = {current_pc: instruction_to_execute}

            # Create the generator instance, passing mutable state dictionaries
            sim_state['current_instruction_generator'] = execute_instruction_detailed_generator(
                current_pc,
                sim_state['registers'],
                sim_state['data_memory'],
                temp_instr_mem_for_gen # Generator uses this single-instruction view
            )
            sim_state['micro_step_index'] = -1 # Reset micro-step index for the new instruction

        # --- Execute the next micro-step by calling next() on the generator ---
        try:
            print(f"--- Executing Micro-Step {sim_state['micro_step_index'] + 1} (Stage: ?) ---")
            step_data_dict = next(sim_state['current_instruction_generator']) # Get data from generator's yield
            sim_state['micro_step_index'] += 1
            current_stage_name = step_data_dict.get("stage", "Unknown") # Get stage name from yielded data
            print(f"  Generator yielded state for Stage: {current_stage_name}")


            # Add current instruction info (using raw string) to the response data for UI display
            step_data_dict['current_instruction_address'] = f"0x{sim_state['current_instr_addr']:X}"
            step_data_dict['current_instruction_string'] = sim_state['current_instr_str']

            # Print the detailed log entry for this micro-step to the server console
            if 'log_entry' in step_data_dict and step_data_dict['log_entry']:
                 log_lines = step_data_dict['log_entry'].strip().split('\n')
                 print("\n".join(f"    {line.strip()}" for line in log_lines)) # Indent log lines

            # Return the micro-step data and current CPU state
            return jsonify({
                "status": "success",           # Indicates micro-step executed successfully
                "step_data": step_data_dict,   # Data yielded by the generator (state, logs, visuals)
                "cpu_state": format_cpu_state_api(), # Current state of registers/memory
                "enable_next": True          # Allow the user to click "Next Step" again
            })

        except StopIteration as e:
            # --- Instruction Completed ---
            # The generator has finished executing the current instruction
            completed_instr_str = sim_state['current_instr_str']
            completed_instr_addr = sim_state['current_instr_addr']
            print(f"--- Instruction Completed: '{completed_instr_str}' at 0x{completed_instr_addr:X} ---")
            sim_state['instruction_completed_flag'] = True # Set flag for the *next* micro_step request
            sim_state['current_instruction_generator'] = None # Clear the finished generator

            # Get the return value from the generator (should be {'next_pc': val, 'error': msg})
            result = e.value if hasattr(e, 'value') and isinstance(e.value, dict) else {}
            next_pc = result.get('next_pc')
            error_msg = result.get('error') # Check if the instruction itself reported an error

            if next_pc is None and not error_msg:
                 # This indicates an internal issue - generator didn't return the expected dict
                 error_msg = "Internal Simulator Error: Generator finished unexpectedly without returning next_pc."
                 print(f"[ERROR] {error_msg} for instruction at 0x{completed_instr_addr:X}")
                 next_pc = completed_instr_addr # Halt simulation by setting PC back
                 sim_state['simulation_loaded'] = False # Stop

            print(f"  Generator Final Result: next_pc=0x{next_pc:X}, error='{error_msg}'")

            # --- Update PC State ---
            # Update the main PC state only AFTER the instruction completes successfully or with error
            sim_state['pc'] = next_pc

            # --- Handle Execution Errors ---
            if error_msg:
                sim_state['error_state'] = f"Execution Error at 0x{completed_instr_addr:X} ('{completed_instr_str}'): {error_msg}"
                sim_state['simulation_loaded'] = False # Halt simulation on execution error
                print(f"[EXECUTION HALTED] {sim_state['error_state']}")
                return jsonify({
                    "status": "error", # Indicate simulation stopped due to error
                    "message": sim_state['error_state'],
                    "cpu_state": format_cpu_state_api()
                }), 500 # Use HTTP 500 for server-side execution errors

            # --- Prepare for Next Instruction (No Error) ---
            # Check if the *new* PC points to a valid instruction before allowing continuation
            if next_pc not in sim_state['instruction_memory']:
                 sim_state['simulation_loaded'] = False # Stop simulation normally
                 final_message = (f"Program finished normally after instruction at 0x{completed_instr_addr:X}. "
                                  f"Next PC=0x{next_pc:X} is outside the loaded instruction memory.")
                 sim_state['error_state'] = final_message # Store reason for finish
                 print(f"--- Program Finished Normally --- \n  {final_message}")
                 return jsonify({
                     "status": "finished_program", # Specific status for normal end
                     "message": final_message,
                     "cpu_state": format_cpu_state_api()
                 })
            else:
                 # Instruction finished successfully, and the next instruction is valid
                 next_instr_str = sim_state['raw_instruction_memory'].get(next_pc, "(Invalid PC)")
                 print(f"  Ready for next instruction request at PC=0x{next_pc:X}: '{next_instr_str}'")
                 return jsonify({
                     "status": "instruction_completed", # Specific status indicating instr end
                     "message": f"Instruction '{completed_instr_str}' completed successfully. Next PC is 0x{next_pc:X}.",
                     "cpu_state": format_cpu_state_api(),
                     "next_pc": f"0x{next_pc:X}", # Inform UI about the next PC
                     "next_instruction": next_instr_str, # Inform UI about the next instruction string
                     "enable_next": True, # Allow user to step into the next instruction
                 })

    except Exception as e:
        # Catch unexpected errors in the API handler logic itself (not generator errors)
        print(f"[FATAL API ERROR] Unexpected error in /api/micro_step endpoint: {e}")
        traceback.print_exc()
        sim_state['error_state'] = f"Unexpected server error during micro-step processing: {e}"
        sim_state['simulation_loaded'] = False # Halt simulation
        return jsonify({
            "status": "error",
            "message": sim_state['error_state'],
            "cpu_state": format_cpu_state_api()
        }), 500


@app.route('/api/reset', methods=['POST'])
def api_reset_state():
    """ Resets the entire simulation state to its initial default values. """
    print("\n>>> Received /api/reset request <<<")
    initialize_sim_state()
    return jsonify({
        "status": "success",
        "message": "Simulator has been reset to its initial state.",
        "cpu_state": format_cpu_state_api() # Return the clean state
    })

# ==============================================================================
# Main Application Runner
# ==============================================================================
if __name__ == '__main__':
    initialize_sim_state() # Initialize state when the server starts
    print("=================================================")
    print(" Starting ARMv8 Simulator Flask Web Server")
    print(" Access at: http://localhost:5010 (or equivalent)")
    print("=================================================")
    # debug=True enables auto-reloading on code changes and provides interactive debugger in browser on errors
    # threaded=False can sometimes simplify debugging state issues by ensuring single-threaded request handling
    app.run(debug=True, host='0.0.0.0', port=5010, threaded=False)


    