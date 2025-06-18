class FlagsRegister:
    """
    Class để xử lý 4 cờ điều kiện N, Z, C, V trong LEGv8
    N: Negative flag - Kết quả âm
    Z: Zero flag - Kết quả bằng 0
    C: Carry flag - Có carry/borrow trong phép toán
    V: Overflow flag - Có overflow trong phép toán signed
    """
    
    def __init__(self):
        # Khởi tạo 4 cờ
        self.N = 0  # Negative flag
        self.Z = 0  # Zero flag
        self.C = 0  # Carry flag
        self.V = 0  # Overflow flag
        
        self.branch_conditions = {
            # Unconditional
            # 'B.AL': lambda: True,           # Always (default)
            # 'B.NV': lambda: False,          # Never
            
            # Equality conditions
            'B.EQ': lambda: self.Z == 1,    # Equal (Z=1)
            'B.NE': lambda: self.Z == 0,    # Not Equal (Z=0)
            
            # Signed comparisons
            'B.LT': lambda: self.N != self.V,        # Less Than (N≠V)
            'B.LE': lambda: self.Z == 1 or self.N != self.V,  # Less Than or Equal (Z=1 OR N≠V)
            'B.GT': lambda: self.Z == 0 and self.N == self.V,  # Greater Than (Z=0 AND N=V)
            'B.GE': lambda: self.N == self.V,        # Greater Than or Equal (N=V)
            
            # Unsigned comparisons
            'B.LO': lambda: self.C == 0,    # Lower (unsigned <) (C=0)
            'B.LS': lambda: self.C == 0 or self.Z == 1,  # Lower or Same (C=0 OR Z=1)
            'B.HI': lambda: self.C == 1 and self.Z == 0,  # Higher (C=1 AND Z=0)
            'B.HS': lambda: self.C == 1,    # Higher or Same (C=1)
            
            # Sign/Overflow conditions
            # 'B.MI': lambda: self.N == 1,    # Minus/Negative (N=1)
            # 'B.PL': lambda: self.N == 0,    # Plus/Positive or Zero (N=0)
            # 'B.VS': lambda: self.V == 1,    # Overflow Set (V=1)
            # 'B.VC': lambda: self.V == 0,    # Overflow Clear (V=0)
            
            # # Carry conditions
            # 'B.CS': lambda: self.C == 1,    # Carry Set (C=1)
            # 'B.CC': lambda: self.C == 0,    # Carry Clear (C=0)
        }
        

    def update_flags(self, result, operand1=None, operand2=None, operation=None):
        """
        Cập nhật flags dựa trên kết quả phép toán
        
        Args:
            result: Kết quả phép toán (64-bit)
            operand1: Toán hạng 1 (cho overflow detection)
            operand2: Toán hạng 2 (cho overflow detection)
            operation: Loại phép toán ('add', 'sub', 'and', 'or', 'eor', etc.)
        """
        # Đảm bảo result là 64-bit
        result_64 = result & 0xFFFFFFFFFFFFFFFF
        
        # Update Zero flag
        self.Z = 1 if result_64 == 0 else 0
        
        # Update Negative flag (bit 63)
        self.N = 1 if (result_64 & 0x8000000000000000) != 0 else 0
        
        # Update Carry và Overflow flags dựa trên operation
        if operation in ['add', 'adds']:
            self._update_add_flags(result, operand1, operand2)
        elif operation in ['sub', 'subs', 'cmp']:
            self._update_sub_flags(result, operand1, operand2)
        elif operation in ['and', 'ands', 'tst']:
            # Logical operations: C = 0, V unchanged
            self.C = 0
        elif operation in ['or', 'orr', 'eor']:
            # Logical operations: C = 0, V unchanged
            self.C = 0
        elif operation in ['lsl', 'lsr', 'asr']:
            # Shift operations: update C based on last bit shifted out
            self._update_shift_flags(result, operand1, operand2, operation)
    
    def _update_add_flags(self, result, operand1, operand2):
        """Cập nhật C và V flags cho phép cộng"""
        if operand1 is not None and operand2 is not None:
            # Carry flag: overflow từ bit 63
            self.C = 1 if result > 0xFFFFFFFFFFFFFFFF else 0
            
            # Overflow flag: signed overflow
            # Overflow xảy ra khi: (+) + (+) = (-) hoặc (-) + (-) = (+)
            sign1 = (operand1 & 0x8000000000000000) >> 63
            sign2 = (operand2 & 0x8000000000000000) >> 63
            sign_result = (result & 0x8000000000000000) >> 63
            
            self.V = 1 if (sign1 == sign2) and (sign1 != sign_result) else 0
    
    def _update_sub_flags(self, result, operand1, operand2):
        """Cập nhật C và V flags cho phép trừ"""
        if operand1 is not None and operand2 is not None:
            # Carry flag: borrow occurred (operand1 < operand2 unsigned)
            self.C = 1 if operand1 >= operand2 else 0
            
            # Overflow flag: signed overflow
            # Overflow xảy ra khi: (+) - (-) = (-) hoặc (-) - (+) = (+)
            sign1 = (operand1 & 0x8000000000000000) >> 63
            sign2 = (operand2 & 0x8000000000000000) >> 63
            sign_result = (result & 0x8000000000000000) >> 63
            
            self.V = 1 if (sign1 != sign2) and (sign1 != sign_result) else 0
    
    def _update_shift_flags(self, result, operand1, shift_amount, operation):
        """Cập nhật flags cho phép shift"""
        if operand1 is not None and shift_amount is not None and shift_amount > 0:
            if operation == 'lsl':  # Left shift
                # C = bit shifted out from left
                if shift_amount <= 64:
                    self.C = 1 if (operand1 & (1 << (64 - shift_amount))) != 0 else 0
            elif operation == 'lsr':  # Logical right shift
                # C = bit shifted out from right
                if shift_amount <= 64:
                    self.C = 1 if (operand1 & (1 << (shift_amount - 1))) != 0 else 0
            elif operation == 'asr':  # Arithmetic right shift
                # C = bit shifted out from right
                if shift_amount <= 64:
                    self.C = 1 if (operand1 & (1 << (shift_amount - 1))) != 0 else 0
    
    def check_condition(self, condition_code):
        """
        Kiểm tra điều kiện branch có thỏa mãn với trạng thái flags hiện tại không
        
        Args:
            condition_code: Mã điều kiện (ví dụ: 'B.EQ', 'B.LT', 'B.HI')
        
        Returns:
            int: 1 nếu điều kiện thỏa mãn, 0 nếu không
        """
        condition_code = condition_code.upper()
        
        if condition_code in self.branch_conditions:
            return 1 if self.branch_conditions[condition_code]() else 0
        else:
            print(f"Warning: Unknown condition code: {condition_code}")
            return 0
    
    def get_flags_state(self):
        """
        Trả về trạng thái hiện tại của tất cả flags
        
        Returns:
            dict: Dictionary chứa trạng thái của 4 flags
        """
        return {
            'N': self.N,
            'Z': self.Z,
            'C': self.C,
            'V': self.V
        }
    
    def set_flags(self, N=None, Z=None, C=None, V=None):
        """
        Thiết lập trạng thái flags thủ công
        
        Args:
            N, Z, C, V: Giá trị flags (0 hoặc 1), None để giữ nguyên
        """
        if N is not None:
            self.N = 1 if N else 0
        if Z is not None:
            self.Z = 1 if Z else 0
        if C is not None:
            self.C = 1 if C else 0
        if V is not None:
            self.V = 1 if V else 0
    
    def reset_flags(self):
        """Reset tất cả flags về 0"""
        self.N = 0
        self.Z = 0
        self.C = 0
        self.V = 0
    
    def __str__(self):
        """String representation của flags"""
        return f"NZCV: {self.N}{self.Z}{self.C}{self.V}"
    
    def __repr__(self):
        return f"FlagsRegister(N={self.N}, Z={self.Z}, C={self.C}, V={self.V})"