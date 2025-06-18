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
            'Reg2Loc': 0,
            'FlagWrite': 0,
            'FlagBranch': 0
        }
    },
    'ADDS': {
        'control': {
            'RegWrite': 1,
            'ALUSrc': 0,
            'MemRead': 0,
            'MemWrite': 0,
            'MemToReg': 0,
            'Branch': 0,
            'UncondBranch': 0,
            'ALUOp': '10',
            'Reg2Loc': 0,
            'FlagWrite': 1,
            'FlagBranch': 0
        }
    },
    'SUBS': {
        'control': {
            'RegWrite': 1,
            'ALUSrc': 0,
            'MemRead': 0,
            'MemWrite': 0,
            'MemToReg': 0,
            'Branch': 0,
            'UncondBranch': 0,
            'ALUOp': '10',
            'Reg2Loc': 0,
            'FlagWrite': 1,
            'FlagBranch': 0
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
            'Reg2Loc': 0,
            'FlagWrite': 0,
            'FlagBranch': 0
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
            'Reg2Loc': 0,
            'FlagWrite': 0,
            'FlagBranch': 0
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
            'Reg2Loc': 0,
            'FlagWrite': 0,
            'FlagBranch': 0
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
            'Reg2Loc': 0,
            'FlagWrite': 0,
            'FlagBranch': 0
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
            'Reg2Loc': 0,
            'FlagWrite': 0,
            'FlagBranch': 0
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
            'Reg2Loc': 0,
            'FlagWrite': 0,
            'FlagBranch': 0
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
            'Reg2Loc': 0,
            'FlagWrite': 0,
            'FlagBranch': 0
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
            'Reg2Loc': 0,
            'FlagWrite': 0,
            'FlagBranch': 0
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
            'Reg2Loc': 0,
            'FlagWrite': 0,
            'FlagBranch': 0
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
            'Reg2Loc': 'X',
            'FlagWrite': 0,
            'FlagBranch': 0
        }
    },
    'STUR': {
        'control': {
            'RegWrite': 0,
            'ALUSrc': 1,
            'MemRead': 0,
            'MemWrite': 1,
            'MemToReg': 'X',
            'Branch': 0,
            'UncondBranch': 0,
            'ALUOp': '00',
            'Reg2Loc': 1,
            'FlagWrite': 0,
            'FlagBranch': 0
        }
    },
    'CBZ': {
        'control': {
            'RegWrite': 0,
            'ALUSrc': 0,
            'MemRead': 0,
            'MemWrite': 0,
            'MemToReg': 'X',
            'Branch': 1,
            'UncondBranch': 0,
            'ALUOp': '01',
            'Reg2Loc': 1,
            'FlagWrite': 0,
            'FlagBranch': 0
        }
    },
    'CBNZ': {
        'control': {
            'RegWrite': 0,
            'ALUSrc': 0,
            'MemRead': 0,
            'MemWrite': 0,
            'MemToReg': 0,
            'Branch': 1,
            'UncondBranch': 0,
            'ALUOp': '01',
            'Reg2Loc': 1,
            'FlagWrite': 0,
            'FlagBranch': 0
        }
    },
    'B': {
        'control': {
            'RegWrite': 0,
            'ALUSrc': "X",
            'MemRead': 0,
            'MemWrite': 0,
            'MemToReg': "X",
            'Branch': 0,
            'UncondBranch': 1,
            'ALUOp': 'XX',
            'Reg2Loc': "X",
            'FlagWrite': 0,
            'FlagBranch': 0
        }
    },
    'B.EQ': {
        'control': {
            'RegWrite': 0,
            'ALUSrc': "X",
            'MemRead': 0,
            'MemWrite': 0,
            'MemToReg': "X",
            'Branch': 0,
            'UncondBranch': 0,
            'ALUOp': 'XX',
            'Reg2Loc': "X",
            'FlagWrite': 0,
            'FlagBranch': 1
        }
    },
    'B.NE': {
        'control': {
            'RegWrite': 0,
            'ALUSrc': "X",
            'MemRead': 0,
            'MemWrite': 0,
            'MemToReg': "X",
            'Branch': 0,
            'UncondBranch': 0,
            'ALUOp': 'XX',
            'Reg2Loc': "X",
            'FlagWrite': 0,
            'FlagBranch': 1
        }
    },
    'B.LT': {
        'control': {
            'RegWrite': 0,
            'ALUSrc': "X",
            'MemRead': 0,
            'MemWrite': 0,
            'MemToReg': "X",
            'Branch': 0,
            'UncondBranch': 0,
            'ALUOp': 'XX',
            'Reg2Loc': "X",
            'FlagWrite': 0,
            'FlagBranch': 1
        }
    },
    'B.LO': {
        'control': {
            'RegWrite': 0,
            'ALUSrc': "X",
            'MemRead': 0,
            'MemWrite': 0,
            'MemToReg': "X",
            'Branch': 0,
            'UncondBranch': 0,
            'ALUOp': 'XX',
            'Reg2Loc': "X",
            'FlagWrite': 0,
            'FlagBranch': 1
        }
    },
    'B.LE': {
        'control': {
            'RegWrite': 0,
            'ALUSrc': "X",
            'MemRead': 0,
            'MemWrite': 0,
            'MemToReg': "X",
            'Branch': 0,
            'UncondBranch': 0,
            'ALUOp': 'XX',
            'Reg2Loc': "X",
            'FlagWrite': 0,
            'FlagBranch': 1
        }
    },
    'B.LS': {
        'control': {
            'RegWrite': 0,
            'ALUSrc': "X",
            'MemRead': 0,
            'MemWrite': 0,
            'MemToReg': "X",
            'Branch': 0,
            'UncondBranch': 0,
            'ALUOp': 'XX',
            'Reg2Loc': "X",
            'FlagWrite': 0,
            'FlagBranch': 1
        }
    },
    'B.LS': {
        'control': {
            'RegWrite': 0,
            'ALUSrc': "X",
            'MemRead': 0,
            'MemWrite': 0,
            'MemToReg': "X",
            'Branch': 0,
            'UncondBranch': 0,
            'ALUOp': 'XX',
            'Reg2Loc': "X",
            'FlagWrite': 0,
            'FlagBranch': 1
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
            'Reg2Loc': 0,
            'FlagWrite': 0,
            'FlagBranch': 0
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
            'Reg2Loc': 1,
            'FlagWrite': 0,
            'FlagBranch': 0
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
            'Reg2Loc': 1,
            'FlagWrite': 0,
            'FlagBranch': 0
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
            'Reg2Loc': 0,
            'FlagWrite': 0,
            'FlagBranch': 0
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
            'Reg2Loc': 0,
            'FlagWrite': 0,
            'FlagBranch': 0
        }
    }
}

    def get_control_signals(self, opcode):
        instr_info = self.INSTRUCTION_TABLE.get(opcode.upper())
        if instr_info is None:
            print(f"[WARN] Control Logic: Unknown opcode '{opcode}'. Using NOP signals.")
            return self.INSTRUCTION_TABLE['NOP']['control'].copy()
        return instr_info['control'].copy()