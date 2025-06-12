"""
Centralized ALU operation mappings for LEGv8 Simulator
Contains both instruction-to-operation mappings and operation-to-control-bits mappings
"""

# ALU Operation mappings by instruction type
ALU_OP_MAPPINGS = {
    # R-format instructions
    'ADD': 'add',
    'SUB': 'sub', 
    'AND': 'and',
    'ORR': 'orr',
    'EOR': 'eor',
    'MUL': 'mul',
    'DIV': 'div',
    'LSL': 'lsl',
    'LSR': 'lsr',
    
    # I-format instructions  
    'ADDI': 'add',
    'SUBI': 'sub',
    'ANDI': 'and', 
    'ORRI': 'orr',
    'EORI': 'eor',
    
    # D-format instructions
    'LDUR': 'add',
    'STUR': 'add',
    
    # CB-format instructions
    'CBZ': 'pass1',   # Pass through Rt value to check for zero
    'CBNZ': 'pass1',  # Pass through Rt value to check for zero
    
    # B-format instructions (no ALU operation needed)
    'B': None,
}

# ALU operation to control bits mapping (for visualization)
ALU_CONTROL_BITS = {
    'pass1': '0111',
    'add': '0010', 
    'orr': '0001',
    'sub': '0110',
    'and': '0000',
    'eor': '0100',  # XOR
    'mul': '1000',  # Extended operation
    'div': '1001',  # Extended operation  
    'lsl': '1010',  # Shift left
    'lsr': '1011',  # Shift right
}

def get_alu_operation(opcode):
    """Get ALU operation string for given instruction opcode"""
    return ALU_OP_MAPPINGS.get(opcode.upper())

def get_alu_control_bits(alu_operation):
    """Get ALU control bits for given ALU operation"""
    return ALU_CONTROL_BITS.get(alu_operation, 'XXXX')

def get_alu_operation_for_instruction_type(opcode):
    """
    Get ALU operation for instruction, with fallback logic
    Returns tuple: (operation, is_valid)
    """
    operation = get_alu_operation(opcode)
    if operation is None:
        return None, False
    return operation, True