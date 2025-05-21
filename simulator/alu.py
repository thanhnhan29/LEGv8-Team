# -*- coding: utf-8 -*-

class ALU:
    @staticmethod
    def execute(operand1, operand2, operation):
        op1_int, op2_int = int(operand1), int(operand2)
        result = 0
        if operation == 'add': result = op1_int + op2_int
        elif operation == 'sub': result = op1_int - op2_int
        elif operation == 'and': result = op1_int & op2_int
        elif operation == 'orr': result = op1_int | op2_int
        elif operation == 'pass1': result = op1_int # Used for CBZ to check zero flag of operand1
        elif operation == 'mul': result = op1_int * op2_int
        elif operation == 'div':
            if op2_int == 0:
                raise ValueError("ALU Error: Division by zero.")
            result = int(op1_int / op2_int)
        else: raise ValueError(f"ALU Error: Operation '{operation}' not supported.")

        result_64 = result & 0xFFFFFFFFFFFFFFFF
        zero_flag = 1 if result_64 == 0 else 0
        return result_64, zero_flag