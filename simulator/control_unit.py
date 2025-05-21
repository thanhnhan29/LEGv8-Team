# -*- coding: utf-8 -*-

class ControlUnit:
    INSTRUCTION_TABLE = {
        'ADD':  {'control': {'RegWrite': 1, 'ALUSrc': 0, 'MemRead': 0, 'MemWrite': 0, 'MemToReg': 0, 'Branch': 0, 'UncondBranch': 0, 'ALUOp': '10'}},
        'SUB':  {'control': {'RegWrite': 1, 'ALUSrc': 0, 'MemRead': 0, 'MemWrite': 0, 'MemToReg': 0, 'Branch': 0, 'UncondBranch': 0, 'ALUOp': '10'}},
        'AND':  {'control': {'RegWrite': 1, 'ALUSrc': 0, 'MemRead': 0, 'MemWrite': 0, 'MemToReg': 0, 'Branch': 0, 'UncondBranch': 0, 'ALUOp': '10'}},
        'ORR':  {'control': {'RegWrite': 1, 'ALUSrc': 0, 'MemRead': 0, 'MemWrite': 0, 'MemToReg': 0, 'Branch': 0, 'UncondBranch': 0, 'ALUOp': '10'}},
        'ADDI': {'control': {'RegWrite': 1, 'ALUSrc': 1, 'MemRead': 0, 'MemWrite': 0, 'MemToReg': 0, 'Branch': 0, 'UncondBranch': 0, 'ALUOp': '00'}},
        'SUBI': {'control': {'RegWrite': 1, 'ALUSrc': 1, 'MemRead': 0, 'MemWrite': 0, 'MemToReg': 0, 'Branch': 0, 'UncondBranch': 0, 'ALUOp': '00'}},
        'LDUR': {'control': {'RegWrite': 1, 'ALUSrc': 1, 'MemRead': 1, 'MemWrite': 0, 'MemToReg': 1, 'Branch': 0, 'UncondBranch': 0, 'ALUOp': '00'}},
        'STUR': {'control': {'RegWrite': 0, 'ALUSrc': 1, 'MemRead': 0, 'MemWrite': 1, 'MemToReg': -1,'Branch': 0, 'UncondBranch': 0, 'ALUOp': '00'}},
        'CBZ':  {'control': {'RegWrite': 0, 'ALUSrc': 0, 'MemRead': 0, 'MemWrite': 0, 'MemToReg': 0, 'Branch': 1, 'UncondBranch': 0, 'ALUOp': '01'}},
        'B':    {'control': {'RegWrite': 0, 'ALUSrc': 0, 'MemRead': 0, 'MemWrite': 0, 'MemToReg': 0, 'Branch': 0, 'UncondBranch': 1, 'ALUOp': 'XX'}},
        'NOP':  {'control': {'RegWrite': 0, 'ALUSrc': 0, 'MemRead': 0, 'MemWrite': 0, 'MemToReg': 0, 'Branch': 0, 'UncondBranch': 0, 'ALUOp': 'XX'}},
        'MUL':  {'control': {'RegWrite': 1, 'ALUSrc': 0, 'MemRead': 0, 'MemWrite': 0, 'MemToReg': 0, 'Branch': 0, 'UncondBranch': 0, 'ALUOp': '10'}},
        'DIV':  {'control': {'RegWrite': 1, 'ALUSrc': 0, 'MemRead': 0, 'MemWrite': 0, 'MemToReg': 0, 'Branch': 0, 'UncondBranch': 0, 'ALUOp': '10'}},
    }

    def get_control_signals(self, opcode):
        instr_info = self.INSTRUCTION_TABLE.get(opcode.upper())
        if instr_info is None:
            print(f"[WARN] Control Logic: Unknown opcode '{opcode}'. Using NOP signals.")
            return self.INSTRUCTION_TABLE['NOP']['control'].copy()
        return instr_info['control'].copy()