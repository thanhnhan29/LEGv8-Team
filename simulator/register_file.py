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
        """Trả về dictionary của tất cả registers để backup"""
        register_dict = {}
        
        # Backup X0-X30 registers
        if hasattr(self, 'x_registers'):
            register_dict['x_registers'] = self.x_registers.copy() if isinstance(self.x_registers, dict) else list(self.x_registers)
        
        # Backup special registers
        if hasattr(self, 'sp'):
            register_dict['sp'] = self.sp
        if hasattr(self, 'fp'):
            register_dict['fp'] = self.fp
        if hasattr(self, 'lr'):
            register_dict['lr'] = self.lr
        if hasattr(self, 'xzr'):
            register_dict['xzr'] = self.xzr
            
        # Backup any other attributes that might be registers
        for attr_name in dir(self):
            if not attr_name.startswith('_') and not callable(getattr(self, attr_name)):
                attr_value = getattr(self, attr_name)
                if attr_name not in register_dict and isinstance(attr_value, (int, float, str)):
                    register_dict[attr_name] = attr_value
                    
        return register_dict
    
    def restore_all_registers(self, register_dict):
        """Khôi phục tất cả registers từ dictionary"""
        for attr_name, attr_value in register_dict.items():
            if hasattr(self, attr_name):
                if attr_name == 'x_registers' and hasattr(self, 'x_registers'):
                    if isinstance(self.x_registers, dict):
                        self.x_registers.clear()
                        self.x_registers.update(attr_value)
                    elif isinstance(self.x_registers, list):
                        self.x_registers[:] = attr_value
                else:
                    setattr(self, attr_name, attr_value)