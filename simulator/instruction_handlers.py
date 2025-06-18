
from .alu import ALU
from .datapath_components import sign_extend, branch_target_adder
from .alu_mappings import ALU_OP_MAPPINGS, get_alu_operation


# --- Decode Handlers ---
def decode_nop(parts):
    return {'log': "  Decode: NOP instruction (no operands).", 'read_reg1_addr': None, 'read_reg2_addr': None}

def decode_r_format(parts):
    if len(parts) < 4: raise ValueError("Decode Error: Invalid R-format instruction syntax")
    rd, rn, rm = parts[1], parts[2], parts[3]
    if rm[0] == '#':
        rm = rm.lstrip('#')
        try:
            rm = int(rm)
        except ValueError:
            raise ValueError(f"Decode Error: Invalid immediate value for I-format: '{rm}'")
        return {'log': f"  Decode: R-format (Rd={rd}, Rn={rn}, shamt = {rm}[12b])",
            'rd': rd, 'rn': rn, 'shamt': rm, 'shamt_bit': 12,
            'read_reg1_addr': rn}
    return {'log': f"  Decode: R-format (Rd={rd}, Rn={rn}, Rm={rm}, shamt = {rm})",
            'rd': rd, 'rn': rn, 'rm': rm,
            'read_reg1_addr': rn, 'read_reg2_addr': rm}

def decode_i_format(parts):
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
    if len(parts) < 4: raise ValueError("Decode Error: Invalid D-format LDUR instruction syntax")
    rt, rn, imm_str = parts[1], parts[2], parts[3].lstrip('#')
    try:
        imm_val = int(imm_str)
    except ValueError:
        raise ValueError(f"Decode Error: Invalid immediate value for D-format: '{imm_str}'")
    return {'log': f"  Decode: D-format Load (Rt={rt}, Rn={rn}, Imm={imm_str} [9b])",
            'rt': rt, 'rd': rt, 
            'rn': rn, 'imm_val': imm_val, 'imm_bits': 9,
            'read_reg1_addr': rn, 
            'read_reg2_addr': None}

def decode_d_format_store(parts):
    if len(parts) < 4: raise ValueError("Decode Error: Invalid D-format STUR instruction syntax")
    rt, rn, imm_str = parts[1], parts[2], parts[3].lstrip('#')
    try:
        imm_val = int(imm_str)
    except ValueError:
        raise ValueError(f"Decode Error: Invalid immediate value for D-format: '{imm_str}'")
    return {'log': f"  Decode: D-format Store (Rt={rt}, Rn={rn}, Imm={imm_str} [9b])",
            'rt': rt, 'rn': rn, 'imm_val': imm_val, 'imm_bits': 9,
            'read_reg1_addr': rn, 
            'read_reg2_addr': rt}

def decode_cb_format(parts):
    print(parts)
    if len(parts) < 3: raise ValueError("Decode Error: Invalid CB-format instruction syntax")
    rt, offset_str = parts[1], parts[2]
    try:
        offset_val = int(offset_str)
    except ValueError:
        raise ValueError(f"Decode Error: Invalid branch offset for CB-format: '{offset_str}'")
    return {'log': f"  Decode: CB-format (Rt={rt}, ByteOffset={offset_str} [19b origin])"
            , 'branch_offset_val': offset_val, 'branch_offset_bits': 19,
            'read_reg1_addr': None,
            'read_reg2_addr': rt}

def decode_b_format(parts):
    if len(parts) < 2: raise ValueError("Decode Error: Invalid B-format instruction syntax")
    offset_str = parts[1]
    try:
        offset_val = int(offset_str)
    except ValueError:
        raise ValueError(f"Decode Error: Invalid branch offset for B-format: '{offset_str}'")
    return {'log': f"  Decode: B-format (ByteOffset={offset_str} [26b origin])",
            'branch_offset_val': offset_val, 'branch_offset_bits': 26,
            'read_reg1_addr': None, 'read_reg2_addr': None}

# --- Execute Handlers ---
def execute_alu_op(decoded_info, alu_input1, alu_input2, flags_register=None):
    """Generic ALU operation executor using centralized mapping with flags support"""
    opcode = decoded_info['opcode']
    operation = get_alu_operation(opcode)
    if not operation:
        raise ValueError(f"Execute Error: ALU operation mapping missing for {opcode}")
    
    # ALU trả về result, zero_flag và flags_data
    alu_result, alu_zero_flag, flags_data = ALU.execute(alu_input1, alu_input2, operation)
    
    # Cập nhật flags register nếu có
    if flags_register is not None:
        flags_register.set_flags(
            flags_data['N'], 
            flags_data['Z'], 
            flags_data['C'], 
            flags_data['V']
        )
    
    log_msg = (f"  Execute: ALU Op='{operation}' "
               f"(In1=0x{int(alu_input1):X}, In2=0x{int(alu_input2):X}) -> "
               f"Result=0x{alu_result:X}, Flags=N:{flags_data['N']} Z:{flags_data['Z']} C:{flags_data['C']} V:{flags_data['V']}")
    
    return {'log': log_msg,
            'alu_result': alu_result, 
            'alu_zero_flag': alu_zero_flag,
            'flags_data': flags_data}

def execute_r_type(decoded_info, controls, read_data1, read_data2, sign_ext_imm, current_pc, flags_register=None):
    return execute_alu_op(decoded_info, read_data1, read_data2, flags_register)

def execute_i_type(decoded_info, controls, read_data1, read_data2, sign_ext_imm, current_pc, flags_register=None):
    return execute_alu_op(decoded_info, read_data1, sign_ext_imm, flags_register)

def execute_d_type(decoded_info, controls, read_data1, read_data2, sign_ext_imm, current_pc, flags_register=None):
    return execute_alu_op(decoded_info, read_data1, sign_ext_imm, flags_register)

def execute_cb_type(decoded_info, controls, read_data1, read_data2, sign_ext_imm, current_pc, flags_register=None):
    rt_reg_name = decoded_info.get('rt', 'N/A')
    offset_val_in = decoded_info.get('branch_offset_val', 0) 
    offset_bits = decoded_info.get('branch_offset_bits', 0) 

    execute_log = f"  Execute: CBZ checking {rt_reg_name}=0x{read_data2:X}.\n"
    
    # Sử dụng ALU với flags support
    _, alu_zero_flag, flags_data = ALU.execute(0, read_data2, 'pass1')
    execute_log += f"  Execute: ALU Zero Flag = {alu_zero_flag}, All Flags = N:{flags_data['N']} Z:{flags_data['Z']} C:{flags_data['C']} V:{flags_data['V']}.\n"

    # Cập nhật flags nếu có flags_register
    if flags_register is not None:
        flags_register.set_flags(flags_data['N'], flags_data['Z'], flags_data['C'], flags_data['V'])

    branch_offset_extended = sign_extend(offset_val_in, offset_bits)
    execute_log += f"  Execute: Sign-extended branch offset = {branch_offset_extended} (0x{branch_offset_extended:X})\n"
    
    branch_target_addr = branch_target_adder(current_pc, branch_offset_extended)
    execute_log += f"  Execute: Branch Target Address (PC + Offset) = 0x{branch_target_addr:X}"
    
    return {'log': execute_log,
            'alu_result': read_data2,
            'alu_zero_flag': alu_zero_flag,
            'flags_data': flags_data,
            'branch_target_addr': branch_target_addr}

def execute_b_type(decoded_info, controls, read_data1, read_data2, sign_ext_imm, current_pc, flags_register=None):
    execute_log = "  Execute: B instruction - ALU not used.\n"
    branch_offset_extended = sign_extend(decoded_info['branch_offset_val'], decoded_info['branch_offset_bits'])
    branch_target_addr = branch_target_adder(current_pc, branch_offset_extended)
    execute_log += f"  Execute: Calculate Branch Target: PC(0x{current_pc:X}) + Offset({branch_offset_extended}) = 0x{branch_target_addr:X}"

    return {'log': execute_log,
            'alu_result': 0, 
            'alu_zero_flag': 0,
            'flags_data': {'N': 0, 'Z': 0, 'C': 0, 'V': 0},  # No flags change for branch
            'branch_target_addr': branch_target_addr}

def execute_nop(decoded_info, controls, read_data1, read_data2, sign_ext_imm, current_pc, flags_register=None):
     return {'log': "  Execute: NOP - No operation performed.", 
             'alu_result': 0, 
             'alu_zero_flag': 0,
             'flags_data': {'N': 0, 'Z': 0, 'C': 0, 'V': 0}}

def execute_mul(decoded_info, controls, read_data1, read_data2, sign_ext_imm, current_pc, flags_register=None):
    """Executes MUL (R-format multiplication). Shared with execute_r_type logic."""
    return execute_r_type(decoded_info, controls, read_data1, read_data2, sign_ext_imm, current_pc, flags_register)

def execute_div(decoded_info, controls, read_data1, read_data2, sign_ext_imm, current_pc, flags_register=None):
    """Executes DIV (R-format division). Shared with execute_r_type logic but handles exception."""
    try:
        return execute_r_type(decoded_info, controls, read_data1, read_data2, sign_ext_imm, current_pc, flags_register)
    except ValueError as e: # Catch division by zero from ALU
         log_msg = (f"  Execute: ALU Op='div' "
                    f"(Dividend=0x{int(read_data1):X}, Divisor=0x{int(read_data2):X}) -> "
                    f"ERROR: {e}")
         raise ValueError(log_msg) from e # Re-raise to halt simulation

# --- Memory Handlers ---
# Input: decoded_info, controls, alu_result (memory address), read_data2 (data for store), data_memory_object
def memory_noop(decoded_info, controls, alu_result, read_data2, data_memory_obj):
    return {'log': "  Memory: No memory operation required.", 'data_read_from_mem': None}

def memory_read(decoded_info, controls, alu_result, read_data2, data_memory_obj):
    mem_address = alu_result
    try:
        data = data_memory_obj.read(mem_address)
        log_msg = f"  Memory Read: Accessing Addr=0x{mem_address:X} -> Read Data=0x{data:X}"
        return {'log': log_msg, 'data_read_from_mem': data}
    except Exception as e:
        raise ValueError(f"Memory Stage Error during read at 0x{mem_address:X}: {e}")

def memory_write(decoded_info, controls, alu_result, read_data2, data_memory_obj):
    mem_address = alu_result
    data_to_write = read_data2
    rt_reg_name = decoded_info.get('rt', 'N/A')
    try:
        data_memory_obj.write(mem_address, data_to_write)
        log_msg = (f"  Memory Write: Accessing Addr=0x{mem_address:X}, Writing Data=0x{data_to_write:X} "
                   f"(from reg {rt_reg_name}) -> Write successful.")
        return {'log': log_msg, 'data_read_from_mem': None} # No data read during write
    except Exception as e:
        raise ValueError(f"Memory Stage Error during write at 0x{mem_address:X}: {e}")

# --- Write Back Handlers (for logging) ---
# Input: decoded_info, controls, alu_result, data_read_from_mem
def writeback_alu_result(decoded_info, controls, alu_result, data_read_from_mem):
    dest_reg = decoded_info.get('rd')
    if controls.get('RegWrite') == 1 and dest_reg:
        return {'log': f"  Write Back: Intending to write ALU Result (0x{alu_result:X}) to {dest_reg}."}
    else:
        return {'log': "  Write Back: No register write intended or RegWrite=0."}

def writeback_mem_data(decoded_info, controls, alu_result, data_read_from_mem):
    dest_reg = decoded_info.get('rt')
    if controls.get('RegWrite') == 1 and dest_reg and data_read_from_mem is not None:
        return {'log': f"  Write Back: Intending to write Memory Data (0x{data_read_from_mem:X}) to {dest_reg}."}
    elif controls.get('RegWrite') == 1 and dest_reg:
         return {'log': f"  Write Back: RegWrite=1 for {dest_reg} but no data was read from memory."}
    else:
        return {'log': "  Write Back: No register write intended or RegWrite=0."}

def writeback_noop(decoded_info, controls, alu_result, data_read_from_mem):
    return {'log': "  Write Back: No register write performed by this instruction."}


# --- Instruction Handler Dispatch Table ---
INSTRUCTION_HANDLERS = {
    'ADD':  {'decode': decode_r_format,      'execute': execute_r_type,   'memory': memory_noop,   'writeback': writeback_alu_result},
    'ADDS':  {'decode': decode_r_format,      'execute': execute_r_type,   'memory': memory_noop,   'writeback': writeback_alu_result, 'setflag': True},
    'SUB':  {'decode': decode_r_format,      'execute': execute_r_type,   'memory': memory_noop,   'writeback': writeback_alu_result},
    'SUBS':  {'decode': decode_r_format,      'execute': execute_r_type,   'memory': memory_noop,   'writeback': writeback_alu_result, 'setflag': True},
    'AND':  {'decode': decode_r_format,      'execute': execute_r_type,   'memory': memory_noop,   'writeback': writeback_alu_result},
    'ANDS':  {'decode': decode_r_format,      'execute': execute_r_type,   'memory': memory_noop,   'writeback': writeback_alu_result, 'setflag': True},
    'ORR':  {'decode': decode_r_format,      'execute': execute_r_type,   'memory': memory_noop,   'writeback': writeback_alu_result},
    'EOR':  {'decode': decode_r_format,      'execute': execute_r_type,   'memory': memory_noop,   'writeback': writeback_alu_result},
    #'MUL':  {'decode': decode_r_format,      'execute': execute_r_type,   'memory': memory_noop,   'writeback': writeback_alu_result},
    #'DIV':  {'decode': decode_r_format,      'execute': execute_r_type,   'memory': memory_noop,   'writeback': writeback_alu_result},
    'LSL':  {'decode': decode_r_format,      'execute': execute_r_type,   'memory': memory_noop,   'writeback': writeback_alu_result},
    'LSR':  {'decode': decode_r_format,      'execute': execute_r_type,   'memory': memory_noop,   'writeback': writeback_alu_result},
    
    'ADDI': {'decode': decode_i_format,      'execute': execute_i_type,   'memory': memory_noop,   'writeback': writeback_alu_result},
    'SUBI': {'decode': decode_i_format,      'execute': execute_i_type,   'memory': memory_noop,   'writeback': writeback_alu_result},
    'ANDI': {'decode': decode_i_format,      'execute': execute_i_type,   'memory': memory_noop,   'writeback': writeback_alu_result},
    'ORRI': {'decode': decode_i_format,      'execute': execute_i_type,   'memory': memory_noop,   'writeback': writeback_alu_result},
    'EORI': {'decode': decode_i_format,      'execute': execute_i_type,   'memory': memory_noop,   'writeback': writeback_alu_result},
    
    'LDUR': {'decode': decode_d_format_load, 'execute': execute_d_type,   'memory': memory_read,   'writeback': writeback_mem_data},
    'STUR': {'decode': decode_d_format_store,'execute': execute_d_type,   'memory': memory_write,  'writeback': writeback_noop},
    
    'CBZ':  {'decode': decode_cb_format,     'execute': execute_cb_type,  'memory': memory_noop,   'writeback': writeback_noop},
    # 'B.EQ':  {'decode': decode_cb_format,     'execute': execute_cb_type,  'memory': memory_noop,   'writeback': writeback_noop},
    'CBNZ':  {'decode': decode_cb_format,     'execute': execute_cb_type,  'memory': memory_noop,   'writeback': writeback_noop},
    'B':    {'decode': decode_b_format,      'execute': execute_b_type,   'memory': memory_noop,   'writeback': writeback_noop},
    'B.EQ':    {'decode': decode_b_format,      'execute': execute_b_type,   'memory': memory_noop,   'writeback': writeback_noop},
    'B.NE':    {'decode': decode_b_format,      'execute': execute_b_type,   'memory': memory_noop,   'writeback': writeback_noop},
    'B.LT':    {'decode': decode_b_format,      'execute': execute_b_type,   'memory': memory_noop,   'writeback': writeback_noop},
    'B.LO':    {'decode': decode_b_format,      'execute': execute_b_type,   'memory': memory_noop,   'writeback': writeback_noop},
    'B.LE':    {'decode': decode_b_format,      'execute': execute_b_type,   'memory': memory_noop,   'writeback': writeback_noop},
    'B.LS':    {'decode': decode_b_format,      'execute': execute_b_type,   'memory': memory_noop,   'writeback': writeback_noop},
    # 'NOP':  {'decode': decode_nop,           'execute': execute_nop,      'memory': memory_noop,   'writeback': writeback_noop},
}