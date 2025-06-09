# -*- coding: utf-8 -*-

# --- Các Khối Phần Cứng Mô Phỏng ---
def pc_plus_4_adder(current_pc):
    return (current_pc + 4) & 0xFFFFFFFFFFFFFFFF

def sign_extend(value, bits):
    value = int(value)
    if bits <= 0 or bits >= 64:
        return value & 0xFFFFFFFFFFFFFFFF

    value_mask = (1 << bits) - 1
    value_masked = value & value_mask 
    sign_bit_mask = 1 << (bits - 1)

    if (value_masked & sign_bit_mask) != 0: # Negative
        upper_bits_mask = (~0 << bits) 
        extended_value = value_masked | upper_bits_mask
    else: # Positive
        extended_value = value_masked
    return extended_value & 0xFFFFFFFFFFFFFFFF

def branch_target_adder(base_pc, byte_offset):
    result = base_pc + byte_offset
    return result & 0xFFFFFFFFFFFFFFFF

# --- Các Bộ Chọn (Mux) Mô Phỏng ---
def alu_input2_mux(reg_read_data2, sign_extended_imm, alu_src_signal):
    return sign_extended_imm if alu_src_signal == 1 else reg_read_data2

def writeback_data_mux(alu_result_data, mem_read_data, mem_to_reg_signal):
    if mem_to_reg_signal == 0: return alu_result_data
    elif mem_to_reg_signal == 1: return mem_read_data
    elif mem_to_reg_signal == -1: return None 
    else: raise ValueError(f"Mux Error: Invalid MemToReg signal: {mem_to_reg_signal}")

def pc_source_mux(pc_plus_4_val, branch_target_addr, pc_src_signal):
    return branch_target_addr if pc_src_signal == 1 else pc_plus_4_val

def mux1(bit_20_16, bit_4_0, reg2loc):
    return bit_20_16 if reg2loc == 0 else bit_4_0

# --- Logic Điều Khiển Nhánh ---
def branch_control_logic(branch_signal, zero_flag, uncond_branch_signal):
    pc_src = (branch_signal & zero_flag) | uncond_branch_signal
    return pc_src