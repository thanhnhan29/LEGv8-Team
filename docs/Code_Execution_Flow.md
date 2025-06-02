# Luồng Thực thi Lệnh trong Trình mô phỏng LEGv8

Tài liệu này mô tả chi tiết cách một lệnh LEGv8 được nạp, giải mã và thực thi từng bước trong trình mô phỏng. Chúng ta sẽ đi qua vai trò của các hàm chính và cách các thành phần tương tác với nhau.

## Tổng quan Luồng Thực thi

Khi người dùng nhấn "Step" trên giao diện, một chuỗi các sự kiện xảy ra:

1.  **Yêu cầu từ Client (`script.js`)**: Gửi yêu cầu POST đến `/api/micro_step`.
2.  **Xử lý ở Server (`app.py`)**: Endpoint `api_micro_step` gọi phương thức `simulator_engine.step_micro()`.
3.  **Động cơ Mô phỏng (`simulator_engine.py`)**: Phương thức `step_micro()` điều phối quá trình thực thi một micro-step. Đây là nơi logic chính của việc mô phỏng pipeline diễn ra tuần tự.
4.  **Trả về Trạng thái (`MicroStepState`)**: `step_micro()` trả về một đối tượng `MicroStepState` chứa thông tin về bước vừa thực hiện, được gửi lại cho client dưới dạng JSON để cập nhật UI.

## Chi tiết các Giai đoạn Thực thi trong `SimulatorEngine._execute_instruction_detailed_generator()`

Phương thức `_execute_instruction_detailed_generator` trong `simulator_engine.py` là một generator, `yield`-ing trạng thái sau mỗi micro-step. Điều này cho phép client thấy từng bước nhỏ của quá trình xử lý lệnh.

### Giai đoạn 0: Instruction Fetch (IF)

- **Mục tiêu**: Lấy lệnh tiếp theo từ bộ nhớ.
- **Hàm/Phương thức liên quan**:
  - `Memory.read_instruction(address)`: Đọc một lệnh 32-bit từ địa chỉ `pc` trong bộ nhớ lệnh.
  - `DatapathComponents.pc_plus_4_adder(current_pc)`: Tính toán địa chỉ `PC + 4`.
- **Hoạt động**:
  1.  Lấy `current_pc_of_instruction = self.pc`.
  2.  Gọi `self.memory.read_instruction(current_pc_of_instruction)` để lấy chuỗi lệnh (`instruction_str_processed`) và lệnh gốc (`instruction_str_raw`).
  3.  Nếu không có lệnh (hết chương trình), kết thúc.
  4.  Tính `pc_p4 = dpc.pc_plus_4_adder(current_pc_of_instruction)`.
  5.  `final_next_pc` được gán bằng `pc_p4` (sẽ được cập nhật nếu có rẽ nhánh).
  6.  **Yield `MicroStepState`**: Trả về trạng thái sau IF, bao gồm log, các đường dẫn hoạt động (ví dụ: từ PC đến Memory, từ Memory đến Instruction Register - IR).

### Giai đoạn 1: Instruction Decode / Register Fetch (ID)

- **Mục tiêu**: Giải mã lệnh để xác định thao tác, đọc các giá trị từ thanh ghi cần thiết, và chuẩn bị các giá trị tức thời.
- **Hàm/Phương thức liên quan**:
  - `re.split()`: Phân tích chuỗi lệnh thành các phần (opcode, toán hạng).
  - `ControlUnit.get_control_signals(opcode)`: Lấy các tín hiệu điều khiển dựa trên opcode.
  - `INSTRUCTION_HANDLERS[opcode]['decode'](parts)` (từ `instruction_handlers.py`): Hàm cụ thể cho từng opcode để trích xuất thông tin chi tiết từ các toán hạng.
  - `RegisterFile.read(reg_addr)`: Đọc giá trị từ một thanh ghi.
  - `DatapathComponents.sign_extend(imm_val, imm_bits)`: Mở rộng dấu cho giá trị tức thời.
- **Hoạt động**:
  1.  Phân tích `instruction_str_processed` để lấy `opcode` và các `parts`.
  2.  Gọi `self.control_unit.get_control_signals(opcode)` để lấy `control_values`.
  3.  Tìm `decode_handler` tương ứng với `opcode` trong `INSTRUCTION_HANDLERS`.
  4.  Gọi `decode_handler(parts)` để nhận `decoded_info` (chứa `read_reg1_addr`, `read_reg2_addr`, `write_reg_addr`, `imm_val`, `branch_offset_val`, etc.).
  5.  **Register Fetch**:
      - Nếu `read_reg1_addr` tồn tại, gọi `self.registers.read(read_reg1_addr)` để lấy `read_data1`.
      - Nếu `read_reg2_addr` tồn tại, gọi `self.registers.read(read_reg2_addr)` để lấy `read_data2`.
  6.  **Immediate Generation**:
      - Nếu `imm_val` tồn tại trong `decoded_info`, gọi `dpc.sign_extend(imm_val, imm_bits)` để tạo `sign_extended_imm`.
  7.  **Branch Offset Calculation (nếu có)**:
      - Nếu `branch_offset_val` tồn tại, nó được lưu lại.
  8.  **Yield `MicroStepState`**: Trả về trạng thái sau ID, bao gồm log, các đường dẫn hoạt động (ví dụ: từ IR đến Control Unit, từ IR đến Register File, từ Register File ra, từ IR đến Sign Extender), và các tín hiệu điều khiển.

### Giai đoạn 2: Execute (EX)

- **Mục tiêu**: Thực hiện phép toán số học/logic hoặc tính toán địa chỉ.
- **Hàm/Phương thức liên quan**:
  - `ALU.execute(operand1, operand2, alu_operation, alu_control_signals)`: Thực hiện phép toán ALU.
  - `DatapathComponents.branch_target_adder(pc_val, offset)`: Tính địa chỉ đích cho lệnh rẽ nhánh.
- **Hoạt động**:
  1.  Xác định các đầu vào cho ALU:
      - `alu_input1`: Thường là `read_data1`.
      - `alu_input2`: Phụ thuộc vào tín hiệu điều khiển `ALUSrc` (từ `control_values`). Có thể là `read_data2` (cho R-format) hoặc `sign_extended_imm` (cho I-format, D-format).
  2.  Gọi `self.alu.execute(...)` với các đầu vào và `control_values.ALUOperation` (hoặc tương đương) để nhận `alu_result` và `alu_flags` (Zero, Negative).
  3.  **Branch Logic**:
      - Nếu là lệnh rẽ nhánh (ví dụ: `B`, `CBZ`, `B.cond`):
        - Tính `branch_target_address` bằng `dpc.branch_target_adder(current_pc_of_instruction, sign_extended_branch_offset)`.
        - Kiểm tra điều kiện rẽ nhánh (dựa trên `alu_flags` cho `B.cond`, hoặc giá trị thanh ghi cho `CBZ`/`CBNZ`).
        - Nếu điều kiện rẽ nhánh đúng (`branch_taken = True`), `final_next_pc` được cập nhật thành `branch_target_address`.
  4.  **Memory Address Calculation (cho LDUR/STUR)**:
      - Nếu là lệnh D-format, `alu_result` (từ `base_reg_val + sign_extended_offset`) chính là địa chỉ bộ nhớ (`memory_address`).
  5.  **Yield `MicroStepState`**: Trả về trạng thái sau EX, bao gồm log, các đường dẫn hoạt động (ví dụ: đến ALU, từ ALU ra), kết quả ALU.

### Giai đoạn 3: Memory Access (MEM)

- **Mục tiêu**: Đọc từ hoặc ghi vào bộ nhớ nếu là lệnh load/store.
- **Hàm/Phương thức liên quan**:
  - `Memory.read_data(address)`: Đọc dữ liệu từ bộ nhớ.
  - `Memory.write_data(address, data)`: Ghi dữ liệu vào bộ nhớ.
- **Hoạt động**:
  1.  Dựa trên tín hiệu điều khiển `MemRead` (từ `control_values`):
      - Nếu `MemRead` được kích hoạt (ví dụ: lệnh `LDUR`):
        - Gọi `self.memory.read_data(memory_address)` để lấy `data_from_memory`.
  2.  Dựa trên tín hiệu điều khiển `MemWrite` (từ `control_values`):
      - Nếu `MemWrite` được kích hoạt (ví dụ: lệnh `STUR`):
        - Dữ liệu cần ghi là `read_data2` (hoặc `Rt` tùy theo quy ước).
        - Gọi `self.memory.write_data(memory_address, data_to_write)`.
  3.  **Yield `MicroStepState`**: Trả về trạng thái sau MEM, bao gồm log, các đường dẫn hoạt động (ví dụ: đến Memory, từ Memory ra nếu là load).

### Giai đoạn 4: Write Back (WB)

- **Mục tiêu**: Ghi kết quả trở lại vào Register File.
- **Hàm/Phương thức liên quan**:
  - `RegisterFile.write(reg_addr, data)`.
- **Hoạt động**:
  1.  Dựa trên tín hiệu điều khiển `RegWrite` và `MemToReg` (hoặc logic tương đương):
      - Xác định dữ liệu cần ghi (`data_to_write_back`):
        - Nếu là lệnh R-format hoặc I-format (không phải load): `data_to_write_back = alu_result`.
        - Nếu là lệnh Load (ví dụ: `LDUR`): `data_to_write_back = data_from_memory`.
      - Xác định thanh ghi đích `write_reg_addr` (từ `decoded_info`).
      - Nếu `RegWrite` được kích hoạt và `write_reg_addr` hợp lệ (không phải XZR):
        - Gọi `self.registers.write(write_reg_addr, data_to_write_back)`.
  2.  **Yield `MicroStepState`**: Trả về trạng thái sau WB, bao gồm log, các đường dẫn hoạt động (ví dụ: đến Register File write port).

### Cập nhật PC cuối cùng

- Sau khi tất cả các micro-steps của một lệnh hoàn thành (hoặc lệnh kết thúc sớm do lỗi):
  - `self.pc = final_next_pc`.
  - Trạng thái `self.is_finished` được cập nhật nếu không còn lệnh nào.

## Cơ chế của một số lệnh LEGv8 cụ thể

### 1. Lệnh `ADD X0, X1, X2` (R-format)

- **Opcode**: Ví dụ: `ADD` (giá trị nhị phân cụ thể được định nghĩa trong `instruction_handlers.py` và `control_unit.py`).
- **IF**: Lệnh được fetch.
- **ID**: `opcode = ADD`. `control_values` được lấy cho ADD (`RegWrite=1, ALUSrc=0, ALUOp='ADD', MemRead=0, MemWrite=0`, etc.). `read_reg1_addr=X1`, `read_reg2_addr=X2`, `write_reg_addr=X0`. Giá trị của X1 và X2 được đọc.
- **EX**: `alu_input1 = value(X1)`, `alu_input2 = value(X2)`. `ALU.execute(value(X1), value(X2), 'ADD')` -> `alu_result = value(X1) + value(X2)`.
- **MEM**: Bỏ qua (không có truy cập bộ nhớ).
- **WB**: `RegisterFile.write(X0, alu_result)`.
- **PC Update**: `PC = PC + 4`.

### 2. Lệnh `ADDI X0, X1, #100` (I-format)

- **Opcode**: `ADDI`.
- **IF**: Lệnh được fetch.
- **ID**: `opcode = ADDI`. `control_values` được lấy cho ADDI (`RegWrite=1, ALUSrc=1, ALUOp='ADD'`, etc.). `read_reg1_addr=X1`, `write_reg_addr=X0`. `imm_val=100`. Giá trị của X1 được đọc. `sign_extended_imm = sign_extend(100, 12)`.
- **EX**: `alu_input1 = value(X1)`, `alu_input2 = sign_extended_imm`. `ALU.execute(value(X1), sign_extended_imm, 'ADD')` -> `alu_result = value(X1) + sign_extended_imm`.
- **MEM**: Bỏ qua.
- **WB**: `RegisterFile.write(X0, alu_result)`.
- **PC Update**: `PC = PC + 4`.

### 3. Lệnh `LDUR X0, [X1, #8]` (D-format)

- **Opcode**: `LDUR`.
- **IF**: Lệnh được fetch.
- **ID**: `opcode = LDUR`. `control_values` được lấy cho LDUR (`RegWrite=1, ALUSrc=1, ALUOp='ADD', MemRead=1, MemToReg=1`, etc.). `read_reg1_addr=X1` (base register), `write_reg_addr=X0` (destination). `imm_val=8` (offset). Giá trị của X1 được đọc. `sign_extended_offset = sign_extend(8, 9)`.
- **EX**: `alu_input1 = value(X1)`, `alu_input2 = sign_extended_offset`. `ALU.execute(value(X1), sign_extended_offset, 'ADD')` -> `alu_result` (đây là `memory_address`).
- **MEM**: `Memory.read_data(memory_address)` -> `data_from_memory`.
- **WB**: `RegisterFile.write(X0, data_from_memory)`.
- **PC Update**: `PC = PC + 4`.

### 4. Lệnh `STUR X0, [X1, #8]` (D-format)

- **Opcode**: `STUR`.
- **IF**: Lệnh được fetch.
- **ID**: `opcode = STUR`. `control_values` được lấy cho STUR (`RegWrite=0, ALUSrc=1, ALUOp='ADD', MemWrite=1`, etc.). `read_reg1_addr=X1` (base register), `read_reg2_addr=X0` (source data to store). `imm_val=8` (offset). Giá trị của X1 và X0 được đọc. `sign_extended_offset = sign_extend(8, 9)`.
- **EX**: `alu_input1 = value(X1)`, `alu_input2 = sign_extended_offset`. `ALU.execute(value(X1), sign_extended_offset, 'ADD')` -> `alu_result` (đây là `memory_address`).
- **MEM**: `Memory.write_data(memory_address, value(X0))`.
- **WB**: Bỏ qua (không ghi vào Register File).
- **PC Update**: `PC = PC + 4`.

### 5. Lệnh `CBZ X0, target_label` (CB-format)

- **Opcode**: `CBZ`.
- **IF**: Lệnh được fetch.
- **ID**: `opcode = CBZ`. `control_values` được lấy cho CBZ (`Branch=1` (hoặc tín hiệu điều khiển rẽ nhánh cụ thể), `ALUOp` có thể là so sánh hoặc không cần thiết nếu kiểm tra trực tiếp). `read_reg1_addr=X0`. `branch_offset_val` được trích xuất từ lệnh (ví dụ: `target_label - PC_current_instruction`). Giá trị của X0 được đọc. `sign_extended_branch_offset` được tính.
- **EX**: Kiểm tra `value(X0) == 0`.
  - Nếu đúng (`branch_taken = True`): `branch_target_address = PC_current_instruction + sign_extended_branch_offset`. `final_next_pc = branch_target_address`.
  - Nếu sai (`branch_taken = False`): `final_next_pc` giữ nguyên là `PC_current_instruction + 4`.
- **MEM**: Bỏ qua.
- **WB**: Bỏ qua.
- **PC Update**: `PC = final_next_pc`.

### 6. Lệnh `B target_label` (B-format)

- **Opcode**: `B`.
- **IF**: Lệnh được fetch.
- **ID**: `opcode = B`. `control_values` được lấy cho B (`UnconditionalBranch=1`). `branch_offset_val` được trích xuất. `sign_extended_branch_offset` được tính.
- **EX**: `branch_taken = True`. `branch_target_address = PC_current_instruction + sign_extended_branch_offset`. `final_next_pc = branch_target_address`.
- **MEM**: Bỏ qua.
- **WB**: Bỏ qua.
- **PC Update**: `PC = final_next_pc`.

## Vai trò của các thành phần LEGv8 trong thực thi

- **Program Counter (PC)**: Luôn trỏ đến lệnh tiếp theo sẽ được fetch (hoặc lệnh hiện tại đang được xử lý trong pipeline mô phỏng này). Được cập nhật sau mỗi lệnh (+4 hoặc đến địa chỉ rẽ nhánh).
- **Instruction Memory**: Lưu trữ các lệnh của chương trình. `SimulatorEngine` đọc từ đây trong giai đoạn IF.
- **Register File (`self.registers`)**: Lưu trữ trạng thái của các thanh ghi X0-XZR. Được đọc trong ID (cho toán hạng) và ghi trong WB (cho kết quả).
- **Sign Extender (`dpc.sign_extend`)**: Mở rộng các giá trị tức thời (offset, immediate) thành 64-bit trước khi đưa vào ALU hoặc tính toán địa chỉ.
- **Control Unit (`self.control_unit`)**: Dựa trên opcode (từ ID), tạo ra tất cả các tín hiệu điều khiển cần thiết cho các giai đoạn EX, MEM, WB. Quyết định ALU làm gì, có đọc/ghi bộ nhớ không, có ghi thanh ghi không, v.v.
- **ALU (`self.alu`)**: Thực hiện các phép toán số học/logic trong giai đoạn EX. Ví dụ: tính `X1+X2`, `X1+imm`, `BaseReg+Offset`.
- **Data Memory (`self.memory`)**: Lưu trữ dữ liệu của chương trình. Được truy cập trong giai đoạn MEM cho các lệnh LDUR (đọc) và STUR (ghi).
- **Multiplexers (MUXes)** (Mô phỏng ngầm trong logic của `SimulatorEngine` và `ALU`):
  - Chọn đầu vào thứ hai cho ALU (từ thanh ghi hoặc từ sign-extended immediate).
  - Chọn giá trị để ghi vào Register File (từ ALU result hoặc từ Data Memory).
  - Chọn PC tiếp theo (PC+4 hoặc branch target address).

Tài liệu này cung cấp một cái nhìn chi tiết về cách trình mô phỏng xử lý các lệnh LEGv8. Sự tương tác giữa các module và việc chia nhỏ quá trình thực thi thành các micro-steps cho phép trực quan hóa và hiểu rõ hơn về hoạt động bên trong của một CPU đơn giản.
