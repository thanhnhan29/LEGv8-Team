# -*- coding: utf-8 -*-

class RegisterFile:
    def __init__(self):
        self.registers = {}
        self.initialize()

    def initialize(self):
        self.registers = {f"X{i}": 0 for i in range(31)} # X0-X30
        self.registers["XZR"] = 0 # Read-only zero
        # SP (X28) initial value, often high in memory
        self.registers["X28"] = 0x7FFFFFFF00 # Example, can be configured

    def read(self, reg_name):
        reg_name = reg_name.upper()
        if reg_name == "XZR" or reg_name == "X31":
            return 0
        if reg_name == "SP":
            reg_name = "X28"
        
        val = self.registers.get(reg_name)
        if val is None:
            raise ValueError(f"Invalid register read: Register '{reg_name}' does not exist.")
        return int(val) & 0xFFFFFFFFFFFFFFFF

    def write(self, reg_name, value):
        reg_name = reg_name.upper()
        if reg_name not in ["XZR", "X31"]:
            if reg_name == "SP":
                reg_name = "X28"
            if reg_name in self.registers:
                written_value = int(value) & 0xFFFFFFFFFFFFFFFF
                self.registers[reg_name] = written_value
            else:
                raise ValueError(f"Invalid register write target: Register '{reg_name}' does not exist.")
        # Writes to XZR/X31 are silently ignored

    def get_display_dict(self):
        regs_copy = self.registers.copy()
        sp_val = regs_copy.get('X28', 0)
        regs_display = {"SP": f"0x{sp_val:X} ({sp_val})"}

        for i in range(32):
            if i == 31:
                reg_name = "XZR"
                val = 0
            else:
                reg_name = f"X{i}"
                if i == 28: continue
                val = regs_copy.get(reg_name, 0)
            
            if reg_name == "XZR":
                regs_display[reg_name] = f"0x{val:X}"
            elif val != 0:
                regs_display[reg_name] = f"0x{val:X} ({val})"
            # else: # Optional: show zero registers
            #    regs_display[reg_name] = f"0x{val:X}"

        def reg_sort_key(item):
            name = item[0]
            if name == "SP": return 28.5
            if name == "XZR": return 31
            try: return int(name[1:])
            except: return 99
        
        return dict(sorted(regs_display.items(), key=reg_sort_key))

    def get_all_registers(self):
        """Returns a copy of the internal registers dictionary."""
        return self.registers.copy()

    def set_all_registers(self, regs_dict):
        """Sets internal registers from a given dictionary (used for state restoration)."""
        self.registers = regs_dict.copy()