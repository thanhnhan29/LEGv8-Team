# LEGv8 Instruction Encoding
# Based on information from "Bai05_Kien truc LEGv8.pdf", page 19 (PDF page 21)

OPCODES = {
    # R-type (opcode: 11 bits [31-21])
    "ADD":  "10001011000", # Example
    "SUB":  "11001011000", # Example
    "AND":  "10001010000", # Example
    "ORR":  "10101010000", # Example
    "LSL":  "11010011010", # Example (shamt is used)
    "LSR":  "11010011011", # Example (shamt is used)
    # I-type (opcode: 10 bits [31-22])
    "ADDI": "1001000100",  # Example
    "SUBI": "1101000100",  # Example
    # D-type (opcode: 11 bits [31-21])
    "LDUR": "11111000010", # Example
    "STUR": "11111000000", # Example
    # B-type (opcode: 6 bits [31-26])
    "B":    "000101",      # Example
    # CB-type (opcode: 8 bits [31-24])
    "CBZ":  "10110100",    # Example
    "CBNZ": "10110101",    # Example
    # IW-type (opcode: 11 bits [31-21])
    "MOVZ": "11010010101", # Base 11-bit opcode for MOVZ
    "MOVK": "11110010101", # Base 11-bit opcode for MOVK
}

# For decoding: map binary opcode to name and type, and define field extraction
OPCODE_FIELDS_FOR_DECODING = [
    # Order is important: check more specific/longer opcodes first if ambiguity could arise.
    # For LEGv8, distinct bit positions for opcode fields usually prevent this.
    # Check 11-bit opcodes (R, D, IW)
    {'type_hint': 'R',    'op_range': (31, 21), 'length': 11, 'decoder': 'decode_r_fields_and_meaning'},
    {'type_hint': 'D',    'op_range': (31, 21), 'length': 11, 'decoder': 'decode_d_fields_and_meaning'},
    {'type_hint': 'IW',   'op_range': (31, 21), 'length': 11, 'decoder': 'decode_iw_fields_and_meaning'},
    # Then 10-bit (I)
    {'type_hint': 'I',    'op_range': (31, 22), 'length': 10, 'decoder': 'decode_i_fields_and_meaning'},
    # Then 8-bit (CB)
    {'type_hint': 'CB',   'op_range': (31, 24), 'length': 8,  'decoder': 'decode_cb_fields_and_meaning'},
    # Then 6-bit (B)
    {'type_hint': 'B',    'op_range': (31, 26), 'length': 6,  'decoder': 'decode_b_fields_and_meaning'},
]

REVERSE_OPCODES = {}
for name, binary_str in OPCODES.items():
    instr_type = None
    if name in ["ADD", "SUB", "AND", "ORR", "LSL", "LSR"]: instr_type = "R"
    elif name in ["ADDI", "SUBI"]: instr_type = "I"
    elif name in ["LDUR", "STUR"]: instr_type = "D"
    elif name == "B": instr_type = "B"
    elif name in ["CBZ", "CBNZ"]: instr_type = "CB"
    elif name in ["MOVZ", "MOVK"]: instr_type = "IW"
    if instr_type:
        REVERSE_OPCODES[binary_str] = {"name": name, "type": instr_type}

# --- Helper Functions ---
def reg_to_bin(reg_str, num_bits=5):
    """Converts register string (e.g., 'X0', 'XZR') to binary string."""
    if reg_str.upper() == "XZR":
        return format(31, f'0{num_bits}b')
    try:
        reg_num = int(reg_str[1:])
        if not (0 <= reg_num <= 30): # Standard registers X0-X30
            raise ValueError(f"Invalid register number: {reg_num}")
        return format(reg_num, f'0{num_bits}b')
    except Exception as e:
        raise ValueError(f"Invalid register format '{reg_str}': {e}")

def imm_to_bin(imm_str, num_bits, signed=False):
    """Converts immediate string (e.g., '#10') to binary string."""
    try:
        val = int(imm_str.replace('#', ''))
    except ValueError:
        raise ValueError(f"Invalid immediate value: {imm_str}")

    if signed:
        min_val = -(1 << (num_bits - 1))
        max_val = (1 << (num_bits - 1)) - 1
        if not (min_val <= val <= max_val):
            raise ValueError(f"Signed immediate {val} out of range for {num_bits} bits ({min_val} to {max_val}).")
        if val < 0:
            val = (1 << num_bits) + val # Convert to two's complement
        return format(val, f'0{num_bits}b')
    else:
        max_val = (1 << num_bits) - 1
        if not (0 <= val <= max_val):
            raise ValueError(f"Unsigned immediate {val} out of range for {num_bits} bits (0 to {max_val}).")
        return format(val, f'0{num_bits}b')

# --- Encoding Functions ---

def encode_r_type(op_name, rd_str, rn_str, rm_str, shamt_str="0"):
    """Encodes R-type instruction."""
    # Layout: opcode(11) | Rm(5) | shamt(6) | Rn(5) | Rd(5)
    if op_name not in OPCODES:
        raise ValueError(f"Unknown R-type opcode: {op_name}")
    opcode_bin = OPCODES[op_name]
    if len(opcode_bin) != 11: # Double check based on R-type format
        raise ValueError(f"Opcode for {op_name} is not 11 bits for R-type.")

    rd_bin = reg_to_bin(rd_str, 5)
    rn_bin = reg_to_bin(rn_str, 5)
    rm_bin = reg_to_bin(rm_str, 5)
    shamt_bin = imm_to_bin(shamt_str, 6, signed=False) # shamt is unsigned

    return f"{opcode_bin}{rm_bin}{shamt_bin}{rn_bin}{rd_bin}"

def encode_i_type(op_name, rd_str, rn_str, imm_val_str):
    """Encodes I-type instruction."""
    # Layout: opcode(10) | ALU_immediate(12) | Rn(5) | Rd(5)
    if op_name not in OPCODES:
        raise ValueError(f"Unknown I-type opcode: {op_name}")
    opcode_bin = OPCODES[op_name]
    if len(opcode_bin) != 10: # Double check based on I-type format
         raise ValueError(f"Opcode for {op_name} is not 10 bits for I-type.")

    rd_bin = reg_to_bin(rd_str, 5)
    rn_bin = reg_to_bin(rn_str, 5)
    # ALU_immediate is 12 bits, signed or unsigned depends on specific I-type instruction
    # For ADDI/SUBI, it's typically signed.
    alu_imm_bin = imm_to_bin(imm_val_str, 12, signed=True)

    return f"{opcode_bin}{alu_imm_bin}{rn_bin}{rd_bin}"

def encode_d_type(op_name, rt_str, rn_str, dt_addr_str, op_val_str="0"):
    """Encodes D-type instruction."""
    # Layout: opcode(11) | DT_address(9) | op(2) | Rn(5) | Rt(5)
    if op_name not in OPCODES:
        raise ValueError(f"Unknown D-type opcode: {op_name}")
    opcode_bin = OPCODES[op_name]
    if len(opcode_bin) != 11: # Double check based on D-type format
        raise ValueError(f"Opcode for {op_name} is not 11 bits for D-type.")

    rt_bin = reg_to_bin(rt_str, 5) # Rt is destination for load, source for store
    rn_bin = reg_to_bin(rn_str, 5) # Base address register
    dt_address_bin = imm_to_bin(dt_addr_str, 9, signed=False) # DT_address is unsigned offset
    
    # op field (2 bits)
    op_val = int(op_val_str)
    if not (0 <= op_val <= 3):
        raise ValueError(f"Invalid 'op' field value for D-type: {op_val}. Must be 0-3.")
    op_bin = format(op_val, '02b')

    return f"{opcode_bin}{dt_address_bin}{op_bin}{rn_bin}{rt_bin}"

def encode_b_type(op_name, br_addr_str, current_address=0, labels=None):
    """Encodes B-type instruction."""
    # Layout: opcode(6) | BR_address(26)
    if labels is None:
        labels = {}
    if op_name not in OPCODES:
        raise ValueError(f"Unknown B-type opcode: {op_name}")
    opcode_bin = OPCODES[op_name]
    if len(opcode_bin) != 6: # Double check based on B-type format
        raise ValueError(f"Opcode for {op_name} is not 6 bits for B-type.")

    offset_val = 0
    try:
        # Try direct numerical offset (PC-relative, in words)
        offset_val = int(br_addr_str.replace('#', ''))
    except ValueError:
        # Assume it's a label
        if br_addr_str in labels:
            target_addr = labels[br_addr_str]
            offset_val = (target_addr - current_address) // 4 # PC-relative offset in words
        else:
            raise ValueError(f"Label '{br_addr_str}' not found for B-type instruction.")
    
    br_address_bin = imm_to_bin(str(offset_val), 26, signed=True)
    return f"{opcode_bin}{br_address_bin}"

def encode_cb_type(op_name, rt_str, cond_br_addr_str, current_address=0, labels=None):
    """Encodes CB-type instruction."""
    # Layout: opcode(8) | COND_BR_address(19) | Rt(5)
    if labels is None:
        labels = {}
    if op_name not in OPCODES:
        raise ValueError(f"Unknown CB-type opcode: {op_name}")
    opcode_bin = OPCODES[op_name]
    if len(opcode_bin) != 8: # Double check based on CB-type format
        raise ValueError(f"Opcode for {op_name} is not 8 bits for CB-type.")

    rt_bin = reg_to_bin(rt_str, 5)
    offset_val = 0
    try:
        offset_val = int(cond_br_addr_str.replace('#', ''))
    except ValueError:
        if cond_br_addr_str in labels:
            target_addr = labels[cond_br_addr_str]
            offset_val = (target_addr - current_address) // 4
        else:
            raise ValueError(f"Label '{cond_br_addr_str}' not found for CB-type instruction.")
            
    cond_br_address_bin = imm_to_bin(str(offset_val), 19, signed=True)
    return f"{opcode_bin}{cond_br_address_bin}{rt_bin}"

def encode_iw_type(op_name, rd_str, mov_imm_str, shift_op_str):
    """Encodes IW-type instruction (MOVZ, MOVK).
    Layout based on PDF: opcode(11) [31-21] | op(2) [20-19] | MOV_immediate(16) [18-3] | Rd(3) [2-0]
    """
    if op_name not in ["MOVZ", "MOVK"]: # Check against base names
        raise ValueError(f"Unknown IW-type opcode base name: {op_name}")

    if op_name not in OPCODES:
        raise ValueError(f"11-bit Opcode for IW-type {op_name} not defined in OPCODES.")
    eleven_bit_opcode = OPCODES[op_name] # This is the 11-bit opcode for MOVZ/MOVK

    # Determine 'op' (hw) field [20-19] from LSL amount
    shift_val = int(shift_op_str.replace('#','').replace('LSL','').strip())
    op_bin = "" # hw field
    if shift_val == 0:   op_bin = "00"
    elif shift_val == 16: op_bin = "01"
    elif shift_val == 32: op_bin = "10" # For 64-bit
    elif shift_val == 48: op_bin = "11" # For 64-bit
    else:
        raise ValueError(f"Invalid LSL shift amount for {op_name}: {shift_val}. Must be 0, 16, 32, or 48.")

    # Rd field: 3 bits [2-0] as per PDF IW-format diagram.
    rd_iw_bin = reg_to_bin(rd_str, 3) # Limits Rd to X0-X7

    # MOV_immediate is 16 bits unsigned [18-3]
    mov_imm_bin = imm_to_bin(mov_imm_str, 16, signed=False)

    return f"{eleven_bit_opcode}{op_bin}{mov_imm_bin}{rd_iw_bin}"


# --- Bit Extraction Helper ---
def get_bits(instruction_int, high, low):
    """Extracts bits from low to high (inclusive) from instruction_int."""
    mask = (1 << (high - low + 1)) - 1
    return (instruction_int >> low) & mask

# --- Field Decoding and Meaning Functions ---
def decode_r_fields_and_meaning(instruction_int):
    # Layout: opcode(11) [31-21] | Rm(5) [20-16] | shamt(6) [15-10] | Rn(5) [9-5] | Rd(5) [4-0]
    opcode = get_bits(instruction_int, 31, 21)
    rm = get_bits(instruction_int, 20, 16)
    shamt = get_bits(instruction_int, 15, 10)
    rn = get_bits(instruction_int, 9, 5)
    rd = get_bits(instruction_int, 4, 0)

    log_str = (f"  Decode: R-type (Opcode={opcode:011b} ({opcode}), Rm=X{rm}, "
               f"shamt={shamt}, Rn=X{rn}, Rd=X{rd})")
    
    fields = {
        'opcode': {'val': opcode, 'bin': f"{opcode:011b}", 'bits': '[31-21]', 'meaning': "Specific R-type operation. To Control Unit."},
        'rm': {'val': rm, 'bin': f"{rm:05b}", 'bits': '[20-16]', 'meaning': f"Second source register (X{rm}). To RegFile read port 2."},
        'shamt': {'val': shamt, 'bin': f"{shamt:06b}", 'bits': '[15-10]', 'meaning': f"Shift amount ({shamt}). To ALU shifter."},
        'rn': {'val': rn, 'bin': f"{rn:05b}", 'bits': '[9-5]', 'meaning': f"First source register (X{rn}). To RegFile read port 1."},
        'rd': {'val': rd, 'bin': f"{rd:05b}", 'bits': '[4-0]', 'meaning': f"Destination register (X{rd}). To RegFile write port."}
    }
    reg_ops = {
        'read1_addr': f"X{rn}" if rn != 31 else "XZR",
        'read2_addr': f"X{rm}" if rm != 31 else "XZR",
        'write_addr': f"X{rd}" if rd != 31 else "XZR"
    }
    if rd == 31: # Writing to XZR is a no-op, but address is still XZR
        reg_ops['write_addr'] = "XZR"
    return {'type': 'R', 'log': log_str, 'fields': fields, 'reg_ops': reg_ops}

def decode_i_fields_and_meaning(instruction_int):
    # Layout: opcode(10) [31-22] | ALU_immediate(12) [21-10] | Rn(5) [9-5] | Rd(5) [4-0]
    opcode = get_bits(instruction_int, 31, 22)
    alu_immediate_raw = get_bits(instruction_int, 21, 10)
    rn = get_bits(instruction_int, 9, 5)
    rd = get_bits(instruction_int, 4, 0)

    signed_alu_imm = alu_immediate_raw
    if (alu_immediate_raw >> 11) & 1: # Check sign bit (MSB of 12-bit immediate)
        signed_alu_imm = alu_immediate_raw - (1 << 12)

    log_str = (f"  Decode: I-type (Opcode={opcode:010b} ({opcode}), Rn=X{rn}, Rd=X{rd}, "
               f"Imm_s={signed_alu_imm} [raw={alu_immediate_raw:012b}])")
    
    fields = {
        'opcode': {'val': opcode, 'bin': f"{opcode:010b}", 'bits': '[31-22]', 'meaning': "Specific I-type operation. To Control Unit."},
        'alu_immediate': {'val_raw': alu_immediate_raw, 'val_signed': signed_alu_imm, 'bin': f"{alu_immediate_raw:012b}", 'bits': '[21-10]', 'meaning': f"Immediate value ({signed_alu_imm}), sign-extended. To ALU."},
        'rn': {'val': rn, 'bin': f"{rn:05b}", 'bits': '[9-5]', 'meaning': f"Source register (X{rn}). To RegFile read port 1."},
        'rd': {'val': rd, 'bin': f"{rd:05b}", 'bits': '[4-0]', 'meaning': f"Destination register (X{rd}). To RegFile write port."}
    }
    reg_ops = {
        'read1_addr': f"X{rn}" if rn != 31 else "XZR",
        'write_addr': f"X{rd}" if rd != 31 else "XZR"
    }
    if rd == 31:
        reg_ops['write_addr'] = "XZR"
    return {'type': 'I', 'log': log_str, 'fields': fields, 'reg_ops': reg_ops, 'imm_val': signed_alu_imm, 'imm_bits': 12}

def decode_d_fields_and_meaning(instruction_int):
    # Layout: opcode(11) [31-21] | DT_address(9) [20-12] | op(2) [11-10] | Rn(5) [9-5] | Rt(5) [4-0]
    opcode = get_bits(instruction_int, 31, 21)
    dt_address = get_bits(instruction_int, 20, 12)
    op2 = get_bits(instruction_int, 11, 10)
    rn = get_bits(instruction_int, 9, 5)
    rt = get_bits(instruction_int, 4, 0)

    # Determine if it's a load or store based on common LEGv8 opcodes (example)
    # LDUR: 11111000010 (0x7C2), STUR: 11111000000 (0x7C0)
    op_type_str = "D-type (Unknown)"
    read_reg2_addr = None
    write_addr = None
    is_load = (opcode == OPCODES["LDUR"]) # Compare with binary string from OPCODES
    is_store = (opcode == OPCODES["STUR"])

    if is_load:
        op_type_str = "D-type Load (LDUR)"
    elif is_store:
        op_type_str = "D-type Store (STUR)"


    log_str = (f"  Decode: {op_type_str} (Opcode={opcode:011b}, DT_addr={dt_address}, "
               f"op2={op2:02b}, Rn=X{rn}, Rt=X{rt})")
    
    fields = {
        'opcode': {'val': opcode, 'bin': f"{opcode:011b}", 'bits': '[31-21]', 'meaning': "Identifies LDUR/STUR. To Control Unit."},
        'dt_address': {'val': dt_address, 'bin': f"{dt_address:09b}", 'bits': '[20-12]', 'meaning': f"Memory offset ({dt_address}). To ALU for address calculation."},
        'op2': {'val': op2, 'bin': f"{op2:02b}", 'bits': '[11-10]', 'meaning': f"Operation specifier ({op2})."}, # Often unused (00) for LDUR/STUR
        'rn': {'val': rn, 'bin': f"{rn:05b}", 'bits': '[9-5]', 'meaning': f"Base address register (X{rn}). To RegFile read port 1."},
        'rt': {'val': rt, 'bin': f"{rt:05b}", 'bits': '[4-0]', 'meaning': f"Target register (X{rt}). For LDUR: dest. For STUR: source."}
    }
    
    reg_ops = {'read1_addr': f"X{rn}" if rn != 31 else "XZR"}
    rt_str = f"X{rt}" if rt != 31 else "XZR"

    if is_load: # LDUR: Rt is destination
        reg_ops['write_addr'] = rt_str
        if rt == 31: reg_ops['write_addr'] = "XZR"
    elif is_store: # STUR: Rt is source
        reg_ops['read2_addr'] = rt_str # Rt is the second source register to read for store
        
    return {'type': 'D', 'log': log_str, 'fields': fields, 'reg_ops': reg_ops, 'imm_val': dt_address, 'imm_bits': 9, 'rt_val': rt}


def decode_b_fields_and_meaning(instruction_int, current_address):
    # Layout: opcode(6) [31-26] | BR_address(26) [25-0]
    opcode = get_bits(instruction_int, 31, 26)
    br_address_offset_raw = get_bits(instruction_int, 25, 0)

    signed_offset = br_address_offset_raw
    if (br_address_offset_raw >> 25) & 1: # Check sign bit
        signed_offset = br_address_offset_raw - (1 << 26)
    
    target_address = current_address + (signed_offset * 4)

    log_str = (f"  Decode: B-type (Opcode={opcode:06b}, Offset_words={signed_offset}, "
               f"Target=0x{target_address:X} from PC=0x{current_address:X})")
    
    fields = {
        'opcode': {'val': opcode, 'bin': f"{opcode:06b}", 'bits': '[31-26]', 'meaning': "Unconditional branch. To Control Unit."},
        'br_address_offset': {'val_raw': br_address_offset_raw, 'val_signed_words': signed_offset, 'bin': f"{br_address_offset_raw:026b}", 'bits': '[25-0]', 'meaning': f"PC-relative offset in words ({signed_offset})."}
    }
    calculated = {'target_address':  f"0x{target_address:X}"}
    return {'type': 'B', 'log': log_str, 'fields': fields, 'reg_ops': {}, 'calculated': calculated} # No explicit reg_ops for B

def decode_cb_fields_and_meaning(instruction_int, current_address):
    # Layout: opcode(8) [31-24] | COND_BR_address(19) [23-5] | Rt(5) [4-0]
    opcode = get_bits(instruction_int, 31, 24)
    cond_br_address_offset_raw = get_bits(instruction_int, 23, 5)
    rt = get_bits(instruction_int, 4, 0)

    signed_offset = cond_br_address_offset_raw
    if (cond_br_address_offset_raw >> 18) & 1: # Check sign bit
        signed_offset = cond_br_address_offset_raw - (1 << 19)

    target_address = current_address + (signed_offset * 4)

    log_str = (f"  Decode: CB-type (Opcode={opcode:08b}, Rt=X{rt}, Offset_words={signed_offset}, "
               f"Target=0x{target_address:X} from PC=0x{current_address:X})")
    
    fields = {
        'opcode': {'val': opcode, 'bin': f"{opcode:08b}", 'bits': '[31-24]', 'meaning': "Conditional branch (CBZ/CBNZ). To Control Unit."},
        'cond_br_address_offset': {'val_raw': cond_br_address_offset_raw, 'val_signed_words': signed_offset, 'bin': f"{cond_br_address_offset_raw:019b}", 'bits': '[23-5]', 'meaning': f"PC-relative offset in words ({signed_offset})."},
        'rt': {'val': rt, 'bin': f"{rt:05b}", 'bits': '[4-0]', 'meaning': f"Register to test (X{rt}). To RegFile read port 1."}
    }
    reg_ops = {'read1_addr': f"X{rt}" if rt != 31 else "XZR"} # Register to be tested
    calculated = {'target_address': f"0x{target_address:X}"}
    return {'type': 'CB', 'log': log_str, 'fields': fields, 'reg_ops': reg_ops, 'calculated': calculated}

def decode_iw_fields_and_meaning(instruction_int):
    # Layout: opcode(11) [31-21] | op(2) [20-19] | MOV_immediate(16) [18-3] | Rd(3) [2-0]
    opcode = get_bits(instruction_int, 31, 21)
    op_hw = get_bits(instruction_int, 20, 19) # hw field
    mov_immediate = get_bits(instruction_int, 18, 3)
    rd_iw = get_bits(instruction_int, 2, 0) # Rd is 3 bits for IW as per PDF

    lsl_amount = 0
    if op_hw == 0b00: lsl_amount = 0
    elif op_hw == 0b01: lsl_amount = 16
    elif op_hw == 0b10: lsl_amount = 32
    elif op_hw == 0b11: lsl_amount = 48
    
    shifted_imm_val = mov_immediate << lsl_amount

    log_str = (f"  Decode: IW-type (Opcode={opcode:011b}, hw={op_hw:02b} (LSL{lsl_amount}), "
               f"Rd_iw=X{rd_iw}, Imm16={mov_immediate}) -> Effective=0x{shifted_imm_val:016X}")
    
    fields = {
        'opcode': {'val': opcode, 'bin': f"{opcode:011b}", 'bits': '[31-21]', 'meaning': "Identifies MOVZ/MOVK. To Control Unit."},
        'op_hw': {'val': op_hw, 'bin': f"{op_hw:02b}", 'bits': '[20-19]', 'meaning': f"LSL amount specifier (LSL #{lsl_amount})."},
        'mov_immediate': {'val': mov_immediate, 'bin': f"{mov_immediate:016b}", 'bits': '[18-3]', 'meaning': f"16-bit immediate value ({mov_immediate})."},
        'rd_iw': {'val': rd_iw, 'bin': f"{rd_iw:03b}", 'bits': '[2-0]', 'meaning': f"Destination register (X{rd_iw}, IW-specific 3-bit). To RegFile write port."}
    }
    # rd_iw is 0-7, so f"X{rd_iw}" is appropriate. XZR (31) is not representable in 3 bits.
    reg_ops = {'write_addr': f"X{rd_iw}"} 
    calculated = {'shifted_immediate_value': f"0x{shifted_imm_val:016X}"}
    return {'type': 'IW', 'log': log_str, 'fields': fields, 'reg_ops': reg_ops, 'calculated': calculated}

# Dynamically get decoder functions by name
DECODER_FUNCTIONS_MAP = {
    'decode_r_fields_and_meaning': decode_r_fields_and_meaning,
    'decode_i_fields_and_meaning': decode_i_fields_and_meaning,
    'decode_d_fields_and_meaning': decode_d_fields_and_meaning,
    'decode_b_fields_and_meaning': decode_b_fields_and_meaning,
    'decode_cb_fields_and_meaning': decode_cb_fields_and_meaning,
    'decode_iw_fields_and_meaning': decode_iw_fields_and_meaning,
}

def decode_binary_instruction_and_get_meaning(instruction_int, current_address=0):
    """
    Decodes a 32-bit integer instruction and returns its structured meaning.
    """
    for op_field_info in OPCODE_FIELDS_FOR_DECODING:
        high, low = op_field_info['op_range']
        length = op_field_info['length']
        
        extracted_op_val = get_bits(instruction_int, high, low)
        extracted_op_bin = format(extracted_op_val, f'0{length}b')

        if extracted_op_bin in REVERSE_OPCODES:
            op_details = REVERSE_OPCODES[extracted_op_bin]
            
            if op_details["type"] == op_field_info["type_hint"]:
                decoder_func_name = op_field_info["decoder"]
                decoder_func = DECODER_FUNCTIONS_MAP.get(decoder_func_name)

                if not decoder_func:
                    raise ValueError(f"Decoder function {decoder_func_name} not found in map.")

                decoded_data = None
                if op_details["type"] in ["B", "CB"]: # These decoders need current_address
                    decoded_data = decoder_func(instruction_int, current_address)
                else:
                    decoded_data = decoder_func(instruction_int)
                
                if decoded_data:
                    decoded_data['opcode_name'] = op_details["name"] # Add symbolic name
                    # Ensure standard fields exist for simulator compatibility
                    decoded_data.setdefault('reg_ops', {})
                    decoded_data.setdefault('fields', {})
                    decoded_data.setdefault('calculated', {})
                    decoded_data.setdefault('imm_val', None)
                    decoded_data.setdefault('imm_bits', 0)
                    return decoded_data
    
    if instruction_int == 0: # NOP (all zeros)
        return {
            'type': 'NOP_ZERO', 
            'log': "  Decode: NOP (all zeros instruction)", 
            'fields': {'instruction': {'val': 0, 'bin': '0'*32, 'bits': '[31-0]', 'meaning': "NOP (all zeros)"}},
            'opcode_name': 'NOP', # Use 'NOP' as a common name for control unit
            'reg_ops': {}, 'calculated': {}, 'imm_val': None, 'imm_bits': 0
        }

    raise ValueError(f"Unknown or unsupported instruction binary pattern: {instruction_int:032b} (int: {instruction_int})")

def parse_and_encode(instruction_str, current_address=0, labels=None):
    """Parses and encodes a single LEGv8 assembly instruction."""
    if labels is None:
        labels = {}
    
    # Adjusted parsing for D-type to better handle brackets and commas
    temp_instr_str = instruction_str.replace(',', ' ') # Replace all commas with spaces first
    if '[' in temp_instr_str and ']' in temp_instr_str:
        # For D-type like LDUR X9, [X10, #64]
        # Goal: LDUR X9 X10 #64 (effectively) after splitting, then handle specific parts
        temp_instr_str = temp_instr_str.replace('[', ' ').replace(']', ' ')
    
    parts_raw = temp_instr_str.split()
    parts = [p.strip().upper() for p in parts_raw if p.strip()]


    if not parts:
        raise ValueError("Empty instruction string.")

    op_name = parts[0]
    # R-type: ADD, SUB, AND, ORR, LSL, LSR
    if op_name in ["ADD", "SUB", "AND", "ORR"]:
        if len(parts) != 4: raise ValueError(f"R-type {op_name} expects Rd, Rn, Rm. Got: {instruction_str} -> {parts}")
        # ADD Rd, Rn, Rm
        return encode_r_type(op_name, parts[1], parts[2], parts[3], "0") # shamt=0
    elif op_name in ["LSL", "LSR"]: # LSL Rd, Rn, #shamt
        if len(parts) != 4: raise ValueError(f"R-type {op_name} expects Rd, Rn, #shamt. Got: {instruction_str} -> {parts}")
        return encode_r_type(op_name, parts[1], parts[2], "XZR", parts[3].replace('#','')) # Rm=XZR for LSL/LSR with imm shamt

    # I-type: ADDI, SUBI
    elif op_name in ["ADDI", "SUBI"]:
        if len(parts) != 4: raise ValueError(f"I-type {op_name} expects Rd, Rn, #imm. Got: {instruction_str} -> {parts}")
        # ADDI Rd, Rn, #imm
        return encode_i_type(op_name, parts[1], parts[2], parts[3])

    # D-type: LDUR, STUR
    elif op_name in ["LDUR", "STUR"]:
        # LDUR Rt, [Rn, #offset] -> after pre-processing parts: LDUR, Rt, Rn, #offset
        if len(parts) != 4: 
            raise ValueError(f"D-type {op_name} expects Rt, [Rn, #offset]. Parsed as: {parts} from {instruction_str}")
        rt_str = parts[1]
        rn_str = parts[2] # Rn is now parts[2] after custom split
        offset_str = parts[3] # offset is now parts[3]
        return encode_d_type(op_name, rt_str, rn_str, offset_str, "0")


    # B-type: B
    elif op_name == "B":
        if len(parts) != 2: raise ValueError(f"B-type expects B label_or_offset. Got: {instruction_str}")
        return encode_b_type(op_name, parts[1], current_address, labels)

    # CB-type: CBZ, CBNZ
    elif op_name in ["CBZ", "CBNZ"]:
        if len(parts) != 3: raise ValueError(f"CB-type {op_name} expects Rt, label_or_offset. Got: {instruction_str} -> {parts}")
        return encode_cb_type(op_name, parts[1], parts[2], current_address, labels)

    # IW-type: MOVZ, MOVK
    elif op_name in ["MOVZ", "MOVK"]:
        # MOVZ Rd, #imm, LSL #shift -> parts: MOVZ, Rd, #imm, LSL, #shift
        if len(parts) != 5 or parts[3] != "LSL": # Adjusted length to 5
            raise ValueError(f"IW-type {op_name} expects Rd, #imm, LSL, #shift. Got: {instruction_str} -> {parts}")
        rd_str = parts[1]
        imm_str = parts[2]
        lsl_val_str = parts[4] # e.g., #0, #16
        return encode_iw_type(op_name, rd_str, imm_str, lsl_val_str)

    else:
        raise ValueError(f"Unsupported instruction: {op_name}")


def main():
    example_labels = {
        "LOOP_START": 0x100,
        "END_IF": 0x110,
        "TARGET": 0x200,
    }
    
    # OPCODES for MOVZ/MOVK are now directly in the global OPCODES dictionary.

    instructions_to_encode = [
        "ADD X0, X1, X2",
        "LSL X3, X4, #5",
        "ADDI X5, X6, #100",
        "SUBI X7, X8, #-50",
        "LDUR X9, [X10, #64]",
        "STUR X11, [X12, #0]",
        "B #-8", 
        "B TARGET",
        "CBZ X13, #-4",
        "CBZ X14, LOOP_START",
        "MOVZ X1, #12345, LSL #0",
        "MOVK X2, #54321, LSL #16",
    ]

    output_filename = "instruction_encoding_output.txt"
    current_pc_for_labels = 0 

    with open(output_filename, "w") as f_out:
        header = f"{'Instruction':<40} -> {'Binary Representation (MSB to LSB)':<50} (Length)"
        print(header)
        f_out.write(header + "\n")
        print("-" * 100)
        f_out.write("-" * 100 + "\n")

        # Test encoding and then decoding from binary
        for i, instr_str in enumerate(instructions_to_encode):
            actual_pc = current_pc_for_labels + (i * 4)
            try:
                binary_code = parse_and_encode(instr_str, actual_pc, example_labels)
                instruction_int = int(binary_code, 2)
                
                result_line = f"\n--- Encoding Test ---\n{instr_str:<40} -> {binary_code:<50} ({len(binary_code)})"
                print(result_line)
                f_out.write(result_line + "\n")

                print("--- Decoding Test (from binary) ---")
                f_out.write("--- Decoding Test (from binary) ---\n")
                
                # Use the new binary decoder
                decoded_info = decode_binary_instruction_and_get_meaning(instruction_int, actual_pc)
                
                if decoded_info:
                    op_name_decoded = decoded_info.get('opcode_name', 'N/A')
                    type_decoded = decoded_info.get('type', 'N/A')
                    log_decoded = decoded_info.get('log', "  No detailed log from binary decoder.")

                    print(f"  Decoded OpName: {op_name_decoded}, Type: {type_decoded}")
                    f_out.write(f"  Decoded OpName: {op_name_decoded}, Type: {type_decoded}\n")
                    print(log_decoded)
                    f_out.write(log_decoded + "\n")

                    if 'fields' in decoded_info and decoded_info['fields']:
                        print("  Fields Extracted:")
                        f_out.write("  Fields Extracted:\n")
                        for field_name, data in decoded_info['fields'].items():
                            val_display = data.get('val', data.get('val_raw', 'N/A'))
                            field_line = f"    - {field_name:<20} ({data.get('bits', 'N/A')}): {data.get('bin', 'N/A')} (Val: {val_display}) - {data.get('meaning', '')}"
                            if 'val_signed_words' in data: # For branch offsets
                                field_line += f" (Signed Words: {data['val_signed_words']})"
                            elif 'val_signed' in data: # For I-type immediate
                                field_line += f" (Signed: {data['val_signed']})"
                            print(field_line)
                            f_out.write("    " + field_line + "\n")
                    if 'reg_ops' in decoded_info and decoded_info['reg_ops']:
                        print(f"  Register Operations: {decoded_info['reg_ops']}")
                        f_out.write(f"  Register Operations: {decoded_info['reg_ops']}\n")
                    if 'calculated' in decoded_info and decoded_info['calculated']:
                        print(f"  Calculated Values: {decoded_info['calculated']}")
                        f_out.write(f"  Calculated Values: {decoded_info['calculated']}\n")
                else:
                    print(f"  Failed to decode binary {binary_code} for '{instr_str}'")
                    f_out.write(f"  Failed to decode binary {binary_code} for '{instr_str}'\n")

            except (ValueError, SystemError, KeyError) as e: # Added KeyError for potential dict issues
                error_msg = f"Error processing '{instr_str}': {type(e).__name__} - {e}"
                print(error_msg)
                f_out.write(error_msg + "\n")
        
        # Test decoding an all-zero instruction
        print("\n--- Decoding Test (0x00000000) ---")
        f_out.write("\n--- Decoding Test (0x00000000) ---\n")
        try:
            decoded_nop = decode_binary_instruction_and_get_meaning(0, 0x200) # Example PC
            if decoded_nop:
                print(f"  Decoded OpName: {decoded_nop.get('opcode_name', 'N/A')}, Type: {decoded_nop.get('type', 'N/A')}")
                f_out.write(f"  Decoded OpName: {decoded_nop.get('opcode_name', 'N/A')}, Type: {decoded_nop.get('type', 'N/A')}\n")
                print(decoded_nop.get('log', "  No detailed log for NOP."))
                f_out.write(decoded_nop.get('log', "  No detailed log for NOP.") + "\n")
                if 'fields' in decoded_nop: print(f"  Fields: {decoded_nop['fields']}")
            else:
                print("  decode_binary_instruction_and_get_meaning returned None for 0x0")
                f_out.write("  decode_binary_instruction_and_get_meaning returned None for 0x0\n")
        except Exception as e:
            print(f"  Error decoding 0x0: {type(e).__name__} - {e}")
            f_out.write(f"  Error decoding 0x0: {type(e).__name__} - {e}\n")

    print(f"\nEncoding and decoding results printed to console and logged in: {output_filename}")

if __name__ == "__main__":
    main()
