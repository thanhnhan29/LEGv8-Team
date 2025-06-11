# -*- coding: utf-8 -*-

class ControlUnit:
    INSTRUCTION_TABLE = {
    'ADD': {
        'control': {
            'RegWrite': 1,
            'ALUSrc': 0,
            'MemRead': 0,
            'MemWrite': 0,
            'MemToReg': 0,
            'Branch': 0,
            'UncondBranch': 0,
            'ALUOp': '10',
            'Reg2Loc': 1
        }
    },
    'SUB': {
        'control': {
            'RegWrite': 1,
            'ALUSrc': 0,
            'MemRead': 0,
            'MemWrite': 0,
            'MemToReg': 0,
            'Branch': 0,
            'UncondBranch': 0,
            'ALUOp': '10',
            'Reg2Loc': 1
        }
    },
    'AND': {
        'control': {
            'RegWrite': 1,
            'ALUSrc': 0,
            'MemRead': 0,
            'MemWrite': 0,
            'MemToReg': 0,
            'Branch': 0,
            'UncondBranch': 0,
            'ALUOp': '10',
            'Reg2Loc': 1
        }
    },
    'ORR': {
        'control': {
            'RegWrite': 1,
            'ALUSrc': 0,
            'MemRead': 0,
            'MemWrite': 0,
            'MemToReg': 0,
            'Branch': 0,
            'UncondBranch': 0,
            'ALUOp': '10',
            'Reg2Loc': 1
        }
    },
    'EOR': {
        'control': {
            'RegWrite': 1,
            'ALUSrc': 0,
            'MemRead': 0,
            'MemWrite': 0,
            'MemToReg': 0,
            'Branch': 0,
            'UncondBranch': 0,
            'ALUOp': '10',
            'Reg2Loc': 1
        }
    },
    'ADDI': {
        'control': {
            'RegWrite': 1,
            'ALUSrc': 1,
            'MemRead': 0,
            'MemWrite': 0,
            'MemToReg': 0,
            'Branch': 0,
            'UncondBranch': 0,
            'ALUOp': '00',
            'Reg2Loc': 0
        }
    },
    'ANDI': {
        'control': {
            'RegWrite': 1,
            'ALUSrc': 1,
            'MemRead': 0,
            'MemWrite': 0,
            'MemToReg': 0,
            'Branch': 0,
            'UncondBranch': 0,
            'ALUOp': '00',
            'Reg2Loc': 0
        }
    },
    'ORRI': {
        'control': {
            'RegWrite': 1,
            'ALUSrc': 1,
            'MemRead': 0,
            'MemWrite': 0,
            'MemToReg': 0,
            'Branch': 0,
            'UncondBranch': 0,
            'ALUOp': '00',
            'Reg2Loc': 0
        }
    },
    'EORI': {
        'control': {
            'RegWrite': 1,
            'ALUSrc': 1,
            'MemRead': 0,
            'MemWrite': 0,
            'MemToReg': 0,
            'Branch': 0,
            'UncondBranch': 0,
            'ALUOp': '00',
            'Reg2Loc': 0
        }
    },
    'SUBI': {
        'control': {
            'RegWrite': 1,
            'ALUSrc': 1,
            'MemRead': 0,
            'MemWrite': 0,
            'MemToReg': 0,
            'Branch': 0,
            'UncondBranch': 0,
            'ALUOp': '00',
            'Reg2Loc': 0
        }
    },
    'LDUR': {
        'control': {
            'RegWrite': 1,
            'ALUSrc': 1,
            'MemRead': 1,
            'MemWrite': 0,
            'MemToReg': 1,
            'Branch': 0,
            'UncondBranch': 0,
            'ALUOp': '00',
            'Reg2Loc': 0
        }
    },
    'STUR': {
        'control': {
            'RegWrite': 0,
            'ALUSrc': 1,
            'MemRead': 0,
            'MemWrite': 1,
            'MemToReg': 0,
            'Branch': 0,
            'UncondBranch': 0,
            'ALUOp': '00',
            'Reg2Loc': 1
        }
    },
    'CBZ': {
        'control': {
            'RegWrite': 0,
            'ALUSrc': 0,
            'MemRead': 0,
            'MemWrite': 0,
            'MemToReg': 0,
            'Branch': 1,
            'UncondBranch': 0,
            'ALUOp': '01',
            'Reg2Loc': 0
        }
    },
    'B': {
        'control': {
            'RegWrite': 0,
            'ALUSrc': 0,
            'MemRead': 0,
            'MemWrite': 0,
            'MemToReg': 0,
            'Branch': 0,
            'UncondBranch': 1,
            'ALUOp': 'XX',
            'Reg2Loc': 0
        }
    },
    'NOP': {
        'control': {
            'RegWrite': 0,
            'ALUSrc': 0,
            'MemRead': 0,
            'MemWrite': 0,
            'MemToReg': 0,
            'Branch': 0,
            'UncondBranch': 0,
            'ALUOp': 'XX',
            'Reg2Loc': 0
        }
    },
    'MUL': {
        'control': {
            'RegWrite': 1,
            'ALUSrc': 0,
            'MemRead': 0,
            'MemWrite': 0,
            'MemToReg': 0,
            'Branch': 0,
            'UncondBranch': 0,
            'ALUOp': '10',
            'Reg2Loc': 1
        }
    },
    'DIV': {
        'control': {
            'RegWrite': 1,
            'ALUSrc': 0,
            'MemRead': 0,
            'MemWrite': 0,
            'MemToReg': 0,
            'Branch': 0,
            'UncondBranch': 0,
            'ALUOp': '10',
            'Reg2Loc': 1
        }
    },
    'LSL':{
            'control': {
            'RegWrite': 1,
            'ALUSrc': 1,
            'MemRead': 0,
            'MemWrite': 0,
            'MemToReg': 0,
            'Branch': 0,
            'UncondBranch': 0,
            'ALUOp': '10',
            'Reg2Loc': 0
        }
    },
    'LSR':{
            'control': {
            'RegWrite': 1,
            'ALUSrc': 1,
            'MemRead': 0,
            'MemWrite': 0,
            'MemToReg': 0,
            'Branch': 0,
            'UncondBranch': 0,
            'ALUOp': '10',
            'Reg2Loc': 0
        }
    }
}

    def get_control_signals(self, opcode):
        instr_info = self.INSTRUCTION_TABLE.get(opcode.upper())
        if instr_info is None:
            print(f"[WARN] Control Logic: Unknown opcode '{opcode}'. Using NOP signals.")
            return self.INSTRUCTION_TABLE['NOP']['control'].copy()
        return instr_info['control'].copy()