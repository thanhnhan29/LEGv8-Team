# -*- coding: utf-8 -*-
import re
import traceback
import copy

from .register_file import RegisterFile
from .memory import Memory
from .alu import ALU
from .control_unit import ControlUnit
from .micro_step import MicroStepState
from . import datapath_components as dpc # datapath_components
from .instruction_handlers import INSTRUCTION_HANDLERS # The big dispatch table

DISPLAY_ADDRESS_OFFSET = 4194304

class SimulatorEngine:
    def __init__(self):
        self.pc = 0
        self.registers = RegisterFile()
        self.data_memory = Memory(memory_type="data")
        self.instruction_memory = Memory(memory_type="instruction") # Holds processed instructions
        self.raw_instruction_memory = Memory(memory_type="instruction") # Holds original user strings
        self.binary_instruction_memory = Memory(memory_type="instruction") # NEW: Holds binary representations
        self.label_table = {} # label_name -> address

        self.control_unit = ControlUnit()
        # ALU is stateless, can call ALU.execute directly

        self.current_instruction_generator = None
        self.simulation_loaded = False
        self.error_state = None
        
        self.current_instr_addr_for_display = -1 # For API to know what was loaded/is about to run
        self.current_instr_str_for_display = ""  # For API
        
        self.micro_step_index_internal = -1      # Tracks micro-step within current instruction execution
        self.instruction_completed_flag = False  # Set when an instruction finishes all its micro-steps

        self.initialize_state()

    def initialize_state(self):
        self.pc = 0
        self.registers.initialize()
        self.data_memory.initialize()
        self.instruction_memory.initialize()
        self.raw_instruction_memory.initialize()
        self.binary_instruction_memory.initialize()  # NEW: Initialize binary memory
        self.label_table = {}
        
        self.current_instruction_generator = None
        self.simulation_loaded = False
        self.error_state = None
        
        self.current_instr_addr_for_display = 0 # Default to 0
        self.current_instr_str_for_display = "(No instruction at PC=0)" 
        
        self.micro_step_index_internal = -1
        self.instruction_completed_flag = False
        print("--- Simulator engine state reset to defaults. ---")

    def load_program_data(self, processed_instr_dict, raw_instr_dict, labels_dict, binary_instr_dict=None):
        self.initialize_state() # Reset before loading new program
        self.instruction_memory.load_instructions(processed_instr_dict)
        self.raw_instruction_memory.load_instructions(raw_instr_dict) # Store raw strings
        
        # NEW: Load binary instructions if provided
        if binary_instr_dict:
            self.binary_instruction_memory.load_instructions(binary_instr_dict)
        
        self.label_table = labels_dict.copy()
        
        self.pc = 0 # Start execution at address 0
        self.simulation_loaded = True
        self.error_state = None
        self.current_instruction_generator = None
        self.micro_step_index_internal = -1
        self.instruction_completed_flag = False
        
        # Set initial display info
        self.current_instr_addr_for_display = self.pc
        try:
            self.current_instr_str_for_display = self.raw_instruction_memory.fetch_instruction(self.pc)
        except ValueError:
            self.current_instr_str_for_display = "(No instruction at PC=0)"

        print(f"--- Program data loaded into simulator. PC=0x{self.pc:X}. ---")
        return len(processed_instr_dict)

    def get_cpu_state_for_api(self):
        # Current state from RegisterFile
        # We want to ensure all standard registers are present in the output, in a specific order.

        # Define the order of display names
        special_priority_aliases = ["SP", "FP", "LR"]
        other_special_regs = ["XZR"]
        # General purpose registers X0-X27 (X28, X29, X30 are covered by SP, FP, LR)
        general_numeric_regs = [f"X{i}" for i in range(28)] 

        all_reg_names_for_display = special_priority_aliases + other_special_regs + general_numeric_regs

        complete_regs_display = {}
        for display_name in all_reg_names_for_display:
            reg_to_read = display_name
            if display_name == "FP":
                reg_to_read = "X29"  # Map FP to X29 for reading
            elif display_name == "SP":
                reg_to_read = "X28"  # Map SP to X28 for reading
            elif display_name == "LR":
                reg_to_read = "X30"  # Map LR to X30 for reading
            
            # For X0-X27 and XZR, display_name is the same as reg_to_read
            # self.registers.read() should handle these canonical names.
            value = self.registers.read(reg_to_read) 
            complete_regs_display[display_name] = f"0x{value:X}"

        return {
            "pc": f"0x{self.pc:X}",
            "registers": complete_regs_display, # Use the new ordered dictionary
            "data_memory": self.data_memory.get_display_dict(),
            "current_binary": self._get_current_binary_instruction(),
        }

    def _get_current_binary_instruction(self):
        """Get binary representation of instruction at current PC"""
        try:
            return self.binary_instruction_memory.fetch_instruction(self.pc)
        except ValueError:
            return "00000000000000000000000000000000"  # Return NOP if not found

    def _execute_instruction_detailed_generator(self):
        """
        Generator that yields MicroStepState objects.
        This is a refactored version of the original execute_instruction_detailed_generator.
        It now uses self.pc, self.registers, self.data_memory, self.instruction_memory etc.
        """
        current_pc_of_instruction = self.pc # PC at the start of this instruction
        instruction_str_processed = "NOP" 
        final_next_pc = current_pc_of_instruction + 4
        pc_p4 = 0

        control_values = {}
        decoded_info = {}
        exec_result = {}
        mem_result = {}
        # wb_log_result = {} # Not strictly needed as var here, local to WB

        read_data1, read_data2 = 0, 0
        sign_extended_imm = 0
        alu_result_val = 0 # Renamed from alu_result to avoid conflict with alu module/class
        alu_zero_flag = 0
        data_read_from_mem = None
        branch_target_addr_val = 0 # Renamed

        current_stage_name = "Start"
        current_micro_step_index_yield = -1 # For MicroStepState object

        try:
            # --- Micro-Step 0: Instruction Fetch (IF) ---
            current_stage_name = "Fetch"
            current_micro_step_index_yield = 0
            stage_log_if = f"[{current_stage_name} @ PC=0x{current_pc_of_instruction + DISPLAY_ADDRESS_OFFSET:X}]\n"
            # ... (active_blocks, active_paths, animated_signals setup for IF)
            active_blocks_if = ["block-pc", "block-imem", "block-adder1"]
            active_paths_if = ["path-pc-imem", "path-pc-adder1","path-4-adder"]
            animated_signals_if = [
                {"path_id": "path-pc-imem", "bits": [f"0x{current_pc_of_instruction + DISPLAY_ADDRESS_OFFSET:X}"], "duration": 0.3},
                {"path_id": "path-pc-adder1", "bits": [f"0x{current_pc_of_instruction + DISPLAY_ADDRESS_OFFSET:X}"], "duration": 0.2},
                {"path_id": "path-4-adder", "bits": [f"0x4"], "duration": 0.2},
            ]
            try:
                # Fetch the processed (string) instruction for logging and opcode detection
                instruction_str_processed = self.instruction_memory.fetch_instruction(current_pc_of_instruction)
                # Fetch the binary instruction
                #bits_instruction = self.binary_instruction_memory.fetch_instruction(current_pc_of_instruction)
                stage_log_if += f"  Fetched Processed Instruction: '{instruction_str_processed}'\n"
                #stage_log_if += f"  Fetched Binary Instruction: {bits_instruction}\n" # Log the binary
            except ValueError as e:
                stage_log_if += f"  Error: {e}\n"
                yield MicroStepState(current_stage_name, current_micro_step_index_yield, stage_log_if, active_blocks_if, active_paths_if, animated_signals_if).to_dict()
                return {"next_pc": current_pc_of_instruction, "error": str(e)}

            pc_p4 = dpc.pc_plus_4_adder(current_pc_of_instruction)
            stage_log_if += f"  PC+4 Adder -> 0x{pc_p4:X}"
            # ... (update paths/signals for IF)
            active_paths_if.append("path-adder1-mux4-in0") 
            animated_signals_if.append({"path_id": "path-adder1-mux4-in0", "bits":[f"0x{pc_p4 + DISPLAY_ADDRESS_OFFSET:X}"], "duration": 0.2, "start_delay": 0.2})
            yield MicroStepState(current_stage_name, current_micro_step_index_yield, stage_log_if, active_blocks_if, active_paths_if, animated_signals_if).to_dict()
            final_next_pc = pc_p4


            # --- Micro-Step 1: Instruction Decode / Register Fetch (ID) ---
            current_stage_name = "Decode"
            current_micro_step_index_yield = 1
            stage_log_id = f"[{current_stage_name}]\n"
            
            try:
                instruction_str_upper = instruction_str_processed.strip().upper()
                parts = re.split(r'[,\s()\[\]]+', instruction_str_upper)
                parts = [p for p in parts if p]
                opcode = parts[0].upper() if parts else "NOP"
                stage_log_id += f"  Opcode Detected: {opcode}\n"
            except Exception as e:
                opcode = "NOP"
                stage_log_id += f"  Error extracting opcode, defaulting to NOP: {e}\n"
            
            # ... (active_blocks, active_paths, animated_signals setup for ID)
            active_blocks_id = ["block-control", "block-regs"]
            active_paths_id = ["path-imem-out", "path-instr-control", "path-instr-regs", "path-instr-regwriteaddr", "path-instr-alucontrol"]
            animated_signals_id = [
                {"path_id": "path-imem-out", "bits":[f"{instruction_str_processed}"], "duration": 0.1},
                {"path_id": "path-instr-control", "bits":[f"{opcode}"], "duration": 0.2},
                {"path_id": "path-instr-regs", "bits":[f"{INSTRUCTION_HANDLERS.get(opcode)['decode'](parts).get('read_reg1_addr')}"], "duration": 0.2},
                {"path_id": "path-instr-regwriteaddr", "bits":[f"{INSTRUCTION_HANDLERS.get(opcode)['decode'](parts).get('rd')}"],"duration":0.2},
                {"path_id": "path-instr-alucontrol", "bits":[f"{opcode}"],"duration":0.2}
            ]
            #yield MicroStepState(current_stage_name, current_micro_step_index_yield, stage_log_id, active_blocks_id, active_paths_id, animated_signals_id, control_values).to_dict()
            if(self.control_unit.get_control_signals(opcode).get('ALUSrc', 0) == 0 or self.control_unit.get_control_signals(opcode).get('MemWrite') == 1):
                if(self.control_unit.get_control_signals(opcode).get('Reg2loc', 0)==0):
                    active_paths_id.append("path-instr-reg2loc-0")
                    animated_signals_id.append({"path_id": "path-instr-reg2loc-0", "bits":[f"{INSTRUCTION_HANDLERS.get(opcode)['decode'](parts).get('read_reg2_addr')}"],"duration":0.2},)
                else:
                    active_paths_id.append("path-instr-reg2loc-1")
                    animated_signals_id.append({"path_id": "path-instr-reg2loc-1", "bits":[f"{INSTRUCTION_HANDLERS.get(opcode)['decode'](parts).get('read_reg1_addr')}"],"duration":0.2},)

                #selected_addr2_mux1 = dpc.mux1(INSTRUCTION_HANDLERS.get(opcode)['decode'](parts).get('rt'), INSTRUCTION_HANDLERS.get(opcode)['decode'](parts).get('rd'), self.control_unit.get_control_signals(opcode).get('Reg2loc', 0))
                animated_signals_id.append({"path_id": "path-reg2loc-out", "bits":[f"{INSTRUCTION_HANDLERS.get(opcode)['decode'](parts).get('read_reg2_addr')}"],"duration":0.2})
                active_paths_id.append("path-reg2loc-out")
            try:
                control_values = self.control_unit.get_control_signals(opcode)
                # Add control signal paths for visualization
                control_paths = ["control-reg2loc-enable","control-uncondbranch-enable", "control-branch-enable", 'control-memread-enable', 'control-memtoreg-enable', 'control-reg2loc-enable', 'control-aluop-enable', 'control-memwrite-enable', 'control-alusrc-enable', 'control-regwrite-enable']
                active_paths_id.extend(control_paths)
                
                # Add control signal animations
                control_signal_animations = []
                start_delay_base = 0.10
                for i, (signal_name, signal_value) in enumerate(control_values.items()):
                    control_path_map = {
                        'UncondBranch': 'control-uncondbranch-enable',
                        'Branch': 'control-branch-enable',
                        'MemRead': 'control-memread-enable',
                        'MemToReg': 'control-memtoreg-enable',
                        'Reg2Loc': 'control-reg2loc-enable',
                        'ALUOp': 'control-aluop-enable',
                        'MemWrite': 'control-memwrite-enable',
                        'ALUSrc': 'control-alusrc-enable',
                        'RegWrite': 'control-regwrite-enable'
                    }
                    
                    if signal_name in control_path_map:
                        path_id = control_path_map[signal_name]
                        # Format signal value for display
                        if isinstance(signal_value, str):
                            display_value = signal_value
                        else:
                            display_value = str(signal_value)
                        
                        control_signal_animations.append({
                            "path_id": path_id,
                            "bits": [display_value],
                            "duration": 0.2,
                            "start_delay": start_delay_base + (i * 0.05)  # Stagger animations slightly
                        })
                
                animated_signals_id.extend(control_signal_animations)
                #print(control_values)
                handlers = INSTRUCTION_HANDLERS.get(opcode)
                if not handlers or 'decode' not in handlers:
                    raise ValueError(f"Unsupported or missing decode handler for {opcode}")
                decode_handler = handlers['decode']
                decoded_info = decode_handler(parts)
                decoded_info['opcode'] = opcode 
                stage_log_id += decoded_info.get('log', "  (No decode log)") + "\n"
                #print(decoded_info.get('log', "  (No decode log)") + "\n")
                read_reg1_addr = decoded_info.get('read_reg1_addr')
                read_reg2_addr = decoded_info.get('read_reg2_addr', None)
                if read_reg1_addr:
                    read_data1 = self.registers.read(read_reg1_addr)
                    stage_log_id += f"  Read Register 1 ({read_reg1_addr}): 0x{read_data1:X}\n"
                    # ADDED: Animation for Register 1 read data output
                    active_paths_id.append("path-regs-rdata1")
                    animated_signals_id.append({"path_id": "path-regs-rdata1", "bits":[f"0x{read_data1:X}"], "duration": 0.3, "start_delay": 4.5})
                if read_reg2_addr:
                    read_data2 = self.registers.read(read_reg2_addr)
                    stage_log_id += f"  Read Register 2 ({read_reg2_addr}): 0x{read_data2:X}\n"
                    # ADDED: Animation for Register 2 read data output  
                    if(self.control_unit.get_control_signals(opcode).get('ALUSrc', 0) == 0):
                        active_paths_id.append("path-regs-rdata2")
                        animated_signals_id.append({"path_id": "path-regs-rdata2", "bits":[f"0x{read_data2:X}"], "duration": 0.3, "start_delay": 4.5})
                if decoded_info.get('shamt') is not None:
                    shamt_bit = int(decoded_info.get('shamt_bit'))
                    shamt = int(decoded_info.get('shamt'))
                    sign_extended_imm = dpc.sign_extend(shamt, shamt_bit)
                    stage_log_id += f"  Sign Extend shamt ({shamt_bit}b): shamt={shamt} -> {sign_extended_imm} (0x{sign_extended_imm:X})\n"
                    if "block-signext" not in active_blocks_id: active_blocks_id.append("block-signext")
                    active_paths_id.extend(["path-instr-signext"])
                    animated_signals_id.extend([
                        {"path_id": "path-instr-signext", "bits":[f"{shamt}"], "duration": 0.2, "start_delay": 0.1},
                        #{"path_id": "path-signext-out-mux2", "bits":[f"0x{sign_extended_imm:X}"], "duration": 0.3, "start_delay": 0.3}
                    ])
                imm_val = decoded_info.get('imm_val')
                if imm_val is not None:
                    imm_bits = decoded_info.get('imm_bits', 0)
                    sign_extended_imm = dpc.sign_extend(imm_val, imm_bits)
                    stage_log_id += f"  Sign Extend Immediate ({imm_bits}b): Val={imm_val} -> {sign_extended_imm} (0x{sign_extended_imm:X})\n"
                    # ... (update paths/signals for sign extend)
                    if "block-signext" not in active_blocks_id: active_blocks_id.append("block-signext")
                    active_paths_id.extend(["path-instr-signext"])
                    animated_signals_id.extend([
                        {"path_id": "path-instr-signext", "bits":[f"{imm_val}"], "duration": 0.2, "start_delay": 0.1},
                        #{"path_id": "path-signext-out-mux2", "bits":[f"0x{sign_extended_imm:X}"], "duration": 0.3, "start_delay": 0.3}
                    ])

                # ADDED: Animation for ALU Input 2 via Mux2 (determined by ALUSrc)
                # MODIFIED: Animation for ALU Input 2 via Mux2 (determined by ALUSrc) - Sequential timing
                # MODIFIED: Animation for ALU Input 2 via Mux2 (determined by ALUSrc) - Sequential timing
                if "block-mux2" not in active_blocks_id and control_values.get('ALUOp', 0) != "01" and control_values.get('ALUOp', 0) != "XX": 
                    active_blocks_id.append("block-mux2")
                alu_src = control_values.get('ALUSrc', 0)
                alu_input2_val = dpc.alu_input2_mux(read_data2, sign_extended_imm, alu_src)
                
                if alu_src == 0 and control_values.get('ALUOp', 0) != "01" and control_values.get('ALUOp', 0) != "XX":  # Use register data
                    # Sequential: read_data2 → Mux2 → ALU
                    # Note: path-regs-rdata2 already animated at start_delay: 0.5
                    active_paths_id.extend(["path-mux2-alu"])
                    animated_signals_id.extend([
                        {"path_id": "path-mux2-alu", "bits":[f"0x{alu_input2_val:X}"], "duration": 0.1, "start_delay": 8.5}  # CHANGED: 0.6 → 0.8 (after read_data2 at 0.5)
                    ])
                    stage_log_id += f"  ALU Input 2 via Mux2 (ALUSrc=0): 0x{alu_input2_val:X} from Register\n"
                elif control_values.get('ALUOp', 0) != "01" and control_values.get('ALUOp', 0) != "XX":  # Use immediate data
                    # Sequential: sign_extended_imm → Mux2 → ALU
                    active_paths_id.extend(["path-signext-out-mux2", "path-mux2-alu"])
                    animated_signals_id.extend([
                        {"path_id": "path-signext-out-mux2", "bits":[f"0x{alu_input2_val:X}"], "duration": 0.3, "start_delay": 4.5},  # CHANGED: 0.5 → 0.4 (after sign extend at ~0.3)
                        {"path_id": "path-mux2-alu", "bits":[f"0x{alu_input2_val:X}"], "duration": 0.1, "start_delay": 8.5}       # CHANGED: 0.6 → 0.8 (after signext-out-mux2)
                    ])
                    stage_log_id += f"  ALU Input 2 via Mux2 (ALUSrc=1): 0x{alu_input2_val:X} from Immediate\n"
                
                branch_offset_val = decoded_info.get('branch_offset_val')
                if branch_offset_val is not None:
                    branch_offset_bits = decoded_info.get('branch_offset_bits', 0)
                    stage_log_id += f"  Branch Offset Value: {branch_offset_val} ({branch_offset_bits}b)\n"
                    # ... (update paths/signals for branch offset if any in ID)
                    if "block-signext" not in active_blocks_id: active_blocks_id.append("block-signext")
                    active_paths_id.append("path-instr-signext") 
                    animated_signals_id.append({"path_id": "path-instr-signext", "bits":[branch_offset_val], "duration": 0.2, "start_delay": 0.1})


                yield MicroStepState(current_stage_name, current_micro_step_index_yield, stage_log_id, active_blocks_id, active_paths_id, animated_signals_id, control_values).to_dict()
            except (IndexError, ValueError, TypeError, KeyError) as e:
                stage_log_id += f"  Error: {e}\n traceback: {traceback.format_exc()}\n"
                yield MicroStepState(current_stage_name, current_micro_step_index_yield, stage_log_id, active_blocks_id, active_paths_id, animated_signals_id, control_values).to_dict()
                return {"next_pc": pc_p4, "error": f"Decode Error: {e}"}

            # --- Micro-Step 2: Execute (EX) ---
            current_stage_name = "Execute"
            current_micro_step_index_yield = 2
            stage_log_ex = f"[{current_stage_name}]\n"
            # ... (active_blocks, active_paths, animated_signals setup for EX)
            active_blocks_ex = ["block-alu", "block-alucontrol"]
            active_paths_ex = []
            animated_signals_ex = []
            try:
                alu_src = control_values.get('ALUSrc', 0)
                alu_input1_val = read_data1
                alu_input2_val = dpc.alu_input2_mux(read_data2, sign_extended_imm, alu_src)
                
                # ... (logging and visualization for ALU inputs and Mux2)
                reg1_source_name = decoded_info.get('read_reg1_addr', 'N/A')
                stage_log_ex += f"  ALU Input 1 (from {reg1_source_name}): 0x{alu_input1_val:X}\n"
                #active_paths_ex.append("path-regs-rdata1")
                #animated_signals_ex.append({"path_id": "path-regs-rdata1", "bits":[f"0x{alu_input1_val:X}"], "duration": 0.2})

                if alu_src == 0: 
                    reg2_source_name = decoded_info.get('read_reg2_addr','N/A')
                    stage_log_ex += f"  ALU Input 2 (from {reg2_source_name}): 0x{alu_input2_val:X} (Mux2 Sel=0)\n"
                    # active_paths_ex.extend(["path-regs-rdata2", "path-mux2-alu"])
                    # animated_signals_ex.extend([
                    #     {"path_id": "path-regs-rdata2", "bits":[f"0x{alu_input2_val:X}"], "duration": 0.1},
                    #     {"path_id": "path-mux2-alu", "bits":[f"0x{alu_input2_val:X}"], "duration": 0.1, "start_delay": 0.1}
                    # ])
                else: 
                    stage_log_ex += f"  ALU Input 2 (from Imm): {alu_input2_val} (0x{alu_input2_val:X}) (Mux2 Sel=1)\n"
                    # active_paths_ex.extend(["path-signext-out-mux2", "path-mux2-alu"])
                    # animated_signals_ex.extend([
                    #     {"path_id": "path-signext-out-mux2", "bits":[f"0x{alu_input2_val:X}"], "duration": 0.1},
                    #     {"path_id": "path-mux2-alu", "bits":[f"0x{alu_input2_val:X}"], "duration": 0.1, "start_delay": 0.1}
                    # ])


                opcode = decoded_info['opcode']
                handlers = INSTRUCTION_HANDLERS.get(opcode)
                if not handlers or 'execute' not in handlers:
                    raise ValueError(f"Missing execute handler for opcode: {opcode}")
                execute_handler = handlers['execute']
                
                # Pass current_pc_of_instruction
                exec_result = execute_handler(decoded_info, control_values, alu_input1_val, alu_input2_val, sign_extended_imm, current_pc_of_instruction)
                stage_log_ex += exec_result.get('log', "  (No execute log)") + "\n"

                alu_result_val = exec_result.get('alu_result', 0)
                alu_zero_flag = exec_result.get('alu_zero_flag', 0)
                branch_target_addr_val = exec_result.get('branch_target_addr', 0)

                # ... (visualization for ALU control signal and results)
                alu_op = control_values.get('ALUOp', 'XX')
                if alu_op != 'XX':
                    # Add ALU Control to ALU signal path
                    #active_paths_ex.append("control-alucontrol-alu")
                    #animated_signals_ex.append({"path_id": "control-alucontrol-alu", "bits":[alu_op], "duration": 0.15, "start_delay": 0.1})
                    
                    # ALU result and zero flag
                    if(int(control_values.get('MemToReg', 0)) == 0):
                        active_paths_ex.append("path-alu-mux3") 
                        animated_signals_ex.append({"path_id": "path-alu-mux3", "bits":[f"0x{alu_result_val:X}"], "duration": 0.3, "start_delay": 0.2})
                    active_paths_ex.append("path-alu-zero")
                    animated_signals_ex.append({"path_id": "path-alu-zero", "bits":[f"{alu_zero_flag}"], "duration": 0.1, "start_delay": 0.2})

                if branch_target_addr_val != 0: 
                    if "block-adder2" not in active_blocks_ex: active_blocks_ex.append("block-adder2")
                    active_paths_ex.append("path-pc-adder2")
                    animated_signals_ex.append({"path_id": "path-pc-adder2", "bits":[f"0x{current_pc_of_instruction + DISPLAY_ADDRESS_OFFSET:X}"], "duration": 0.2})
                    active_paths_ex.append("path-signext-br-shift") 
                    animated_signals_ex.append({"path_id": "path-signext-br-shift", "bits":[f"0x{branch_offset_val:X}"], "duration": 0.2})
                    active_paths_ex.append("path-shift-adder2") 
                    animated_signals_ex.append({"path_id": "path-shift-adder2", "bits":[f"0x{(branch_offset_val):X}"], "duration": 0.2})
                    active_paths_ex.append("path-adder2-or")
                    animated_signals_ex.append({"path_id": "path-adder2-or", "bits":[f"0x{(branch_offset_val) + DISPLAY_ADDRESS_OFFSET:X}"], "duration": 0.2, "start_delay": 0.2})


                yield MicroStepState(current_stage_name, current_micro_step_index_yield, stage_log_ex, active_blocks_ex, active_paths_ex, animated_signals_ex, control_values).to_dict()
            except (ValueError, TypeError) as e:
                stage_log_ex += f"  Error: {e}\n traceback: {traceback.format_exc()}\n"
                yield MicroStepState(current_stage_name, current_micro_step_index_yield, stage_log_ex, active_blocks_ex, active_paths_ex, animated_signals_ex, control_values).to_dict()
                return {"next_pc": pc_p4, "error": f"Execute Error: {e}"}

            # --- Micro-Step 3: Memory Access (MEM) ---
            current_stage_name = "Memory"
            current_micro_step_index_yield = 3
            stage_log_mem = f"[{current_stage_name}]\n"
            # ... (active_blocks, active_paths, animated_signals setup for MEM)
            active_blocks_mem = []
            active_paths_mem = []
            animated_signals_mem = []
            try:
                mem_read_ctrl = control_values.get('MemRead', 0) # Renamed from mem_read
                mem_write_ctrl = control_values.get('MemWrite', 0) # Renamed from mem_write

                opcode = decoded_info['opcode']
                handlers = INSTRUCTION_HANDLERS.get(opcode)
                if not handlers or 'memory' not in handlers:
                    raise ValueError(f"Missing memory handler for opcode: {opcode}")
                memory_handler = handlers['memory']
                
                # Pass self.data_memory object to the handler
                mem_result = memory_handler(decoded_info, control_values, alu_result_val, read_data2, self.data_memory)
                stage_log_mem += mem_result.get('log', "  (No memory log)") + "\n"
                data_read_from_mem = mem_result.get('data_read_from_mem')

                # ... (visualization for memory access)
                mem_address_for_vis = alu_result_val 

                if mem_read_ctrl == 1:
                    if "block-datamem" not in active_blocks_mem: active_blocks_mem.append("block-datamem")
                    active_paths_mem.extend(["path-alu-result"])
                    animated_signals_mem.extend([
                        {"path_id": "path-alu-result", "bits":[f"0x{mem_address_for_vis:X}"], "duration": 0.2},
                        #{"path_id": "control-memread-enable", "bits":["READ"], "duration": 0.1}
                    ])
                    if data_read_from_mem is not None:
                        active_paths_mem.append("path-mem-readdata")
                        animated_signals_mem.append({"path_id": "path-mem-readdata", "bits":[f"0x{data_read_from_mem:X}"], "duration": 0.3, "start_delay": 0.2})
                elif mem_write_ctrl == 1:
                    if "block-datamem" not in active_blocks_mem: active_blocks_mem.append("block-datamem")
                    active_paths_mem.extend(["path-alu-result", "path-rdata2-memwrite"])
                    animated_signals_mem.extend([
                        {"path_id": "path-alu-result", "bits":[f"0x{mem_address_for_vis:X}"], "duration": 0.2},
                        {"path_id": "path-rdata2-memwrite", "bits":[f"0x{read_data2:X}"], "duration": 0.3, "start_delay": 0.1},
                        #{"path_id": "control-memwrite-enable", "bits":["WRITE"], "duration": 0.1}
                    ])
                yield MicroStepState(current_stage_name, current_micro_step_index_yield, stage_log_mem, active_blocks_mem, active_paths_mem, animated_signals_mem, control_values).to_dict()
            except (ValueError, TypeError, KeyError) as e:
                stage_log_mem += f"  Error: {e}\n traceback: {traceback.format_exc()}\n"
                yield MicroStepState(current_stage_name, current_micro_step_index_yield, stage_log_mem, active_blocks_mem, active_paths_mem, animated_signals_mem, control_values).to_dict()
                return {"next_pc": pc_p4, "error": f"Memory Error: {e}"}

            # --- Micro-Step 4: Write Back (WB) & PC Update ---
            current_stage_name = "Write Back / PC Update"
            current_micro_step_index_yield = 4
            stage_log_wb = f"[{current_stage_name}]\n"
            # ... (active_blocks, active_paths, animated_signals setup for WB)
            active_blocks_wb = [] 
            active_paths_wb = []
            animated_signals_wb = []
            try:
                # --- Part 1: Write Back to Register File ---
                reg_write_ctrl = control_values.get('RegWrite', 0) # Renamed
                mem_to_reg_ctrl = control_values.get('MemToReg', 0) # Renamed
                data_to_write_back = None
                write_occurred = False
                wb_specific_log = ""

                if reg_write_ctrl == 1:
                    active_blocks_wb.append("block-mux3")
                    data_to_write_back = dpc.writeback_data_mux(alu_result_val, data_read_from_mem, mem_to_reg_ctrl)
                    dest_reg = decoded_info.get('rd') or decoded_info.get('rt')

                    if data_to_write_back is not None and dest_reg:
                        wb_specific_log += f"  Write Back Stage: RegWrite=1 for {dest_reg}.\n"
                        # ... (visualization for RegWrite and Mux3)
                        #active_paths_wb.extend(["control-regwrite-enable"])
                        # animated_signals_wb.extend([
                        #     {"path_id": "control-regwrite-enable", "bits":["WR_EN"],"duration":0.1},
                        # ])
                        wb_path_mux_out = "path-mux3-wb"  
                        wb_path_to_regs = "path-mux3-wb" # Use same path since they connect
                        active_paths_wb.extend([wb_path_mux_out])
                        mux3_in_path, mux3_sel_path = "", ""

                        if mem_to_reg_ctrl == 0: 
                            wb_specific_log += f"  Write Back Stage: Mux3 selects ALU Result (0x{data_to_write_back:X}).\n"
                            mux3_in_path = "path-alu-mux3" # Use existing ALU result path
                            mux3_sel_path = "control-memtoreg-enable" # Use existing control signal
                        elif mem_to_reg_ctrl == 1: 
                            wb_specific_log += f"  Write Back Stage: Mux3 selects Memory Data (0x{data_to_write_back:X}).\n"
                            mux3_in_path = "path-mem-readdata" # Use existing memory read path
                            mux3_sel_path = "control-memtoreg-enable" # Use existing control signal 
                        
                        # if mux3_in_path: active_paths_wb.append(mux3_in_path)
                        # if mux3_sel_path: active_paths_wb.append(mux3_sel_path)
                        
                        # data_to_write_back is guaranteed to be not None here due to the outer if condition
                        # (i.e., inside 'if data_to_write_back is not None and dest_reg:')
                        formatted_data = f"0x{data_to_write_back:X}" if isinstance(data_to_write_back, int) else str(data_to_write_back)

                        temp_animations_for_wb = []

                        # Animation for the Mux3 select signal (MemToReg)
                        # mux3_sel_path is "control-memtoreg-enable", its value is mem_to_reg_ctrl
                        # if mux3_sel_path: # This is "control-memtoreg-enable"
                        #      temp_animations_for_wb.append({
                        #          "path_id": mux3_sel_path,
                        #          "bits": [str(mem_to_reg_ctrl)], # Animate the actual select signal value
                        #          "duration": 0.1,
                        #          "start_delay": 0.0 # Show selector first or concurrently
                        #      })

                        # Animation for the selected input path feeding into Mux3
                        if mux3_in_path:
                            selected_input_value_str = ""
                            if mem_to_reg_ctrl == 0: # Mux3 selected ALU result
                                selected_input_value_str = f"0x{alu_result_val:X}"
                            elif mem_to_reg_ctrl == 1: # Mux3 selected Memory data
                                if data_read_from_mem is not None:
                                    selected_input_value_str = f"0x{data_read_from_mem:X}"
                                else:
                                    # Fallback if data_read_from_mem is None when MemToReg=1
                                    selected_input_value_str = "0x0" # Defaulting for visualization

                            # if selected_input_value_str: # Ensure a string was set
                            #     temp_animations_for_wb.append(
                            #         {"path_id": mux3_in_path, "bits": [selected_input_value_str], "duration": 0.1, "start_delay": 0.05} # After selector
                            #     )
                        
                        # Animation for the output path of Mux3 (this shows data_to_write_back)
                        # wb_path_mux_out is the ID of the path coming out of Mux3
                        temp_animations_for_wb.append(
                            {"path_id": wb_path_mux_out, "bits": [formatted_data], "duration": 0.2, "start_delay": 0.1} # After input
                        )
                        animated_signals_wb.extend(temp_animations_for_wb)
                        
                        try:
                            self.registers.write(dest_reg, data_to_write_back)
                            wb_specific_log += f"  Write Back Stage: Wrote 0x{data_to_write_back:X} to {dest_reg}.\n"
                            write_occurred = True
                        except ValueError as e:
                            raise ValueError(f"Write Back Error: {e}")
                    elif reg_write_ctrl == 1:
                         wb_specific_log += f"  Write Back: RegWrite=1 but no data/dest_reg (MemToReg={mem_to_reg_ctrl}, Dest='{dest_reg}').\n"
                
                opcode = decoded_info['opcode'] # For WB Handler Log
                handlers = INSTRUCTION_HANDLERS.get(opcode)
                if handlers and 'writeback' in handlers:
                    wb_log_handler_result = handlers['writeback'](decoded_info, control_values, alu_result_val, data_read_from_mem)
                    wb_specific_log += wb_log_handler_result.get('log', "  (No WB handler log)") + "\n"

                if not write_occurred and reg_write_ctrl == 0 :
                    wb_specific_log += "  Write Back Stage: No register write needed (RegWrite=0).\n"
                stage_log_wb += wb_specific_log

                # --- Part 2: PC Update ---
                active_blocks_wb.append("block-mux4")
                active_blocks_wb.append("block-and-gate")
                active_blocks_wb.append("block-or-gate")
                branch_signal = control_values.get('Branch', 0)
                uncond_branch_signal = control_values.get('UncondBranch', 0)
                opcode_for_debug = decoded_info.get('opcode', 'N/A')
                
                # Calculate PCSrc signal FIRST
                pc_src_signal = dpc.branch_control_logic(branch_signal, alu_zero_flag, uncond_branch_signal)

                pc_update_log = f"  PC Update Logic Input: Opcode='{opcode_for_debug}', BranchSig={branch_signal}, UncondSig={uncond_branch_signal}, ALUZero={alu_zero_flag}\n"
                final_next_pc = dpc.pc_source_mux(pc_p4, branch_target_addr_val, pc_src_signal)
                pc_update_log += f"  PC Source Mux Output: Next PC = 0x{final_next_pc:X}"
                if pc_src_signal == 1 and branch_target_addr_val != 0:
                     pc_update_log += f" (from Branch Target 0x{branch_target_addr_val:X})\n"
                elif pc_src_signal == 0:
                     pc_update_log += f" (from PC+4 Addr 0x{pc_p4:X})\n"
                stage_log_wb += pc_update_log

                # ... (Visualization for Mux4)
                path_mux4_out = "path-mux4-pc"
                active_paths_wb.append(path_mux4_out)
                mux4_in_path_vis, mux4_sel_path_vis = "", ""
                selected_input_value_for_mux4_str = ""

                if pc_src_signal == 1:
                    mux4_in_path_vis = "path-adder2-or"
                    mux4_sel_path_vis = "control-branch-enable" # Path visually representing PCSrc=1
                    selected_input_value_for_mux4_str = f"0x{branch_target_addr_val:X}"
                else: # pc_src_signal == 0
                    mux4_in_path_vis = "path-adder1-mux4-in0"
                    mux4_sel_path_vis = "control-uncondbranch-enable" # Path visually representing PCSrc=0
                    selected_input_value_for_mux4_str = f"0x{pc_p4:X}"
                
                # active_paths_wb.extend([mux4_in_path_vis])
                
                temp_animations_for_mux4 = []
                # Animate the Mux4 select signal path with the value of PCSrc
                # if mux4_sel_path_vis:
                #     temp_animations_for_mux4.append({
                #         "path_id": mux4_sel_path_vis, 
                #         "bits": [str(pc_src_signal)], 
                #         "duration": 0.1,
                #         "start_delay": 0.0
                #     })

                # # Animate the selected input path feeding into Mux4
                # if mux4_in_path_vis and selected_input_value_for_mux4_str:
                #     temp_animations_for_mux4.append({
                #         "path_id": mux4_in_path_vis,
                #         "bits": [selected_input_value_for_mux4_str],
                #         "duration": 0.1,
                #         "start_delay": 0.05 
                #     })
                
                # Animate the output path of Mux4
                temp_animations_for_mux4.extend([{
                    "path_id": path_mux4_out,
                    "bits": [f"0x{final_next_pc + DISPLAY_ADDRESS_OFFSET:X}"],
                    "duration": 0.2,
                    "start_delay": 0.1 
                },
                {
                    "path_id": "path-and-or",
                    "bits": [f"{branch_signal & alu_zero_flag}"],
                    "duration": 0.2,
                    "start_delay": 0.1 
                },
                {
                    "path_id": "path-or-mux4",
                    "bits": [f"{pc_src_signal}"],
                    "duration": 0.2,
                    "start_delay": 0.1 
                },
                ])
                animated_signals_wb.extend(temp_animations_for_mux4)

                yield MicroStepState(current_stage_name, current_micro_step_index_yield, stage_log_wb, active_blocks_wb, active_paths_wb, animated_signals_wb, control_values).to_dict()
                return {"next_pc": final_next_pc} # Normal completion
            
            except (ValueError, TypeError) as e:
                stage_log_wb += f"  Error: {e}\n traceback: {traceback.format_exc()}\n"
                yield MicroStepState(current_stage_name, current_micro_step_index_yield, stage_log_wb, active_blocks_wb, active_paths_wb, animated_signals_wb, control_values).to_dict()
                return {"next_pc": pc_p4, "error": f"Write Back / PC Update Error: {e}"}

        except StopIteration: # Should not happen if generator yields and returns correctly
            raise
        except Exception as e:
            error_msg = (f"Unexpected Runtime Error in Generator for instruction at PC=0x{current_pc_of_instruction:X} "
                         f"(Stage: {current_stage_name}, Step: {current_micro_step_index_yield}): {e}\n"
                         f"{traceback.format_exc()}")
            print(f"FATAL GENERATOR ERROR: {error_msg}")
            try:
                last_ctrl = control_values if 'control_values' in locals() else {}
                yield MicroStepState(current_stage_name, current_micro_step_index_yield, error_msg, [], [], [], last_ctrl).to_dict()
            except Exception: pass 
            return {"next_pc": current_pc_of_instruction, "error": error_msg}

    def step_micro(self):
        """
        Manages the execution of micro-steps for the current instruction.
        This replaces the core logic from the original api_micro_step.
        Returns a dictionary suitable for the Flask API response.
        """
        if not self.simulation_loaded:
            error_msg = self.error_state or 'Simulation not loaded or has ended.'
            print(f"Micro-step request rejected: {error_msg}")
            return {"status": "error", "message": error_msg, "cpu_state": self.get_cpu_state_for_api()}

        try:
            # --- Handle State Between Instructions ---
            if self.instruction_completed_flag:
                print("--- Transitioning to next instruction ---")
                self.instruction_completed_flag = False
                self.current_instruction_generator = None
                self.micro_step_index_internal = -1
                self.current_instr_addr_for_display = self.pc # PC has been updated
                try:
                    self.current_instr_str_for_display = self.raw_instruction_memory.fetch_instruction(self.pc)
                except ValueError:
                     self.current_instr_str_for_display = f"(No instruction at PC=0x{self.pc:X})"
                print(f"Ready for instruction at new PC=0x{self.pc:X}: '{self.current_instr_str_for_display}'")


            # --- Check PC Validity ---
            try:
                # Try to fetch to see if PC is valid, but don't use the instruction yet.
                # The generator will fetch the processed instruction.
                _ = self.instruction_memory.fetch_instruction(self.pc) 
            except ValueError: # No instruction at current PC
                self.simulation_loaded = False
                self.error_state = f"Program terminated: No instruction found at PC=0x{self.pc:X}"
                print(f"Execution Halt: {self.error_state}")
                return {
                    "status": "finished_program",
                    "message": self.error_state,
                    "cpu_state": self.get_cpu_state_for_api()
                }

            # --- Initialize Generator if needed ---
            if self.current_instruction_generator is None:
                # Update display info for the instruction we are *about* to execute
                self.current_instr_addr_for_display = self.pc
                try:
                    self.current_instr_str_for_display = self.raw_instruction_memory.fetch_instruction(self.pc)
                except ValueError:
                    self.current_instr_str_for_display = f"(Raw instruction missing at PC=0x{self.pc:X})"
                
                # The generator itself will fetch the processed instruction using self.pc
                # and self.instruction_memory.
                print(f"--- Creating Generator for Instruction at PC=0x{self.pc:X} ---")
                print(f"  Raw Display: '{self.current_instr_str_for_display}'")
                # Processed instruction will be fetched inside generator
                
                self.current_instruction_generator = self._execute_instruction_detailed_generator()
                self.micro_step_index_internal = -1 

            # --- Execute the next micro-step ---
            try:
                print(f"--- Executing Micro-Step {self.micro_step_index_internal + 1} ---")
                step_data_dict = next(self.current_instruction_generator)
                self.micro_step_index_internal += 1
                current_stage_name = step_data_dict.get("stage", "Unknown")
                print(f"  Generator yielded state for Stage: {current_stage_name}")

                # Add current instruction display info to the response
                step_data_dict['current_instruction_address'] = f"0x{self.current_instr_addr_for_display:X}"
                step_data_dict['current_instruction_string'] = self.current_instr_str_for_display
                
                if 'log_entry' in step_data_dict and step_data_dict['log_entry']:
                    log_lines = step_data_dict['log_entry'].strip().split('\n')
                    print("\n".join(f"    {line.strip()}" for line in log_lines))

                return {
                    "status": "success",
                    "step_data": step_data_dict,
                    "cpu_state": self.get_cpu_state_for_api(),
                    "enable_next": True
                }

            except StopIteration as e:
                # --- Instruction Completed ---
                completed_instr_str = self.current_instr_str_for_display
                completed_instr_addr = self.current_instr_addr_for_display # PC before it was updated
                print(f"--- Instruction Completed: '{completed_instr_str}' at 0x{completed_instr_addr:X} ---")
                self.instruction_completed_flag = True
                self.current_instruction_generator = None

                result = e.value if hasattr(e, 'value') and isinstance(e.value, dict) else {}
                next_pc_val = result.get('next_pc')
                error_msg_from_instr = result.get('error')

                if next_pc_val is None and not error_msg_from_instr:
                    error_msg_from_instr = "Internal Error: Generator finished without returning next_pc."
                    print(f"[ERROR] {error_msg_from_instr} for 0x{completed_instr_addr:X}")
                    next_pc_val = completed_instr_addr # Halt
                    self.simulation_loaded = False

                print(f"  Generator Result: next_pc=0x{next_pc_val:X}, error='{error_msg_from_instr}'")
                self.pc = next_pc_val # Update PC state

                if error_msg_from_instr:
                    self.error_state = f"Exec Error at 0x{completed_instr_addr:X} ('{completed_instr_str}'): {error_msg_from_instr}"
                    self.simulation_loaded = False
                    print(f"[EXECUTION HALTED] {self.error_state}")
                    return {
                        "status": "error",
                        "message": self.error_state,
                        "cpu_state": self.get_cpu_state_for_api()
                    }

                # --- Prepare for Next Instruction (No Error from current instruction) ---
                try:
                    next_instr_raw_str = self.raw_instruction_memory.fetch_instruction(self.pc)
                    print(f"  Ready for next request at PC=0x{self.pc:X}: '{next_instr_raw_str}'")
                    return {
                        "status": "instruction_completed",
                        "message": f"Instruction '{completed_instr_str}' completed. Next PC is 0x{self.pc:X}.",
                        "cpu_state": self.get_cpu_state_for_api(),
                        "next_pc": f"0x{self.pc:X}",
                        "next_instruction": next_instr_raw_str,
                        "enable_next": True,
                    }
                except ValueError: # Next PC is invalid (end of program)
                    self.simulation_loaded = False
                    final_message = (f"Program finished after 0x{completed_instr_addr:X}. "
                                     f"Next PC=0x{self.pc:X} is outside loaded memory.")
                    self.error_state = final_message
                    print(f"--- Program Finished Normally ---\n  {final_message}")
                    return {
                        "status": "finished_program",
                        "message": final_message,
                        "cpu_state": self.get_cpu_state_for_api()
                    }

        except Exception as e:
            # Catch unexpected errors in step_micro logic
            print(f"[FATAL SIMULATOR ENGINE ERROR] Unexpected error in step_micro: {e}")
            traceback.print_exc()
            self.error_state = f"Unexpected server error during micro-step: {e}"
            self.simulation_loaded = False
            return {
                "status": "error",
                "message": self.error_state,
                "cpu_state": self.get_cpu_state_for_api()
            }