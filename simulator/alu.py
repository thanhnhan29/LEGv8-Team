
class ALU:
    @staticmethod
    def execute(operand1, operand2, operation):
        """
        Execute ALU operation and return result with flags information
        
        Args:
            operand1: First operand (int)
            operand2: Second operand (int) 
            operation: Operation string
            
        Returns:
            tuple: (result, zero_flag, flags_data)
                - result: ALU result (64-bit)
                - zero_flag: Zero flag (0 or 1)
                - flags_data: Dict with N, Z, C, V flags for updating FlagsRegister
        """
        op1_int, op2_int = int(operand1), int(operand2)
        result = 0
        carry_flag = 0
        overflow_flag = 0
        
        if operation == 'add': 
            result = op1_int + op2_int
            # Calculate carry for unsigned addition
            carry_flag = 1 if result > 0xFFFFFFFFFFFFFFFF else 0
            # Calculate overflow for signed addition
            overflow_flag = ALU._calculate_add_overflow(op1_int, op2_int, result)
            
        elif operation == 'sub': 
            result = op1_int - op2_int
            # Calculate borrow for unsigned subtraction (inverted carry)
            carry_flag = 1 if op1_int >= op2_int else 0
            # Calculate overflow for signed subtraction
            overflow_flag = ALU._calculate_sub_overflow(op1_int, op2_int, result)
            
        elif operation == 'and': 
            result = op1_int & op2_int
            # Logical operations don't affect C, V flags
            
        elif operation == 'orr': 
            result = op1_int | op2_int
            
        elif operation == 'eor': 
            result = op1_int ^ op2_int
            
        elif operation == 'pass1': 
            result = op2_int 
            
        elif operation == 'mul': 
            result = op1_int * op2_int
            # Multiplication may set C flag if result overflows 64-bit
            carry_flag = 1 if result > 0xFFFFFFFFFFFFFFFF else 0
            
        elif operation == 'div':
            if op2_int == 0:
                raise ValueError("ALU Error: Division by zero.")
            result = int(op1_int / op2_int)

        elif operation == 'lsl': 
            result = op1_int << operand2
            # Shift operations may affect carry flag
            if operand2 > 0 and operand2 <= 64:
                # Check if any bits were shifted out
                carry_flag = 1 if (op1_int >> (64 - operand2)) & 1 else 0
                
        elif operation == 'lsr': 
            result = op1_int >> operand2
            # Check if any bits were shifted out
            if operand2 > 0 and operand2 <= 64:
                carry_flag = (op1_int >> (operand2 - 1)) & 1
                
        else: 
            raise ValueError(f"ALU Error: Operation '{operation}' not supported.")

        # Ensure result fits in 64-bit
        result_64 = result & 0xFFFFFFFFFFFFFFFF
        
        # Calculate flags
        zero_flag = 1 if result_64 == 0 else 0
        negative_flag = 1 if (result_64 & 0x8000000000000000) != 0 else 0
        
        # Prepare flags data for FlagsRegister
        flags_data = {
            'N': negative_flag,
            'Z': zero_flag, 
            'C': carry_flag,
            'V': overflow_flag
        }
        return result_64, zero_flag, flags_data

    @staticmethod
    def _calculate_add_overflow(op1, op2, result):
        """Calculate overflow flag for signed addition"""
        # Overflow occurs when:
        # - Adding two positive numbers gives negative result
        # - Adding two negative numbers gives positive result
        op1_sign = (op1 >> 63) & 1
        op2_sign = (op2 >> 63) & 1
        result_sign = (result >> 63) & 1
        
        # Overflow if operands have same sign but result has different sign
        if op1_sign == op2_sign and op1_sign != result_sign:
            return 1
        return 0

    @staticmethod
    def _calculate_sub_overflow(op1, op2, result):
        """Calculate overflow flag for signed subtraction"""
        # Overflow occurs when:
        # - Subtracting negative from positive gives negative result
        # - Subtracting positive from negative gives positive result
        op1_sign = (op1 >> 63) & 1
        op2_sign = (op2 >> 63) & 1
        result_sign = (result >> 63) & 1
        
        # Overflow if operands have different signs and result has same sign as subtrahend
        if op1_sign != op2_sign and result_sign == op2_sign:
            return 1
        return 0