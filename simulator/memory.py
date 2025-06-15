# -*- coding: utf-8 -*-

class Memory:
    def __init__(self, memory_type="data"):
        self.memory = {}
        self.memory_type = memory_type # "data" or "instruction"

    def initialize(self):
        self.memory = {}

    def read(self, address):
        address = int(address)
        value = self.memory.get(address, 0) # Default to 0 if address not found for data memory
        if self.memory_type == "instruction" and address not in self.memory:
             raise ValueError(f"Fetch Error: No instruction found at PC=0x{address:X}")
        return int(value) & 0xFFFFFFFFFFFFFFFF if self.memory_type == "data" else value

    def write(self, address, value):
        address = int(address)
        if self.memory_type == "instruction":
            # Instruction memory is typically written to by the loader
            self.memory[address] = str(value) # Store instruction strings
        else: # Data memory
            written_value = int(value) & 0xFFFFFFFFFFFFFFFF
            self.memory[address] = written_value

    def get_display_dict(self):
        if self.memory_type == "instruction":
            # For instruction memory, might want to show address: instruction string
            return {f"0x{addr:X}": val for addr, val in self.memory.items()}
        
        # For data memory, show non-zero values
        mem_display = {
            f"0x{addr:X}": f"0x{val:X} ({val})"
            for addr, val in self.memory.items() if isinstance(val, int) and val != 0
        }
        return dict(sorted(mem_display.items(), key=lambda item: int(item[0], 16)))

    def load_instructions(self, instructions_dict):
        """For instruction memory, loads a dictionary of address: instruction_string."""
        if self.memory_type == "instruction":
            self.memory = instructions_dict.copy()
        else:
            raise TypeError("load_instructions can only be called on instruction memory.")

    def fetch_instruction(self, address):
        if self.memory_type != "instruction":
            raise TypeError("fetch_instruction can only be called on instruction memory.")
        instr = self.memory.get(int(address))
        if instr is None:
            raise ValueError(f"Fetch Error: No instruction found at PC=0x{int(address):X}")
        return instr

    def get_raw_memory(self):
        """Returns a copy of the internal memory dictionary."""
        return self.memory.copy()

    def set_raw_memory(self, mem_dict):
        """Sets internal memory from a given dictionary (used for state restoration)."""
        self.memory = mem_dict.copy()

    def get_all_memory_data(self):
        """Trả về toàn bộ dữ liệu memory để backup"""
        return {
            'instruction_memory': getattr(self, 'instruction_memory', {}).copy(),
            'data_memory': getattr(self, 'data_memory', {}).copy()
        }
        
    def load_from_dict(self, memory_data):
        """Khôi phục memory từ dictionary"""
        if 'instruction_memory' in memory_data:
            self.instruction_memory = memory_data['instruction_memory'].copy()
        if 'data_memory' in memory_data:
            self.data_memory = memory_data['data_memory'].copy()
    
    def get_raw_memory(self):
        """Trả về raw memory data để backup - compatible với memory objects"""
        if hasattr(self, 'memory') and isinstance(self.memory, dict):
            return self.memory.copy()
        elif hasattr(self, 'data_memory') and isinstance(self.data_memory, dict):
            return self.data_memory.copy()
        elif hasattr(self, 'instruction_memory') and isinstance(self.instruction_memory, dict):
            return self.instruction_memory.copy()
        else:
            return {}
    
    def set_raw_memory(self, memory_data):
        """Khôi phục raw memory data - compatible với memory objects"""
        if hasattr(self, 'memory') and isinstance(self.memory, dict):
            self.memory.clear()
            self.memory.update(memory_data)
        elif hasattr(self, 'data_memory') and isinstance(self.data_memory, dict):
            self.data_memory.clear()
            self.data_memory.update(memory_data)
        elif hasattr(self, 'instruction_memory') and isinstance(self.instruction_memory, dict):
            self.instruction_memory.clear()
            self.instruction_memory.update(memory_data)