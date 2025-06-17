class Memory:
    def __init__(self, memory_type="data", size=1024):  # Default 1MB
        self.memory_type = memory_type # "data" or "instruction"
        self.data_base_address = 0x7FFFFFFF00  # 0x8000000000 - LEGv8 data segment base
        if memory_type == "data":
            self.memory = bytearray(size)  # Array-based memory for data
            self.size = size
        else:
            self.memory = {}  # Keep dictionary for instruction memory:


    def initialize(self):
        if self.memory_type == "data":
            # Clear all bytes to 0
            for i in range(len(self.memory)):
                self.memory[i] = 0
        else:
            self.memory = {}

    def _normalize_address(self, address):
        """Convert virtual address to array index"""
        if self.memory_type == "data":
            # Subtract base address to get array index
            return address - self.data_base_address
        return address

    def _validate_address(self, address, size=8):
        """Validate address for array bounds"""
        if self.memory_type == "data":
            normalized_addr = self._normalize_address(address)
            if normalized_addr < 0 or normalized_addr + size > self.size:
                raise ValueError(f"Memory access out of bounds: address=0x{address}, normalized=0x{normalized_addr:X}, size={size}")

    def read(self, address):
        address = int(address)
        
        if self.memory_type == "instruction":
            value = self.memory.get(address, None)
            if value is None:
                raise ValueError(f"Fetch Error: No instruction found at PC=0x{address:X}")
            return value
        else:  # Data memory - array based
            self._validate_address(address, 8)
            normalized_addr = self._normalize_address(address)
            
            # Read 8 consecutive bytes and combine into 64-bit value (little-endian)
            value = 0
            bytes_read = []
            for i in range(8):
                byte_val = self.memory[normalized_addr + i]
                bytes_read.append(byte_val)
                value |= (byte_val << (i * 8))
            
            
            return value & 0xFFFFFFFFFFFFFFFF

    def write(self, address, value):
        address = int(address)
        
        if self.memory_type == "instruction":
            # Instruction memory is typically written to by the loader
            self.memory[address] = str(value) # Store instruction strings
        else: # Data memory - array based
            
            self._validate_address(address, 8)
            normalized_addr = self._normalize_address(address)

            
            written_value = int(value) & 0xFFFFFFFFFFFFFFFF
            
            # Split 64-bit value into 8 bytes and write (little-endian)
            for i in range(8):
                byte_val = (written_value >> (i * 8)) & 0xFF
                self.memory[normalized_addr + i] = byte_val
                
            
            
    def get_display_dict(self):
        if self.memory_type == "instruction":
            # For instruction memory, show address: instruction string
            return {f"0x{addr:X}": val for addr, val in self.memory.items()}
        
        # For data memory, show non-zero 8-byte values with same format
        mem_display = {}
        
        # Debug: Print first few bytes to see if data exists
        
        for array_index in range(0, min(self.size, 1024), 8):  # Limit check to first 1KB for performance
            value = 0
            # Check if any of the 8 bytes are non-zero
            has_data = False
            for i in range(8):
                if array_index + i < self.size:
                    byte_val = self.memory[array_index + i]
                    if byte_val != 0:
                        has_data = True
                    value |= (byte_val << (i * 8))
            
            if has_data:
                # Convert back to virtual address for display, same format as instruction
                virtual_addr = array_index + self.data_base_address
                mem_display[f"0x{virtual_addr:X}"] = value
                print(f"🔍 Found data at array[{array_index}] = 0x{value:X}, virtual addr = 0x{virtual_addr:X}")
        
       
        return mem_display

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
        if self.memory_type == "data":
            return {'data_memory': bytearray(self.memory)}
        else:
            return {'instruction_memory': self.memory.copy()}
        
    def load_from_dict(self, memory_data):
        """Khôi phục memory từ dictionary"""
        if self.memory_type == "data" and 'data_memory' in memory_data:
            if isinstance(memory_data['data_memory'], (bytearray, list)):
                self.memory = bytearray(memory_data['data_memory'][:self.size])
        elif self.memory_type == "instruction" and 'instruction_memory' in memory_data:
            self.memory = memory_data['instruction_memory'].copy()
    
    def get_raw_memory(self):
        """Returns a copy of the internal memory."""
        if self.memory_type == "data":
            return bytearray(self.memory)
        else:
            return self.memory.copy()

    def set_raw_memory(self, mem_data):
        """Sets internal memory from given data (used for state restoration)."""
        if self.memory_type == "data":
            if isinstance(mem_data, (bytearray, list)):
                self.memory = bytearray(mem_data[:self.size])
            elif isinstance(mem_data, dict):
                # Legacy compatibility: convert from old dict format
                self.initialize()
                for addr, val in mem_data.items():
                    try:
                        self.write(int(addr) if isinstance(addr, str) else addr, val)
                    except (ValueError, TypeError):
                        continue
        else:
            self.memory = mem_data.copy() if isinstance(mem_data, dict) else {}

    def debug_memory_state(self):
        """Debug method to check memory state"""
        if self.memory_type == "data":
            print(f"🔍 Memory Debug:")
            print(f"🔍 Size: {self.size}")
            print(f"🔍 Base address: 0x{self.data_base_address:X}")
            print(f"🔍 Memory type: {type(self.memory)}")
            print(f"🔍 First 64 bytes: {list(self.memory[:64])}")
            
            # Check for any non-zero bytes
            non_zero_count = sum(1 for b in self.memory if b != 0)
            print(f"🔍 Non-zero bytes found: {non_zero_count}")
            
            if non_zero_count > 0:
                # Find first non-zero byte
                for i, byte_val in enumerate(self.memory):
                    if byte_val != 0:
                        virtual_addr = i + self.data_base_address
                        print(f"🔍 First non-zero at array[{i}] = {byte_val}, virtual = 0x{virtual_addr:X}")
                        break
        else:
            print(f"🔍 Instruction memory has {len(self.memory)} entries")