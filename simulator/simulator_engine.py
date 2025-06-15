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
from .alu_mappings import get_alu_control_bits, get_alu_operation # Import ALU mappings

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

        # NEW: State history system for return back functionality
        self.state_history = []  # Store state snapshots
        self.max_history_size = 100  # Limit number of snapshots  
        self.current_history_index = -1  # Current position in history

        self.initialize_state()
    def initialize_state(self):
        """
        Reset the simulator to its initial state.
        
        This method resets all simulator components to their default values,
        preparing the simulator for a new program or restart. It clears all
        state including registers, memory, and execution tracking variables.
        
        Components Reset:
            - PC (Program Counter): Set to 0
            - Register File: All registers cleared to 0
            - Data Memory: All memory locations cleared
            - Instruction Memory: All loaded instructions removed
            - Label Table: All labels cleared
            - Execution State: All flags and generators reset
        
        Side Effects:
            - Prints confirmation message to console
            - Marks simulation as not loaded
            - Clears any error states
            - Resets all internal tracking variables
        
        Note:
            This method is automatically called by load_program_data()
            before loading new program data.
        """
        self.pc = 0
        self.registers.initialize()
        self.data_memory.initialize()
        self.instruction_memory.initialize()
        self.raw_instruction_memory.initialize()
        self.binary_instruction_memory.initialize()  # Initialize binary memory
        self.label_table = {}
        
        self.current_instruction_generator = None
        self.simulation_loaded = False
        self.error_state = None
        
        self.current_instr_addr_for_display = 0  # Default to 0
        self.current_instr_str_for_display = "(No instruction at PC=0)" 
        
        self.micro_step_index_internal = -1
        self.instruction_completed_flag = False
        print("--- Simulator engine state reset to defaults. ---")

        # Reset state history
        if not hasattr(self, 'state_history'):
            self.state_history = []
        if not hasattr(self, 'current_history_index'):
            self.current_history_index = -1
        if not hasattr(self, 'max_history_size'):
            self.max_history_size = 100
            
        self.state_history.clear()
        self.current_history_index = -1
        #self._save_state_snapshot()

    def load_program_data(self, processed_instr_dict, raw_instr_dict, labels_dict, binary_instr_dict=None):
        """
        Load a complete LEGv8 program into the simulator.
        
        This method initializes the simulator state and loads all necessary instruction
        data including processed instructions, raw user input, labels, and optional
        binary representations.
        
        Args:
            processed_instr_dict (dict): Processed/parsed instructions ready for execution
                                       Format: {address: instruction_object}
            raw_instr_dict (dict): Original user input strings for display purposes
                                 Format: {address: "original_instruction_string"}
            labels_dict (dict): Label mappings for jumps and branches
                              Format: {"label_name": address}
            binary_instr_dict (dict, optional): Binary representations of instructions
                                              Format: {address: "32bit_binary_string"}
        
        Returns:
            int: Number of instructions loaded successfully
            
        Side Effects:
            - Resets simulator state to defaults
            - Sets PC to 0 (program start)
            - Marks simulation as loaded and ready
            - Updates display info for current instruction
        """
        self.initialize_state()  # Reset before loading new program
        self.instruction_memory.load_instructions(processed_instr_dict)
        self.raw_instruction_memory.load_instructions(raw_instr_dict)  # Store raw strings
        
        # Load binary instructions if provided
        if binary_instr_dict:
            self.binary_instruction_memory.load_instructions(binary_instr_dict)
        
        self.label_table = labels_dict.copy()
        
        # Start execution at address 0
        self.pc = 0 
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
        """
        Get the current CPU state for API response.
        
        This method retrieves the complete state of the simulator including
        registers, memory, and binary instruction representation for display
        in the web interface.
        
        Returns:
            dict: Complete CPU state containing:
                - pc (str): Current program counter in hex format
                - registers (dict): All register values in ordered display format
                - data_memory (dict): Data memory contents for display
                - current_binary (str): Binary representation of current instruction
                
        Note:
            Register names are displayed in priority order: SP, FP, LR, XZR, X0-X27
        """
        # Define the order of display names for registers
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
        """
        Get binary representation of instruction at current PC.
        
        Returns:
            str: 32-bit binary string representation of the current instruction,
                 or NOP pattern if not found
        """
        try:
            return self.binary_instruction_memory.fetch_instruction(self.pc)
        except ValueError:
            return "00000000000000000000000000000000"  # Return NOP if not found

    def _execute_instruction_detailed_generator(self):
        """
        Generator that yields MicroStepState objects for instruction execution.
        
        This is the core execution engine that processes a single LEGv8 instruction
        through all 5 pipeline stages: Fetch, Decode, Execute, Memory, and Write Back.
        Each stage is yielded as a separate micro-step with visualization data.
        
        Pipeline Stages:
            0. Fetch (IF): Load instruction from memory, calculate PC+4
            1. Decode (ID): Parse instruction, read registers, generate control signals
            2. Execute (EX): Perform ALU operations, calculate branch targets
            3. Memory (MEM): Access data memory for loads/stores
            4. Write Back (WB): Write results to registers, update PC
        
        Yields:
            dict: MicroStepState data for each pipeline stage containing:
                - stage: Stage name ("Fetch", "Decode", etc.)
                - micro_step_index: Current step number (0-4)
                - log_entry: Detailed execution log
                - active_blocks: SVG components to highlight
                - active_paths: Data paths to animate
                - animated_signals: Animation data with values and timing
                - control_values: Control signal states
        
        Returns:
            dict: Final execution result containing:
                - next_pc: Address of next instruction to execute
                - error: Error message if execution failed (optional)
        
        Raises:
            StopIteration: When instruction execution completes (normal flow)
            Exception: For unexpected runtime errors during execution
        """
        # Initialize execution state variables
        current_pc_of_instruction = self.pc  # PC at the start of this instruction
        instruction_str_processed = "NOP" 
        final_next_pc = current_pc_of_instruction + 4
        pc_p4 = 0

        # Control and data flow variables
        control_values = {}
        decoded_info = {}
        exec_result = {}
        mem_result = {}

        # Register and ALU data
        read_data1, read_data2 = 0, 0
        sign_extended_imm = 0
        alu_result_val = 0  # Renamed from alu_result to avoid conflict with alu module/class
        alu_zero_flag = 0
        data_read_from_mem = None
        branch_target_addr_val = 0  # Renamed for clarity

        # Micro-step tracking
        current_stage_name = "Start"
        current_micro_step_index_yield = -1  # For MicroStepState object

        try:
            # ================================
            # STAGE 0: INSTRUCTION FETCH (IF)
            # ================================
            current_stage_name = "Fetch"
            current_micro_step_index_yield = 0
            stage_log_if = f"[{current_stage_name} @ PC=0x{current_pc_of_instruction + DISPLAY_ADDRESS_OFFSET:X}]\n"
            
            # Setup visualization components for Fetch stage
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
                stage_log_if += f"  Fetched Processed Instruction: '{instruction_str_processed}'\n"
            except ValueError as e:
                stage_log_if += f"  Error: {e}\n"
                yield MicroStepState(current_stage_name, current_micro_step_index_yield, stage_log_if, active_blocks_if, active_paths_if, animated_signals_if).to_dict()
                return {"next_pc": current_pc_of_instruction, "error": str(e)}

            # Calculate PC+4 for next sequential instruction
            pc_p4 = dpc.pc_plus_4_adder(current_pc_of_instruction)
            stage_log_if += f"  PC+4 Adder -> 0x{pc_p4:X}"
            
            # Add PC+4 path animation
            active_paths_if.append("path-adder1-mux4-in0") 
            animated_signals_if.append({"path_id": "path-adder1-mux4-in0", "bits":[f"0x{pc_p4 + DISPLAY_ADDRESS_OFFSET:X}"], "duration": 0.2, "start_delay": 0.2})
            yield MicroStepState(current_stage_name, current_micro_step_index_yield, stage_log_if, active_blocks_if, active_paths_if, animated_signals_if).to_dict()
            final_next_pc = pc_p4


            # ===================================
            # STAGE 1: INSTRUCTION DECODE (ID)
            # ===================================
            current_stage_name = "Decode"
            current_micro_step_index_yield = 1
            stage_log_id = f"[{current_stage_name}]\n"
            
            try:
                # Parse instruction opcode
                instruction_str_upper = instruction_str_processed.strip().upper()
                parts = re.split(r'[,\s()\[\]]+', instruction_str_upper)
                parts = [p for p in parts if p]
                opcode = parts[0].upper() if parts else "NOP"
                stage_log_id += f"  Opcode Detected: {opcode}\n"
            except Exception as e:
                opcode = "NOP"
                stage_log_id += f"  Error extracting opcode, defaulting to NOP: {e}\n"
            
            # Setup visualization components for Decode stage
            active_blocks_id = ["block-control", "block-regs"]
            active_paths_id = ["path-instr-control", "path-instr-alucontrol"]
            animated_signals_id = [
                #{"path_id": "path-imem-out", "bits":[f"{instruction_str_processed}"], "duration": 0.1},
                {"path_id": "path-instr-control", "bits":[f"{opcode}"], "duration": 0.2},
            ]
            
            # Safely add register and decode information with None checks
            try:
                decoded_info_temp = INSTRUCTION_HANDLERS.get(opcode, {}).get('decode', lambda x: {})(parts)
                
                # Add read_reg1_addr animation if not None
                read_reg1 = decoded_info_temp.get('read_reg1_addr')
                if read_reg1 is not None:
                    animated_signals_id.append({"path_id": "path-instr-regs", "bits":[f"{read_reg1}"], "duration":0.2})
                    active_paths_id.append("path-instr-regs")
                    
                # Add rd (destination register) animation if not None
                rd_reg = decoded_info_temp.get('rd')
                if rd_reg is not None:
                    animated_signals_id.append({"path_id": "path-instr-regwriteaddr", "bits":[f"{rd_reg}"], "duration": 0.2})
                    active_paths_id.append("path-instr-regwriteaddr")
                    
            except (KeyError, TypeError, AttributeError) as decode_err:
                print(f"Warning: Could not decode instruction parts for animation: {decode_err}")
                
            # Always add ALU control opcode animation
            animated_signals_id.append({"path_id": "path-instr-alucontrol", "bits":[f"{opcode}"], "duration": 0.2})
            # Handle Reg2Loc multiplexer for second register address
            if(self.control_unit.get_control_signals(opcode).get('ALUSrc', 0) == 0 or self.control_unit.get_control_signals(opcode).get('MemWrite') == 1):
                try:
                    decoded_info_check = INSTRUCTION_HANDLERS.get(opcode, {}).get('decode', lambda x: {})(parts)
                    read_reg2_addr = decoded_info_check.get('read_reg2_addr')
                    
                    if read_reg2_addr is not None:  # Only proceed if read_reg2_addr exists
                        if(self.control_unit.get_control_signals(opcode).get('Reg2Loc', 0)==0):
                            # Reg2Loc = 0: Use Rt field (normal register operation)
                            active_paths_id.append("path-instr-reg2loc-0")
                            animated_signals_id.append({"path_id": "path-instr-reg2loc-0", "bits":[f"{read_reg2_addr}"], "duration":0.2})
                            animated_signals_id.append({"path_id": "path-reg2loc-out", "bits":[f"{read_reg2_addr}"], "duration":0.2})
                            active_paths_id.append("path-reg2loc-out")
                        else:
                            # Reg2Loc = 1: Use Rd field (for store operations)
                            active_paths_id.append("path-instr-reg2loc-1")
                            animated_signals_id.append({"path_id": "path-instr-reg2loc-1", "bits":[f"{read_reg2_addr}"], "duration":0.2})
                            animated_signals_id.append({"path_id": "path-reg2loc-out", "bits":[f"{read_reg2_addr}"], "duration":0.2})
                            active_paths_id.append("path-reg2loc-out")
                except (KeyError, TypeError, AttributeError) as e:
                    print(f"Warning: Could not get read_reg2_addr for Reg2Loc animation: {e}")
            try:
                # Generate control signals for current instruction
                control_values = self.control_unit.get_control_signals(opcode)
                
                # Add control signal paths for visualization
                control_paths = ["control-reg2loc-enable","control-uncondbranch-enable", "control-branch-enable", 'control-memread-enable', 'control-memtoreg-enable', 'control-reg2loc-enable', 'control-aluop-enable', 'control-memwrite-enable', 'control-alusrc-enable', 'control-regwrite-enable']
                active_paths_id.extend(control_paths)
                
                # Create staggered control signal animations
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
                
                # Decode instruction using appropriate handler
                handlers = INSTRUCTION_HANDLERS.get(opcode)
                if not handlers or 'decode' not in handlers:
                    raise ValueError(f"Unsupported or missing decode handler for {opcode}")
                decode_handler = handlers['decode']
                decoded_info = decode_handler(parts)
                decoded_info['opcode'] = opcode 
                stage_log_id += decoded_info.get('log', "  (No decode log)") + "\n"
                
                # Read register values if specified
                read_reg1_addr = decoded_info.get('read_reg1_addr')
                read_reg2_addr = decoded_info.get('read_reg2_addr', None)
                if read_reg1_addr:
                    read_data1 = self.registers.read(read_reg1_addr)
                    stage_log_id += f"  Read Register 1 ({read_reg1_addr}): 0x{read_data1:X}\n"
                    # Animation for Register 1 read data output
                    active_paths_id.append("path-regs-rdata1")
                    animated_signals_id.append({"path_id": "path-regs-rdata1", "bits":[f"0x{read_data1:X}"], "duration": 0.3, "start_delay": 0.15})
                if read_reg2_addr:
                    read_data2 = self.registers.read(read_reg2_addr)
                    stage_log_id += f"  Read Register 2 ({read_reg2_addr}): 0x{read_data2:X}\n"
                    # Animation for Register 2 read data output (only if used for ALU)
                    if(self.control_unit.get_control_signals(opcode).get('ALUSrc', 0) == 0):
                        active_paths_id.append("path-regs-rdata2")
                        animated_signals_id.append({"path_id": "path-regs-rdata2", "bits":[f"0x{read_data2:X}"], "duration": 0.3, "start_delay": 0.25})
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
                        {"path_id": "path-mux2-alu", "bits":[f"0x{alu_input2_val:X}"], "duration": 0.1, "start_delay": 0.3}  # CHANGED: 0.6 → 0.8 (after read_data2 at 0.5)
                    ])
                    stage_log_id += f"  ALU Input 2 via Mux2 (ALUSrc=0): 0x{alu_input2_val:X} from Register\n"
                elif control_values.get('ALUOp', 0) != "01" and control_values.get('ALUOp', 0) != "XX":  # Use immediate data
                    # Sequential: sign_extended_imm → Mux2 → ALU
                    active_paths_id.extend(["path-signext-out-mux2", "path-mux2-alu"])
                    animated_signals_id.extend([
                        {"path_id": "path-signext-out-mux2", "bits":[f"0x{alu_input2_val:X}"], "duration": 0.3, "start_delay": 0.5},  # CHANGED: 0.5 → 0.4 (after sign extend at ~0.3)
                        {"path_id": "path-mux2-alu", "bits":[f"0x{alu_input2_val:X}"], "duration": 0.1, "start_delay": 0.2}       # CHANGED: 0.6 → 0.8 (after signext-out-mux2)
                    ])
                    stage_log_id += f"  ALU Input 2 via Mux2 (ALUSrc=1): 0x{alu_input2_val:X} from Immediate\n"
                
                branch_offset_val = decoded_info.get('branch_offset_val')
                if branch_offset_val is not None:
                    branch_offset_bits = decoded_info.get('branch_offset_bits', 0)
                    stage_log_id += f"  Branch Offset Value: {branch_offset_val} ({branch_offset_bits}b)\n"
                    # ... (update paths/signals for branch offset if any in ID)
                    if "block-signext" not in active_blocks_id: active_blocks_id.append("block-signext")
                    active_paths_id.append("path-instr-signext") 
                    animated_signals_id.append({"path_id": "path-instr-signext", "bits":[f"{(branch_offset_val)//4}"], "duration": 0.2, "start_delay": 0.1})


                yield MicroStepState(current_stage_name, current_micro_step_index_yield, stage_log_id, active_blocks_id, active_paths_id, animated_signals_id, control_values).to_dict()
            except (IndexError, ValueError, TypeError, KeyError) as e:
                stage_log_id += f"  Error: {e}\n traceback: {traceback.format_exc()}\n"
                yield MicroStepState(current_stage_name, current_micro_step_index_yield, stage_log_id, active_blocks_id, active_paths_id, animated_signals_id, control_values).to_dict()
                return {"next_pc": pc_p4, "error": f"Decode Error: {e}"}

            # ===============================
            # STAGE 2: EXECUTE (EX)
            # ===============================
            current_stage_name = "Execute"
            current_micro_step_index_yield = 2
            stage_log_ex = f"[{current_stage_name}]\n"
            
            # Setup visualization components for Execute stage
            active_blocks_ex = ["block-alu", "block-alucontrol"]
            active_paths_ex = []
            animated_signals_ex = []
            try:
                # Prepare ALU inputs
                alu_src = control_values.get('ALUSrc', 0)
                alu_input1_val = read_data1
                alu_input2_val = dpc.alu_input2_mux(read_data2, sign_extended_imm, alu_src)
                
                # Log ALU input sources and values
                reg1_source_name = decoded_info.get('read_reg1_addr', 'N/A')
                stage_log_ex += f"  ALU Input 1 (from {reg1_source_name}): 0x{alu_input1_val:X}\n"

                if alu_src == 0: 
                    reg2_source_name = decoded_info.get('read_reg2_addr','N/A')
                    stage_log_ex += f"  ALU Input 2 (from {reg2_source_name}): 0x{alu_input2_val:X} (Mux2 Sel=0)\n"
                else: 
                    stage_log_ex += f"  ALU Input 2 (from Imm): {alu_input2_val} (0x{alu_input2_val:X}) (Mux2 Sel=1)\n"

                # Execute instruction using appropriate handler
                opcode = decoded_info['opcode']
                handlers = INSTRUCTION_HANDLERS.get(opcode)
                if not handlers or 'execute' not in handlers:
                    raise ValueError(f"Missing execute handler for opcode: {opcode}")
                execute_handler = handlers['execute']
                
                # Execute with current PC for branch calculations
                exec_result = execute_handler(decoded_info, control_values, alu_input1_val, alu_input2_val, sign_extended_imm, current_pc_of_instruction)
                stage_log_ex += exec_result.get('log', "  (No execute log)") + "\n"

                # Extract execution results
                alu_result_val = exec_result.get('alu_result', 0)
                alu_zero_flag = exec_result.get('alu_zero_flag', 0)
                if opcode == "CBNZ":
                    alu_zero_flag = 1 - alu_zero_flag  # Invert zero flag for CBNZ logic
                branch_target_addr_val = exec_result.get('branch_target_addr', 0)

                # Visualize ALU control signals and results
                alu_op = control_values.get('ALUOp', 'XX')
                
                # Get ALU operation and control bits for current instruction
                current_alu_operation = get_alu_operation(opcode)
                alu_control_bits = get_alu_control_bits(current_alu_operation) if current_alu_operation else 'XXXX'

                if alu_op != 'XX' and current_alu_operation:
                    # Add ALU Control to ALU signal path
                    active_paths_ex.append("control-alucontrol-alu")
                    animated_signals_ex.append({"path_id": "control-alucontrol-alu", "bits":[alu_control_bits], "duration": 0.15, "start_delay": 0.1})
                    
                    # ALU result output (only if not going to memory)
                    if(control_values.get('MemToReg', 0) != 'X' and int(control_values.get('MemToReg', 0)) == 0):
                        active_paths_ex.append("path-alu-mux3") 
                        animated_signals_ex.append({"path_id": "path-alu-mux3", "bits":[f"0x{alu_result_val:X}"], "duration": 0.3, "start_delay": 0.2})
                    
                    # Zero flag output with instruction-specific display
                    active_paths_ex.append("path-alu-zero")
                    zero_flag_display = "ZERO"
                    if opcode == "CBNZ":
                        # For CBNZ, show "NOT ZERO" since we want to branch when NOT zero
                        zero_flag_display = "NOT ZERO" if alu_zero_flag == 1 else "ZERO"
                    
                        # For other instructions (CBZ, etc.), show normal zero flag
                        #zero_flag_display = "ZERO" if alu_zero_flag == 1 : "NOT ZERO"
                    
                    animated_signals_ex.append({"path_id": "path-alu-zero", "bits":[alu_zero_flag], "duration": 0.1, "start_delay": 0.2})
                    
                    # Add special instruction to update SVG text element for zero flag display
                    animated_signals_ex.append({
                        "path_id": "u", 
                        "bits": [zero_flag_display], 
                        "duration": 0.1, 
                        "start_delay": 0.2,
                        "svg_text_update": True,
                        "target_element_text": "Zero",  # Find element containing this text
                        "new_text": zero_flag_display
                    })

                # Handle branch target calculation visualization
                if branch_target_addr_val != 0: 
                    if "block-adder2" not in active_blocks_ex: active_blocks_ex.append("block-adder2")
                    if "block-shift-left" not in active_blocks_ex: active_blocks_ex.append("block-shift-left")
                    
                    # PC to branch adder
                    active_paths_ex.append("path-pc-adder2")
                    animated_signals_ex.append({"path_id": "path-pc-adder2", "bits":[f"0x{current_pc_of_instruction + DISPLAY_ADDRESS_OFFSET:X}"], "duration": 0.2})
                    
                    # Sign extend to shift left
                    active_paths_ex.append("path-signext-br-shift") 
                    animated_signals_ex.append({"path_id": "path-signext-br-shift", "bits":[f"0x{(branch_offset_val)//4:X}"], "duration": 0.2})
                    
                    # Shift left to branch adder
                    active_paths_ex.append("path-shift-adder2") 
                    animated_signals_ex.append({"path_id": "path-shift-adder2", "bits":[f"0x{(branch_offset_val):X}"], "duration": 0.2})
                    
                    # Branch adder to OR gate
                    active_paths_ex.append("path-adder2-or")
                    animated_signals_ex.append({"path_id": "path-adder2-or", "bits":[f"0x{branch_target_addr_val + DISPLAY_ADDRESS_OFFSET:X}"], "duration": 0.2, "start_delay": 0.2})

                yield MicroStepState(current_stage_name, current_micro_step_index_yield, stage_log_ex, active_blocks_ex, active_paths_ex, animated_signals_ex, control_values).to_dict()
            except (ValueError, TypeError) as e:
                stage_log_ex += f"  Error: {e}\n traceback: {traceback.format_exc()}\n"
                yield MicroStepState(current_stage_name, current_micro_step_index_yield, stage_log_ex, active_blocks_ex, active_paths_ex, animated_signals_ex, control_values).to_dict()
                return {"next_pc": pc_p4, "error": f"Execute Error: {e}"}

            # ===============================
            # STAGE 3: MEMORY ACCESS (MEM)
            # ===============================
            current_stage_name = "Memory"
            current_micro_step_index_yield = 3
            stage_log_mem = f"[{current_stage_name}]\n"
            
            # Setup visualization components for Memory stage
            active_blocks_mem = []
            active_paths_mem = []
            animated_signals_mem = []
            try:
                # Get memory control signals
                mem_read_ctrl = control_values.get('MemRead', 0)
                mem_write_ctrl = control_values.get('MemWrite', 0)

                # Execute memory operation using appropriate handler
                opcode = decoded_info['opcode']
                handlers = INSTRUCTION_HANDLERS.get(opcode)
                if not handlers or 'memory' not in handlers:
                    raise ValueError(f"Missing memory handler for opcode: {opcode}")
                memory_handler = handlers['memory']
                
                # Pass data memory object to the handler
                mem_result = memory_handler(decoded_info, control_values, alu_result_val, read_data2, self.data_memory)
                stage_log_mem += mem_result.get('log', "  (No memory log)") + "\n"
                data_read_from_mem = mem_result.get('data_read_from_mem')

                # Visualize memory access operations
                mem_address_for_vis = alu_result_val 

                if mem_read_ctrl == 1:
                    # Memory read operation (LDUR)
                    if "block-datamem" not in active_blocks_mem: active_blocks_mem.append("block-datamem")
                    active_paths_mem.extend(["path-alu-result"])
                    animated_signals_mem.extend([
                        {"path_id": "path-alu-result", "bits":[f"0x{mem_address_for_vis:X}"], "duration": 0.2},
                    ])
                    if data_read_from_mem is not None:
                        # Show data read from memory
                        active_paths_mem.append("path-mem-readdata")
                        animated_signals_mem.append({"path_id": "path-mem-readdata", "bits":[f"0x{data_read_from_mem:X}"], "duration": 0.3, "start_delay": 0.2})
                elif mem_write_ctrl == 1:
                    # Memory write operation (STUR)
                    if "block-datamem" not in active_blocks_mem: active_blocks_mem.append("block-datamem")
                    active_paths_mem.extend(["path-alu-result", "path-rdata2-memwrite"])
                    animated_signals_mem.extend([
                        {"path_id": "path-alu-result", "bits":[f"0x{mem_address_for_vis:X}"], "duration": 0.2},
                        {"path_id": "path-rdata2-memwrite", "bits":[f"0x{read_data2:X}"], "duration": 0.3, "start_delay": 0.1},
                    ])
                yield MicroStepState(current_stage_name, current_micro_step_index_yield, stage_log_mem, active_blocks_mem, active_paths_mem, animated_signals_mem, control_values).to_dict()
            except (ValueError, TypeError, KeyError) as e:
                stage_log_mem += f"  Error: {e}\n traceback: {traceback.format_exc()}\n"
                yield MicroStepState(current_stage_name, current_micro_step_index_yield, stage_log_mem, active_blocks_mem, active_paths_mem, animated_signals_mem, control_values).to_dict()
                return {"next_pc": pc_p4, "error": f"Memory Error: {e}"}

            # ==========================================
            # STAGE 4: WRITE BACK (WB) & PC UPDATE
            # ==========================================
            current_stage_name = "Write Back / PC Update"
            current_micro_step_index_yield = 4
            stage_log_wb = f"[{current_stage_name}]\n"
            
            # Setup visualization components for Write Back stage
            active_blocks_wb = [] 
            active_paths_wb = []
            animated_signals_wb = []
            try:
                # ========================================
                # Part 1: Write Back to Register File
                # ========================================
                reg_write_ctrl = control_values.get('RegWrite', 0)
                mem_to_reg_ctrl = control_values.get('MemToReg', 0)
                data_to_write_back = None
                write_occurred = False
                wb_specific_log = ""

                if reg_write_ctrl == 1:
                    # Activate Mux3 for writeback data selection
                    active_blocks_wb.append("block-mux3")
                    data_to_write_back = dpc.writeback_data_mux(alu_result_val, data_read_from_mem, mem_to_reg_ctrl)
                    dest_reg = decoded_info.get('rd') or decoded_info.get('rt')

                    if data_to_write_back is not None and dest_reg:
                        wb_specific_log += f"  Write Back Stage: RegWrite=1 for {dest_reg}.\n"
                        
                        # Setup writeback data path visualization
                        wb_path_mux_out = "path-mux3-wb"  
                        active_paths_wb.extend([wb_path_mux_out])

                        # Determine data source for logging
                        if mem_to_reg_ctrl == 0: 
                            wb_specific_log += f"  Write Back Stage: Mux3 selects ALU Result (0x{data_to_write_back:X}).\n"
                        elif mem_to_reg_ctrl == 1: 
                            wb_specific_log += f"  Write Back Stage: Mux3 selects Memory Data (0x{data_to_write_back:X}).\n"
                        
                        # Format data for animation
                        formatted_data = f"0x{data_to_write_back:X}" if isinstance(data_to_write_back, int) else str(data_to_write_back)

                        # Animation for the output path of Mux3 (shows data_to_write_back)
                        animated_signals_wb.append({
                            "path_id": wb_path_mux_out, 
                            "bits": [formatted_data], 
                            "duration": 0.2, 
                            "start_delay": 0.1
                        })
                        
                        # Perform the actual register write
                        try:
                            self.registers.write(dest_reg, data_to_write_back)
                            wb_specific_log += f"  Write Back Stage: Wrote 0x{data_to_write_back:X} to {dest_reg}.\n"
                            write_occurred = True
                        except ValueError as e:
                            raise ValueError(f"Write Back Error: {e}")
                    elif reg_write_ctrl == 1:
                         wb_specific_log += f"  Write Back: RegWrite=1 but no data/dest_reg (MemToReg={mem_to_reg_ctrl}, Dest='{dest_reg}').\n"
                
                # Execute writeback handler for additional logging
                opcode = decoded_info['opcode']
                handlers = INSTRUCTION_HANDLERS.get(opcode)
                if handlers and 'writeback' in handlers:
                    wb_log_handler_result = handlers['writeback'](decoded_info, control_values, alu_result_val, data_read_from_mem)
                    wb_specific_log += wb_log_handler_result.get('log', "  (No WB handler log)") + "\n"

                if not write_occurred and reg_write_ctrl == 0:
                    wb_specific_log += "  Write Back Stage: No register write needed (RegWrite=0).\n"
                stage_log_wb += wb_specific_log

                # ========================================
                # Part 2: PC Update Logic
                # ========================================
                active_blocks_wb.extend(["block-mux4", "block-and-gate", "block-or-gate"])
                branch_signal = control_values.get('Branch', 0)
                uncond_branch_signal = control_values.get('UncondBranch', 0)
                opcode_for_debug = decoded_info.get('opcode', 'N/A')
                
                # Calculate PCSrc signal for PC source selection
                pc_src_signal = dpc.branch_control_logic(branch_signal, alu_zero_flag, uncond_branch_signal)

                # Log PC update logic inputs and results
                pc_update_log = f"  PC Update Logic Input: Opcode='{opcode_for_debug}', BranchSig={branch_signal}, UncondSig={uncond_branch_signal}, ALUZero={alu_zero_flag}\n"
                final_next_pc = dpc.pc_source_mux(pc_p4, branch_target_addr_val, pc_src_signal)
                pc_update_log += f"  PC Source Mux Output: Next PC = 0x{final_next_pc:X}"
                if pc_src_signal == 1 and branch_target_addr_val != 0:
                     pc_update_log += f" (from Branch Target 0x{branch_target_addr_val:X})\n"
                elif pc_src_signal == 0:
                     pc_update_log += f" (from PC+4 Addr 0x{pc_p4:X})\n"
                stage_log_wb += pc_update_log

                # Visualize PC update logic
                active_paths_wb.extend(["path-and-or", "path-or-mux4", "path-mux4-pc"])
                
                # Animate PC update components
                animated_signals_wb.extend([
                    {
                        "path_id": "path-mux4-pc",
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

                yield MicroStepState(current_stage_name, current_micro_step_index_yield, stage_log_wb, active_blocks_wb, active_paths_wb, animated_signals_wb, control_values).to_dict()
                return {"next_pc": final_next_pc}  # Normal completion
            
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
        Execute a single micro-step of the current instruction.
        
        This method manages the state machine for instruction execution, handling
        transitions between instructions and coordinating with the instruction
        generator for micro-step execution.
        
        State Management:
            - Checks simulation status and PC validity
            - Initializes instruction generator when needed
            - Handles instruction completion and PC updates
            - Manages transitions between instructions
        
        Returns:
            dict: API response containing:
                - status (str): "success", "error", "instruction_completed", or "finished_program"
                - message (str): Status description or error message
                - step_data (dict, optional): MicroStepState data for visualization
                - cpu_state (dict): Current CPU state
                - enable_next (bool, optional): Whether next step is available
                - next_pc (str, optional): Next program counter value
                - next_instruction (str, optional): Next instruction string
        
        Error Handling:
            - Validates simulation state before execution
            - Catches and reports instruction execution errors
            - Handles end-of-program conditions gracefully
            - Provides detailed error messages for debugging
        
        Side Effects:
            - Updates PC when instruction completes
            - Modifies internal state machine variables
            - May terminate simulation on errors or program end
        """
        # Lưu snapshot trước khi thực hiện step - CHỈ Ở ĐẦU INSTRUCTION
        print(f"📸 Checking if should save snapshot...")
        current_micro_step = getattr(self, 'micro_step_index_internal', -1)
        print(f"📸 Current micro step: {current_micro_step}")
        
        # CHỈ save snapshot khi bắt đầu instruction mới (micro_step_index_internal == -1)
        if current_micro_step == 0:
            print(f"📸 Saving instruction-level snapshot before starting new instruction")
            self._save_state_snapshot()
        else:
            print(f"📸 Skipping snapshot - already in instruction (micro step {current_micro_step})")

        if not self.simulation_loaded:
            error_msg = self.error_state or 'Simulation not loaded or has ended.'
            print(f"Micro-step request rejected: {error_msg}")
            return {"status": "error", "message": error_msg, "cpu_state": self.get_cpu_state_for_api()}

        try:
            # Handle state transitions between instructions
            if self.instruction_completed_flag:
                print("--- Transitioning to next instruction ---")
                
                # QUAN TRỌNG: Save snapshot khi instruction hoàn thành, trước khi move to next
                print(f"📸 Instruction completed - preparing for next instruction")
                
                self.instruction_completed_flag = False
                self.current_instruction_generator = None
                self.micro_step_index_internal = -1
                self.current_instr_addr_for_display = self.pc  # PC has been updated
                try:
                    self.current_instr_str_for_display = self.raw_instruction_memory.fetch_instruction(self.pc)
                except ValueError:
                     self.current_instr_str_for_display = f"(No instruction at PC=0x{self.pc:X})"
                print(f"Ready for instruction at new PC=0x{self.pc:X}: '{self.current_instr_str_for_display}'")

            # Validate current PC before proceeding
            try:
                # Check if PC points to a valid instruction
                _ = self.instruction_memory.fetch_instruction(self.pc) 
            except ValueError:  # No instruction at current PC
                self.simulation_loaded = False
                self.error_state = f"Program terminated: No instruction found at PC=0x{self.pc:X}"
                print(f"Execution Halt: {self.error_state}")
                return {
                    "status": "finished_program",
                    "message": self.error_state,
                    "cpu_state": self.get_cpu_state_for_api()
                }

            # Initialize instruction generator if needed
            if self.current_instruction_generator is None:
                # Update display info for the instruction about to execute
                self.current_instr_addr_for_display = self.pc
                try:
                    self.current_instr_str_for_display = self.raw_instruction_memory.fetch_instruction(self.pc)
                except ValueError:
                    self.current_instr_str_for_display = f"(Raw instruction missing at PC=0x{self.pc:X})"
                
                print(f"--- Creating Generator for Instruction at PC=0x{self.pc:X} ---")
                print(f"  Raw Display: '{self.current_instr_str_for_display}'")
                
                self.current_instruction_generator = self._execute_instruction_detailed_generator()
                self.micro_step_index_internal = -1 

            # Execute the next micro-step
            try:
                print(f"--- Executing Micro-Step {self.micro_step_index_internal + 1} ---")
                step_data_dict = next(self.current_instruction_generator)
                self.micro_step_index_internal += 1
                current_stage_name = step_data_dict.get("stage", "Unknown")
                print(f"  Generator yielded state for Stage: {current_stage_name}")

                # Add current instruction display info to the response
                step_data_dict['current_instruction_address'] = f"0x{self.current_instr_addr_for_display:X}"
                step_data_dict['current_instruction_string'] = self.current_instr_str_for_display
                
                # Log execution details to console
                if 'log_entry' in step_data_dict and step_data_dict['log_entry']:
                    log_lines = step_data_dict['log_entry'].strip().split('\n')
                    print("\n".join(f"    {line.strip()}" for line in log_lines))

                return {
                    "status": "success",
                    "step_data": step_data_dict,
                    "cpu_state": self.get_cpu_state_for_api(),
                    "enable_next": True,
                    "can_return_back": self.can_return_back()
                }

            except StopIteration as e:
                # Instruction execution completed
                completed_instr_str = self.current_instr_str_for_display
                completed_instr_addr = self.current_instr_addr_for_display  # PC before it was updated
                print(f"--- Instruction Completed: '{completed_instr_str}' at 0x{completed_instr_addr:X} ---")
                self.instruction_completed_flag = True
                self.current_instruction_generator = None

                # Extract results from generator
                result = e.value if hasattr(e, 'value') and isinstance(e.value, dict) else {}
                next_pc_val = result.get('next_pc')
                error_msg_from_instr = result.get('error')

                # Validate generator results
                if next_pc_val is None and not error_msg_from_instr:
                    error_msg_from_instr = "Internal Error: Generator finished without returning next_pc."
                    print(f"[ERROR] {error_msg_from_instr} for 0x{completed_instr_addr:X}")
                    next_pc_val = completed_instr_addr  # Halt execution
                    self.simulation_loaded = False

                print(f"  Generator Result: next_pc=0x{next_pc_val:X}, error='{error_msg_from_instr}'")
                self.pc = next_pc_val  # Update PC state

                # Handle execution errors
                if error_msg_from_instr:
                    self.error_state = f"Exec Error at 0x{completed_instr_addr:X} ('{completed_instr_str}'): {error_msg_from_instr}"
                    self.simulation_loaded = False
                    print(f"[EXECUTION HALTED] {self.error_state}")
                    return {
                        "status": "error",
                        "message": self.error_state,
                        "cpu_state": self.get_cpu_state_for_api()
                    }

                # Prepare for next instruction (no error from current instruction)
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
                        "can_return_back": self.can_return_back()
                    }
                except ValueError:  # Next PC is invalid (end of program)
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
        
    def _save_state_snapshot(self):
        """Lưu snapshot trạng thái hiện tại vào lịch sử"""
        print("sdf")
        try:
            # CHỈ lưu snapshot ở ĐẦUE instruction (micro step = -1 hoặc 0)
            current_micro_step = getattr(self, 'micro_step_index_internal', -1)
            
            # Chỉ save khi bắt đầu instruction mới (trước micro step đầu tiên)
            if current_micro_step >0:
                print(f"📸 Skipping snapshot save - in middle of instruction (micro step {current_micro_step})")
                return
            
            print(f"📸 Saving instruction-level snapshot (before micro steps)")
            
            # Handle registers properly - check if it's RegisterFile object or dict
            registers_data = {}
            if hasattr(self, 'registers') and self.registers:
                if hasattr(self.registers, 'get_all_registers'):
                    # Get raw register values (not formatted hex strings)
                    registers_data = self.registers.get_all_registers()
                    print(f"📸 Got registers via get_all_registers(): {list(registers_data.items())[:3]}")
                elif hasattr(self.registers, 'get_raw_registers'):
                    # Alternative method name
                    registers_data = self.registers.get_raw_registers()
                    print(f"📸 Got registers via get_raw_registers(): {list(registers_data.items())[:3]}")
                elif hasattr(self.registers, '__dict__'):
                    # Fallback: serialize object attributes, but get raw values
                    registers_data = {}
                    for attr in dir(self.registers):
                        if not attr.startswith('_') and not callable(getattr(self.registers, attr)):
                            try:
                                value = getattr(self.registers, attr)
                                if isinstance(value, (int, float)):
                                    registers_data[attr] = int(value)  # Store as int, not string
                                elif isinstance(value, str) and value.startswith('0x'):
                                    registers_data[attr] = int(value, 16)  # Parse hex string to int
                                elif isinstance(value, (list, dict)):
                                    registers_data[attr] = value
                            except:
                                pass
                    print(f"📸 Got registers via __dict__ scan: {list(registers_data.items())[:3]}")
                elif isinstance(self.registers, dict):
                    # Make sure we store int values, not hex strings
                    registers_data = {}
                    for reg_name, reg_value in self.registers.items():
                        if isinstance(reg_value, str) and reg_value.startswith('0x'):
                            registers_data[reg_name] = int(reg_value, 16)
                        else:
                            registers_data[reg_name] = int(reg_value) if isinstance(reg_value, (int, str)) else reg_value
                    print(f"📸 Got registers via dict conversion: {list(registers_data.items())[:3]}")
                else:
                    print(f"Warning: Unknown registers type: {type(self.registers)}")
                    registers_data = {}
            
            # Handle memory - use helper method
            memory_data = self.get_memory_backup()
            import copy
            snapshot = {
                'pc': getattr(self, 'pc', 0),
                'registers': copy.deepcopy(self.registers),
                'memory_data': memory_data,
                'current_instr_addr_for_display': getattr(self, 'current_instr_addr_for_display', 0),
                'current_instr_str_for_display': getattr(self, 'current_instr_str_for_display', ''),
                'micro_step_index': getattr(self, 'micro_step_index_internal', -1),
                'execution_finished': getattr(self, 'execution_finished', False),
                'is_running': getattr(self, 'is_running', False),
                'execution_stage_name': getattr(self, 'execution_stage_name', ''),
                'label_table': getattr(self, 'label_table', {}).copy() if hasattr(self, 'label_table') and isinstance(getattr(self, 'label_table', {}), dict) else {}
            }
            
            # Print snapshot summary
            print(f"📸 SNAPSHOT SUMMARY:")
            print(f"📸   PC: 0x{snapshot['pc']:X}")
            #print(f"📸   Registers: {(snapshot['registers'])} entries")
            # if snapshot['registers']:
            #     sample_regs = list(snapshot['registers'].items())[:3]
            #     for reg_name, reg_val in sample_regs:
            #         print(f"📸     {reg_name}: 0x{reg_val:X}" if isinstance(reg_val, int) else f"📸     {reg_name}: {reg_val}")
            # print(f"📸   Memory: {len(snapshot['memory_data'])} memory sections")
            # for mem_type, mem_data in snapshot['memory_data'].items():
            #     if mem_data:
            #         print(f"📸     {mem_type}: {len(mem_data)} entries")
            # print(f"📸   Instruction: {snapshot['current_instr_str_for_display']}")
            # print(f"📸   Micro step: {snapshot['micro_step_index']}")
            
            # Nếu đang ở giữa lịch sử (do return back), xóa các snapshot sau vị trí hiện tại
            if self.current_history_index < len(self.state_history) - 1:
                removed_count = len(self.state_history) - self.current_history_index - 1
                self.state_history = self.state_history[:self.current_history_index + 1]
                print(f"📸 Cleared {removed_count} future snapshots due to new step")
            
            # Thêm snapshot mới
            self.state_history.append(snapshot)
            self.current_history_index = len(self.state_history) - 1
            
            # Giới hạn kích thước lịch sử
            if len(self.state_history) > self.max_history_size:
                self.state_history.pop(0)
                self.current_history_index -= 1
                
            print(f"📸 State snapshot saved. History size: {len(self.state_history)}, Current index: {self.current_history_index}")
            print(f"📸 Can return back after save: {self.can_return_back()}")
            
        except Exception as e:
            print(f"Error saving state snapshot: {e}")
            import traceback
            traceback.print_exc()

    # Helper method to ensure get_memory_backup exists and works
    def ensure_memory_backup_methods(self):
        """Ensure memory backup methods are available"""
        if not hasattr(self, 'get_memory_backup'):
            print("ERROR: get_memory_backup method not found!")
            return False
        if not hasattr(self, '_backup_memory_object'):
            print("ERROR: _backup_memory_object method not found!")  
            return False
        if not hasattr(self, 'restore_memory_backup'):
            print("ERROR: restore_memory_backup method not found!")
            return False
        return True
    
    # Override _save_state_snapshot to ensure methods exist
    def _save_state_snapshot_safe(self):
        """Safe version of _save_state_snapshot with method checking"""
        try:
            # Check methods exist - try direct call first
            try:
                memory_data = self.get_memory_backup()
            except AttributeError:
                print("Warning: get_memory_backup method missing, using fallback")
                memory_data = {}
            
            # Handle registers safely
            registers_data = {}
            if hasattr(self, 'registers') and self.registers:
                if hasattr(self.registers, 'get_all_registers'):
                    registers_data = self.registers.get_all_registers()
                elif hasattr(self.registers, '__dict__'):
                    registers_data = {}
                    for attr in dir(self.registers):
                        if not attr.startswith('_') and not callable(getattr(self.registers, attr)):
                            try:
                                value = getattr(self.registers, attr)
                                if isinstance(value, (int, float, str, list, dict)):
                                    registers_data[attr] = value
                            except:
                                pass
                elif isinstance(self.registers, dict):
                    registers_data = self.registers.copy()
            
            snapshot = {
                'pc': getattr(self, 'pc', 0),
                'registers': registers_data,
                'memory_data': memory_data,
                'current_instr_addr_for_display': getattr(self, 'current_instr_addr_for_display', 0),
                'current_instr_str_for_display': getattr(self, 'current_instr_str_for_display', ''),
                'micro_step_index': getattr(self, 'micro_step_index_internal', getattr(self, 'micro_step_index', -1)),
                'execution_finished': getattr(self, 'execution_finished', False),
                'is_running': getattr(self, 'is_running', False),
                'execution_stage_name': getattr(self, 'execution_stage_name', ''),
                'label_table': getattr(self, 'label_table', {}).copy() if hasattr(self, 'label_table') and isinstance(getattr(self, 'label_table', {}), dict) else {}
            }
            
            # Manage history
            if self.current_history_index < len(self.state_history) - 1:
                self.state_history = self.state_history[:self.current_history_index + 1]
            
            self.state_history.append(snapshot)
            self.current_history_index = len(self.state_history) - 1
            
            if len(self.state_history) > self.max_history_size:
                self.state_history.pop(0)
                self.current_history_index -= 1
                
            print(f"📸 State snapshot saved safely. History size: {len(self.state_history)}, Index: {self.current_history_index}")
            
        except Exception as e:
            print(f"Error saving state snapshot: {e}")
            import traceback
            traceback.print_exc()

    # Updated step_micro to use safe snapshot
    def step_micro_with_snapshot(self):
        """Step micro with safe state snapshot"""
        # Save snapshot safely before step
        self._save_state_snapshot_safe()
        
        # Continue with original step_micro implementation
        # This should call the actual step_micro logic
        
        # Return with can_return_back info
        return {
            "status": "success",
            "message": "Micro step completed", 
            "can_return_back": self.can_return_back()
        }
    
    def can_return_back(self):
        """Kiểm tra có thể return back về instruction trước đó không"""
        # Cần có ít nhất 1 instruction snapshot trong history
        has_history = hasattr(self, 'current_history_index') and hasattr(self, 'state_history')
        
        if not has_history:
            print(f"🔙 Can return back: NO - No history system")
            return False
            
        # Cần có ít nhất 1 instruction trước đó (index > 0)
        has_previous_instruction = self.current_history_index > 0
        
        # Log detailed info
        history_size = len(self.state_history) if hasattr(self, 'state_history') else 0
        current_index = self.current_history_index if hasattr(self, 'current_history_index') else -1
        
        print(f"🔙 Can return back check: history_size={history_size}, current_index={current_index}, can_return={has_previous_instruction}")
        
        return has_previous_instruction

    # ===== MEMORY BACKUP METHODS =====
    def get_memory_backup(self):
        """Helper method to backup memory data from various possible attributes"""
        memory_backup = {}
        
        # Backup data_memory (chính)
        if hasattr(self, 'data_memory') and self.data_memory:
            memory_backup['data_memory'] = copy.deepcopy(self.data_memory)
        
        # Backup instruction_memory nếu tồn tại riêng biệt
        if hasattr(self, 'instruction_memory') and self.instruction_memory:
            memory_backup['instruction_memory'] = self._backup_memory_object(self.instruction_memory)
        
        # Backup raw_instruction_memory
        if hasattr(self, 'raw_instruction_memory') and self.raw_instruction_memory:
            memory_backup['raw_instruction_memory'] = self._backup_memory_object(self.raw_instruction_memory)
        
        # Backup binary_instruction_memory
        if hasattr(self, 'binary_instruction_memory') and self.binary_instruction_memory:
            memory_backup['binary_instruction_memory'] = self._backup_memory_object(self.binary_instruction_memory)
            
        return memory_backup

    def _backup_memory_object(self, memory_obj):
        """Helper method to safely backup a memory object"""
        if not memory_obj:
            return {}
        import copy
        try:
            if hasattr(memory_obj, 'get_raw_memory'):
                return memory_obj.get_raw_memory()
            elif hasattr(memory_obj, 'memory') and isinstance(memory_obj.memory, dict):
                return copy.deepcoy(memory_obj.memory)
            elif isinstance(memory_obj, dict):
                return copy.deepcoy(memory_obj)
            else:
                print(f"Warning: Unknown memory object type: {type(memory_obj)}")
                return {}
        except Exception as e:
            print(f"Error backing up memory object: {e}")
            return {}

    def restore_memory_backup(self, memory_backup):
        """Helper method to restore memory data to various possible attributes"""
        if not memory_backup:
            return
            
        try:
            # Restore data_memory
            if 'data_memory' in memory_backup and hasattr(self, 'data_memory'):
                self._restore_memory_object(self.data_memory, memory_backup['data_memory'])
            
            # Restore instruction_memory
            if 'instruction_memory' in memory_backup and hasattr(self, 'instruction_memory'):
                self._restore_memory_object(self.instruction_memory, memory_backup['instruction_memory'])
            
            # Restore raw_instruction_memory
            if 'raw_instruction_memory' in memory_backup and hasattr(self, 'raw_instruction_memory'):
                self._restore_memory_object(self.raw_instruction_memory, memory_backup['raw_instruction_memory'])
            
            # Restore binary_instruction_memory
            if 'binary_instruction_memory' in memory_backup and hasattr(self, 'binary_instruction_memory'):
                self._restore_memory_object(self.binary_instruction_memory, memory_backup['binary_instruction_memory'])
                
        except Exception as e:
            print(f"Warning: Could not restore memory backup: {e}")

    def _restore_memory_object(self, memory_obj, backup_data):
        """Helper method to safely restore a memory object"""
        if not memory_obj or not backup_data:
            return
        
        try:
            if hasattr(memory_obj, 'set_raw_memory'):
                memory_obj.set_raw_memory(backup_data)
            elif hasattr(memory_obj, 'memory') and isinstance(memory_obj.memory, dict):
                memory_obj.memory.clear()
                memory_obj.memory.update(backup_data)
            elif isinstance(memory_obj, dict):
                memory_obj.clear()
                memory_obj.update(backup_data)
            else:
                print(f"Warning: Cannot restore memory object type: {type(memory_obj)}")
        except Exception as e:
            print(f"Error restoring memory object: {e}")

    def _restore_state_snapshot_fixed(self, snapshot):
        """Khôi phục trạng thái từ snapshot - Fixed version"""
        try:
            print(f"🔄 ===== STARTING STATE RESTORATION =====")
            print(f"🔄 Snapshot contains keys: {list(snapshot.keys())}")
            
            # Restore basic attributes safely
            if 'pc' in snapshot:
                old_pc = getattr(self, 'pc', 0)
                self.pc = snapshot['pc']
                print(f"🔄 PC: 0x{old_pc:X} → 0x{self.pc:X}")
            
            # Restore display attributes
            restore_attrs = ['pc', 'memory_data', 'registers', 'current_instr_addr_for_display', 'current_instr_str_for_display', 'micro_step_index', 'execution_finished', 'is_running', 'execution_stage_name', 'label_table']
            for attr_name in restore_attrs:
                if attr_name in snapshot:
                    old_value = getattr(self, attr_name, 'N/A')
                    # if attr_name == 'memory_data':
                    #     old_value = old_value['data_memory']
                    new_value = snapshot[attr_name]
                    setattr(self, attr_name, new_value)
                    print(f"🔄 {attr_name}: {old_value} → {new_value}")
            
            # Handle micro_step_index with detailed logging
            if 'micro_step_index' in snapshot:
                if hasattr(self, 'micro_step_index_internal'):
                    old_index = self.micro_step_index_internal
                    self.micro_step_index_internal = snapshot['micro_step_index']
                    print(f"🔄 micro_step_index_internal: {old_index} → {self.micro_step_index_internal}")
                else:
                    old_index = getattr(self, 'micro_step_index', -1)
                    self.micro_step_index = snapshot['micro_step_index']
                    print(f"🔄 micro_step_index: {old_index} → {self.micro_step_index}")
            
            # Handle registers restoration properly with detailed logging
            if 'registers' in snapshot:
                registers_data = snapshot['registers']
                # print(f"🔄 Restoring {len(registers_data)} registers from snapshot")
                # print(f"🔄 Sample register data: {list(registers_data.items())[:3]}")  # Show first 3 registers
                
                if hasattr(self, 'registers') and self.registers:
                    # Check what methods are available on register file
                    register_methods = [method for method in dir(self.registers) if not method.startswith('_')]
                    print(f"🔄 Available register methods: {register_methods}")
                    self.registers = registers_data
                    # if hasattr(self.registers, 'restore_all_registers'):
                    #     print("🔄 Using restore_all_registers method")
                    #     self.registers.restore_all_registers(registers_data)
                    # elif hasattr(self.registers, 'set_all_registers'):
                    #     print("🔄 Using set_all_registers method")
                    #     self.registers.set_all_registers(registers_data)
                    # else:
                    #     print("🔄 Using manual register restoration")
                    #     # Manual restoration - iterate through register data
                    #     restored_count = 0
                    #     for reg_name, reg_value in registers_data.items():
                    #         try:
                    #             # Show BEFORE value
                    #             old_value = self.registers.read(reg_name) if hasattr(self.registers, 'read') else 'N/A'
                    #             print(f"🔄 BEFORE: {reg_name} = 0x{old_value:X}" if isinstance(old_value, int) else f"🔄 BEFORE: {reg_name} = {old_value}")
                                
                    #             # Convert value to int if needed
                    #             if isinstance(reg_value, str) and reg_value.startswith('0x'):
                    #                 reg_value = int(reg_value, 16)
                    #             elif isinstance(reg_value, str):
                    #                 reg_value = int(reg_value)
                    #             elif not isinstance(reg_value, int):
                    #                 reg_value = int(reg_value)
                                
                    #             # Write to register using the standard write method
                    #             self.registers.write(reg_name, reg_value)
                                
                    #             # Show AFTER value
                    #             new_value = self.registers.read(reg_name) if hasattr(self.registers, 'read') else 'N/A'
                    #             print(f"🔄 AFTER:  {reg_name} = 0x{new_value:X} (restored from 0x{reg_value:X})")
                                
                    #             restored_count += 1
                    #         except Exception as e:
                    #             print(f"⚠️ Could not restore register {reg_name} (value: {reg_value}): {e}")
                        
                        # print(f"🔄 Successfully restored {restored_count}/{len(registers_data)} registers")
                print(f"🔄 Registers restoration completed")
            
            # Restore memory data
            if 'memory_data' in snapshot and snapshot['memory_data']:
                print(f"🔄 Restoring memory data...")
                memory_data = snapshot['memory_data']
                print(f"🔄 Memory backup contains: {list(memory_data.keys())}")
                
                # Show some memory data before restore
                if hasattr(self, 'data_memory') and self.data_memory:
                    current_memory = self.data_memory.get_display_dict()
                    print(f"🔄 BEFORE memory restore: {len(current_memory)} entries")
                    if current_memory:
                        sample_entries = list(current_memory.items())[:3]
                        for addr, value in sample_entries:
                            print(f"🔄 BEFORE: Mem[{addr}] = {value}")
                
                #self.restore_memory_backup(snapshot['memory_data'])
                self.data_memory = snapshot['memory_data']['data_memory']
                # Show memory data after restore
                if hasattr(self, 'data_memory') and self.data_memory:
                    restored_memory = self.data_memory.get_display_dict()
                    print(f"🔄 AFTER memory restore: {len(restored_memory)} entries")
                    if restored_memory:
                        sample_entries = list(restored_memory.items())[:3]
                        for addr, value in sample_entries:
                            print(f"🔄 AFTER: Mem[{addr}] = {value}")
            else:
                print(f"🔄 No memory data to restore")
            
            # Restore other attributes
            restore_attrs = ['current_instr_addr_for_display', 'current_instr_str_for_display', 
                           'execution_finished', 'execution_stage_name']
            for attr_name in restore_attrs:
                if attr_name in snapshot:
                    setattr(self, attr_name, snapshot[attr_name])
            
            # Handle micro_step_index
            if 'micro_step_index' in snapshot:
                if hasattr(self, 'micro_step_index_internal'):
                    self.micro_step_index_internal = snapshot['micro_step_index']
                else:
                    self.micro_step_index = snapshot['micro_step_index']
            
            # Reset state for return back
            self.simulation_loaded = True
            self.error_state = None
            if hasattr(self, 'current_instruction_generator'):
                self.current_instruction_generator = None
            if hasattr(self, 'instruction_completed_flag'):
                self.instruction_completed_flag = False
            
            # Restore label table
            if 'label_table' in snapshot and hasattr(self, 'label_table'):
                self.label_table = snapshot['label_table'].copy()
                
            print(f"🔄 ===== STATE RESTORATION COMPLETED =====")
            print(f"🔄 Final PC: 0x{self.pc:X}")
            print(f"🔄 Final instruction: {getattr(self, 'current_instr_str_for_display', 'N/A')}")
            print(f"🔄 Final micro step: {getattr(self, 'micro_step_index_internal', -1)}")
            
            # Show final register sample
            if hasattr(self, 'registers') and self.registers:
                print(f"🔄 Final register sample:")
                try:
                    for reg_name in ['X0', 'X1', 'X2', 'SP']:
                        if hasattr(self.registers, 'read'):
                            reg_val = self.registers.read(reg_name)
                            print(f"🔄   {reg_name}: 0x{reg_val:X}")
                except:
                    print(f"🔄   (Could not read sample registers)")
            
            # QUAN TRỌNG: Force cập nhật lại tất cả state sau restore
            print(f"🔄 Forcing state refresh after restore...")
            
        except Exception as e:
            print(f"❌ ERROR restoring state snapshot: {e}")
            import traceback
            traceback.print_exc()
            raise

    def return_back(self):
        """Wrapper for instruction-level return back"""
        return self.return_back_to_previous_instruction()

    def return_back_to_previous_instruction(self):
        """Trở lại instruction trước đó (về đầu instruction, không phải micro step)"""
        try:
            print(f"🔙 Return back to previous instruction requested. Current history: {self.current_history_index}/{len(self.state_history)-1}")
            
            if not self.can_return_back():
                print(f"🔙 Cannot return back - no previous instruction available")
                return {
                    "status": "error",
                    "message": "Cannot return back - no previous instruction available"
                }
                
            # Di chuyển về instruction trước đó (mỗi snapshot = 1 instruction)
            previous_index = self.current_history_index
            
            snapshot = self.state_history[self.current_history_index]
            self.current_history_index -= 1
            print(f"🔙 Moving from instruction {previous_index} to instruction {self.current_history_index}")
            print(f"🔙 Restoring to beginning of instruction with PC: 0x{snapshot.get('pc', 0):X}")
            print(f"🔙 Target instruction: {snapshot.get('current_instr_str_for_display', 'N/A')}")
            
            # Khôi phục trạng thái về đầu instruction
            self._restore_state_snapshot_fixed(snapshot)
            
            # ĐẶT LẠI VỀ TRẠNG THÁI ĐẦU INSTRUCTION
            self.micro_step_index_internal = -1  # Reset về trước micro step đầu tiên
            self.instruction_completed_flag = False
            self.current_instruction_generator = None  # Reset generator
            
            print(f"🔙 Reset to beginning of instruction - micro step index: {self.micro_step_index_internal}")
            
            # Force refresh CPU state after restore
            print(f"🔙 Getting fresh CPU state after restore...")
            fresh_cpu_state = self.get_cpu_state_for_api()
            
            result = {
                "status": "success",
                "message": f"Returned to beginning of previous instruction (instruction {self.current_history_index + 1}/{len(self.state_history)})",
                "cpu_state": fresh_cpu_state,
                "current_instr_addr": f"0x{self.current_instr_addr_for_display:X}",
                "current_instr_str": self.current_instr_str_for_display,
                "micro_step_info": f"Ready to start instruction (0/5)",
                "can_return_back": self.can_return_back(),
                "step_data": {
                    "current_instruction_address": self.current_instr_addr_for_display,
                    "current_instruction_string": self.current_instr_str_for_display,
                    "micro_step_index": -1,
                    "stage": "Ready",
                    "active_blocks": [],
                    "active_paths": [],
                    "control_signals": {}
                }
            }
            
            print(f"🔙 Return back successful. At beginning of instruction. Can return back again: {self.can_return_back()}")
            return result
            
        except Exception as e:
            print(f"Error in return_back: {e}")
            import traceback
            traceback.print_exc()
            return {
                "status": "error",
                "message": f"Error returning to previous instruction: {str(e)}"
            }