
import re
CB_FORMAT = ["CBZ", "CBNZ"]
class Assembler:
    def __init__(self):
        self.label_table = {}
        self.instruction_memory = {} # address -> processed instruction string
        self.raw_instruction_memory = {} # address -> original instruction string

    def parse(self, code_string):
        self.label_table.clear()
        self.instruction_memory.clear()
        self.raw_instruction_memory.clear()

        lines = code_string.splitlines()
        current_address = 0
        
        raw_instructions_list = [] # Temp list for pass 1 info

        # --- Pass 1: Build Label Table & Store Raw Instruction Info ---
        print("--- ASM Pass 1: Finding labels and addresses ---")
        line_num = 0
        for line in lines:
            line_num += 1
            original_line = line
            cleaned_line = line.split('//')[0].strip()
            if not cleaned_line: continue

            label_match = re.match(r'^([a-zA-Z_][a-zA-Z0-9_]*):\s*(.*)', cleaned_line)
            instruction_part = cleaned_line

            if label_match:
                label = label_match.group(1)
                instruction_part = label_match.group(2).strip()
                if label in self.label_table:
                    raise ValueError(f"Duplicate label '{label}' defined on line {line_num}")
                self.label_table[label] = current_address
                print(f"  Label Found: '{label}' => Address 0x{current_address:X}")

            if instruction_part:
                if not instruction_part.startswith(('.', '#')):
                    raw_instructions_list.append({
                        'address': current_address,
                        'text': instruction_part,
                        'original': original_line.strip() 
                    })
                    # Store original for display right away
                    self.raw_instruction_memory[current_address] = original_line.strip()
                    current_address += 4
                else:
                    print(f"  Skipping directive/comment: '{instruction_part}'")
        
        print(f"--- ASM Pass 1 Complete. Labels: {self.label_table} ---")

        # --- Pass 2: Resolve Branch Labels to Byte Offsets ---
        print("--- ASM Pass 2: Resolving branch labels to byte offsets ---")
        branch_opcodes = {"CBZ", "CBNZ", "B"}
        instr_count = 0

        for instr_info in raw_instructions_list:
            address = instr_info['address']
            instr_text = instr_info['text']
            processed_instr_text = instr_text

            parts_process = re.split(r'[,\s()\[\]]+', instr_text.upper())
            parts_process = [p for p in parts_process if p]
            opcode_process = parts_process[0].upper() if parts_process else None

            if opcode_process in branch_opcodes:
                potential_label = None
                label_to_replace_in_text = None
                label_match_re = None

                if opcode_process in CB_FORMAT and len(parts_process) >= 3:
                    label_match_re = re.search(r'[,]\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*$', instr_text.strip())
                elif opcode_process == "B" and len(parts_process) >= 2:
                    label_match_re = re.search(r'\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*$', instr_text.strip())

                if label_match_re:
                    potential_label = label_match_re.group(1)
                    label_to_replace_in_text = potential_label
                    
                    label_upper = potential_label.upper()
                    target_address = None
                    actual_label_key = None
                    # Case-insensitive lookup (important)
                    for k_label, v_addr in self.label_table.items():
                        if k_label.upper() == label_upper:
                            target_address = v_addr
                            actual_label_key = k_label
                            break
                    
                    if target_address is not None:
                        offset = target_address - address
                        print(f"  Label '{actual_label_key}' in '{instr_text}' resolved to 0x{target_address:X}. Offset = {offset}")
                        
                        if opcode_process in CB_FORMAT:
                            processed_instr_text = re.sub(r'[,]\s*' + re.escape(label_to_replace_in_text) + r'\s*$', f', {offset}', instr_text.strip())
                        elif opcode_process == "B":
                            processed_instr_text = re.sub(r'\s+' + re.escape(label_to_replace_in_text) + r'\s*$', f' {offset}', instr_text.strip())
                    else:
                        raise ValueError(f"Undefined label '{potential_label}' in '{instr_text}' at 0x{address:X}")
                elif len(parts_process) >= (3 if opcode_process == "CBZ" else 2):
                    last_part = instr_text.split()[-1].lstrip(',')
                    try:
                        int(last_part) # It's already a number
                        print(f"  Branch '{instr_text}' at 0x{address:X} uses numeric offset.")
                    except ValueError:
                        raise ValueError(f"Syntax error or unresolved label '{last_part}' in branch at 0x{address:X}: '{instr_text}'")
            
            self.instruction_memory[address] = processed_instr_text.strip()
            instr_count += 1
        
        print(f"--- ASM Pass 2 Complete. {instr_count} instructions processed. ---")
        return self.instruction_memory, self.raw_instruction_memory, self.label_table