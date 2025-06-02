# Thiết kế Trình mô phỏng LEGv8

Trình mô phỏng LEGv8 này được thiết kế theo module để dễ dàng quản lý, mở rộng và hiểu. Dưới đây là mô tả chi tiết về các thành phần chính và cách chúng tương tác.

## Sơ đồ tổng quan tương tác các Module

```mermaid
graph TD
    A[User Interface (index.html + script.js)] -->|HTTP Requests (JSON)| B(app.py - Flask Server)
    B -->|Code string| C(Assembler: assembler.py)
    C -->|Processed Instructions, Labels| B
    B -->|Load Program Data| D(SimulatorEngine: simulator_engine.py)
    D -->|Initialize/Update| E(RegisterFile: register_file.py)
    D -->|Initialize/Update| F(Memory: memory.py)
    B -->|Micro-step Request| D
    D -- Get Opcode --> G(Instruction: Current Instruction)
    D -- Opcode --> H(ControlUnit: control_unit.py)
    H -- Control Signals --> D
    D -- Operands, Control --> I(ALU: alu.py)
    I -- ALU Result --> D
    D -- Address, Data, Control --> F
    F -- Data --> D
    D -- Write Data, Register, Control --> E
    D -- MicroStepState --> B
    B -->|JSON Response| A

    D --> J(DatapathComponents: datapath_components.py)
    J --> I
    J --> F
    J --> E

    K(InstructionHandlers: instruction_handlers.py) --> C
    K --> D
```

## 1. `app.py` - Máy chủ Flask (Flask Server)

- **Vai trò:** Điểm vào chính cho các tương tác từ người dùng. Nó xử lý các yêu cầu HTTP từ giao diện web.
- **Chức năng chính:**
  - Phục vụ file `index.html` và các tài nguyên tĩnh (CSS, JS, SVG).
  - Cung cấp các API endpoints:
    - `/api/load` (hoặc `/api/compile`): Nhận mã hợp ngữ từ client, gọi `Assembler` để xử lý, sau đó nạp chương trình vào `SimulatorEngine`.
    - `/api/micro_step`: Yêu cầu `SimulatorEngine` thực hiện một bước nhỏ (micro-step) trong quá trình thực thi lệnh.
    - `/api/reset`: Reset trạng thái của `SimulatorEngine` và `Assembler`.
  - Quản lý các instance toàn cục của `SimulatorEngine` và `Assembler`.
  - Định dạng dữ liệu trả về cho client dưới dạng JSON.

## 2. `simulator/assembler.py` - Trình biên dịch (Assembler)

- **Vai trò:** Chuyển đổi mã hợp ngữ LEGv8 do người dùng viết thành một định dạng mà `SimulatorEngine` có thể hiểu và thực thi.
- **Chức năng chính:**
  - **Lexical Analysis & Parsing:** Đọc mã nguồn, loại bỏ comment, khoảng trắng thừa. Tách từng dòng thành các token (nhãn, lệnh, toán hạng).
  - **Label Handling:** Xây dựng một bảng nhãn (`label_table`) để lưu trữ địa chỉ của các nhãn trong mã.
  - **Instruction Encoding (Simplified):** Đối với trình mô phỏng này, thay vì tạo mã máy nhị phân đầy đủ, `Assembler` có thể tạo ra một danh sách các đối tượng lệnh hoặc tuple chứa thông tin đã được xử lý (ví dụ: opcode dưới dạng chuỗi, các toán hạng đã được phân giải).
    - Sử dụng `InstructionHandlers` để lấy thông tin về cách parse từng lệnh.
  - **Error Handling:** Phát hiện và báo cáo các lỗi cú pháp trong mã hợp ngữ.
- **Đầu ra:**
  - `processed_instr`: Danh sách các lệnh đã được xử lý (ví dụ: một list các dictionary, mỗi dict chứa opcode, toán hạng, v.v.).
  - `raw_instr`: Danh sách các chuỗi lệnh gốc (để hiển thị).
  - `labels`: Bảng nhãn đã được giải quyết.

## 3. `simulator/simulator_engine.py` - Động cơ Mô phỏng (Simulator Engine)

- **Vai trò:** Thành phần cốt lõi thực hiện việc mô phỏng thực thi chương trình LEGv8.
- **Chức năng chính:**
  - **Quản lý trạng thái CPU:**
    - Program Counter (`pc`).
    - Các thanh ghi đa dụng (thông qua `RegisterFile`).
    - Bộ nhớ lệnh và dữ liệu (thông qua `Memory`).
    - Cờ trạng thái (nếu được triển khai đầy đủ).
  - **Nạp chương trình:** Nhận dữ liệu đã xử lý từ `Assembler` và khởi tạo bộ nhớ lệnh.
  - **Thực thi từng bước (Micro-stepping):** Triển khai logic cho từng giai đoạn của pipeline (Fetch, Decode, Execute, Memory, Write-back) dưới dạng các micro-steps tuần tự.
    - **Fetch:** Đọc lệnh từ `Memory` tại địa chỉ `pc`.
    - **Decode:** Phân tích lệnh, xác định opcode, đọc giá trị từ `RegisterFile`. Gọi `ControlUnit` để lấy tín hiệu điều khiển. Sử dụng `InstructionHandlers` để biết cách decode cụ thể cho lệnh.
    - **Execute:** Sử dụng `ALU` để thực hiện các phép toán. Tính toán địa chỉ rẽ nhánh, địa chỉ bộ nhớ.
    - **Memory:** Truy cập `Memory` để đọc (LDUR) hoặc ghi (STUR) dữ liệu.
    - **Write-back:** Ghi kết quả trở lại `RegisterFile`.
  - **Cập nhật PC:** Xác định địa chỉ của lệnh tiếp theo.
  - **Tạo `MicroStepState`:** Sau mỗi micro-step, tạo một đối tượng `MicroStepState` chứa thông tin chi tiết về trạng thái hiện tại để gửi về cho client trực quan hóa.
  - **Xử lý Exception/Interrupt (Cơ bản):** Xử lý các lỗi runtime cơ bản (ví dụ: lệnh không hợp lệ, truy cập bộ nhớ sai).

## 4. `simulator/control_unit.py` - Đơn vị Điều khiển (Control Unit)

- **Vai trò:** Dựa trên opcode của lệnh hiện tại, tạo ra các tín hiệu điều khiển cần thiết để điều phối hoạt động của các thành phần khác trong đường dẫn dữ liệu.
- **Chức năng chính:**
  - Nhận opcode làm đầu vào.
  - Xuất ra một tập hợp các tín hiệu điều khiển, ví dụ:
    - `RegWrite`: Cho phép ghi vào Register File.
    - `MemRead`: Cho phép đọc từ Memory.
    - `MemWrite`: Cho phép ghi vào Memory.
    - `ALUSrc`: Chọn đầu vào thứ hai cho ALU (từ thanh ghi hay giá trị tức thời).
    - `ALUOp`: Xác định phép toán mà ALU sẽ thực hiện.
    - `Branch`: Tín hiệu cho biết có rẽ nhánh hay không.
    - `Reg2Loc`: Chọn thanh ghi nguồn thứ hai (ví dụ, cho lệnh store).
    - `PCSrc`: Chọn nguồn cho PC tiếp theo (PC+4, địa chỉ rẽ nhánh, ...).
- Thường được triển khai dưới dạng một bảng ánh xạ lớn hoặc logic điều kiện dựa trên opcode.

## 5. `simulator/alu.py` - Đơn vị Số học & Logic (ALU)

- **Vai trò:** Thực hiện các phép toán số học (cộng, trừ) và logic (AND, OR, XOR) theo yêu cầu của lệnh.
- **Chức năng chính:**
  - Nhận hai toán hạng 64-bit và một tín hiệu điều khiển `ALUOp` (hoặc tương đương) để xác định phép toán.
  - Thực hiện phép toán.
  - Xuất ra kết quả 64-bit và các cờ trạng thái (Zero, Negative - nếu cần cho rẽ nhánh có điều kiện).

## 6. `simulator/memory.py` - Bộ nhớ (Memory)

- **Vai trò:** Mô phỏng bộ nhớ chính của hệ thống, nơi lưu trữ cả lệnh và dữ liệu.
- **Chức năng chính:**
  - Lưu trữ một mảng các byte hoặc word (ví dụ: 64-bit words).
  - Cung cấp các phương thức `read(address)` và `write(address, data)`.
  - Xử lý các vấn đề về căn chỉnh địa chỉ (alignment) nếu cần.
  - Trong trình mô phỏng này, có thể có hai vùng nhớ riêng biệt hoặc một vùng nhớ chung cho lệnh và dữ liệu.

## 7. `simulator/register_file.py` - Tập Thanh ghi (Register File)

- **Vai trò:** Mô phỏng 32 thanh ghi đa dụng 64-bit của LEGv8.
- **Chức năng chính:**
  - Lưu trữ giá trị của các thanh ghi X0-X30 và XZR.
  - Cung cấp các phương thức `read(register_number)` và `write(register_number, data)`.
  - Đảm bảo XZR luôn trả về 0 khi đọc và không thay đổi khi ghi.

## 8. `simulator/datapath_components.py` - Các Thành phần Đường dẫn Dữ liệu

- **Vai trò:** Chứa các khối xây dựng nhỏ hơn của đường dẫn dữ liệu không phức tạp bằng ALU hay Memory.
- **Chức năng chính (ví dụ):**
  - **Mux (Multiplexer):** Chọn một trong nhiều đầu vào dựa trên tín hiệu điều khiển.
  - **Adder:** Thực hiện phép cộng đơn giản (ví dụ: PC + 4, tính toán địa chỉ rẽ nhánh).
  - **SignExtender:** Mở rộng một giá trị tức thời ngắn hơn (ví dụ: 12-bit, 9-bit, 19-bit, 26-bit) thành giá trị 64-bit, giữ nguyên dấu.

## 9. `simulator/instruction_handlers.py` - Bộ xử lý Lệnh

- **Vai trò:** Cung cấp logic cụ thể cho việc giải mã (decode) và chuẩn bị thực thi (execute preparation) cho từng loại lệnh hoặc nhóm lệnh LEGv8.
- **Chức năng chính:**
  - Định nghĩa một cấu trúc dữ liệu (ví dụ: dictionary) ánh xạ từ tên opcode (chuỗi) sang các hàm xử lý.
  - Mỗi hàm xử lý nhận đầu vào là các phần của lệnh đã được parse (ví dụ: `parts` từ `assembler`) và trả về một dictionary chứa thông tin đã được giải mã:
    - `read_reg1_addr`, `read_reg2_addr`: Số hiệu thanh ghi cần đọc.
    - `write_reg_addr`: Số hiệu thanh ghi cần ghi (nếu có).
    - `imm_val`: Giá trị tức thời đã được trích xuất và có thể đã chuyển đổi.
    - `imm_bits`: Số bit của giá trị tức thời (để sign-extend).
    - `branch_offset_val`: Giá trị offset cho lệnh rẽ nhánh.
    - `alu_op_type`: Gợi ý loại phép toán cho ALU.
    - `log`: Chuỗi log mô tả quá trình decode.
  - Giúp tách biệt logic xử lý của từng lệnh ra khỏi `SimulatorEngine` và `Assembler`, làm cho code dễ quản lý hơn.

## 10. `simulator/micro_step.py` - Trạng thái Micro-Step

- **Vai trò:** Định nghĩa một cấu trúc dữ liệu (thường là một class hoặc named tuple) để đóng gói tất cả thông tin liên quan đến một bước thực thi nhỏ (micro-step) của một lệnh.
- **Chức năng chính:**
  - Lưu trữ thông tin như:
    - Tên giai đoạn hiện tại (IF, ID, EX, MEM, WB).
    - Log mô tả các hoạt động trong micro-step đó.
    - Danh sách các khối (blocks) và đường dẫn (paths) đang hoạt động trên SVG datapath.
    - Giá trị của các tín hiệu điều khiển quan trọng.
    - Trạng thái CPU (PC, thanh ghi, bộ nhớ) sau micro-step (hoặc chỉ những thay đổi).
  - Giúp `SimulatorEngine` trả về một đối tượng nhất quán cho `app.py`, sau đó được gửi dưới dạng JSON đến client để cập nhật giao diện.

## Luồng tương tác chính (Ví dụ: Thực thi lệnh ADDI)

1.  **User -> `app.py` -> `Assembler`**: Người dùng nhập `ADDI X1, X2, #10`. `Assembler` parse thành `{'opcode': 'ADDI', 'Rd': 'X1', 'Rn': 'X2', 'imm': 10}`.
2.  **`app.py` -> `SimulatorEngine`**: Nạp chương trình.
3.  **User -> `app.py` -> `SimulatorEngine.step_micro()` (Fetch)**:
    - `pc` trỏ đến lệnh ADDI.
    - `Memory.read(pc)` lấy lệnh.
    - `pc` được cập nhật thành `pc + 4` (tạm thời).
    - `MicroStepState` được tạo (IF, log, active paths: PC -> Mem, Mem -> IR).
4.  **User -> `app.py` -> `SimulatorEngine.step_micro()` (Decode)**:
    - Lệnh ADDI được giải mã. `InstructionHandlers['ADDI']` được gọi.
    - `ControlUnit.get_control_signals('ADDI')` -> `RegWrite=1, ALUSrc=1, ALUOp='ADD', ...`.
    - `RegisterFile.read(X2)` lấy giá trị của X2.
    - `DatapathComponents.sign_extend(10, 12)` mở rộng giá trị tức thời.
    - `MicroStepState` được tạo (ID, log, active paths, control signals).
5.  **User -> `app.py` -> `SimulatorEngine.step_micro()` (Execute)**:
    - `ALU.execute(value_X2, extended_imm, 'ADD')` -> `result`.
    - `MicroStepState` được tạo (EX, log, active paths: Regs -> ALU, Imm -> ALU, ALU -> Regs_WriteData).
6.  **User -> `app.py` -> `SimulatorEngine.step_micro()` (Memory - Bỏ qua cho ADDI)**:
    - Không có truy cập bộ nhớ.
    - `MicroStepState` được tạo (MEM, log, no significant active paths).
7.  **User -> `app.py` -> `SimulatorEngine.step_micro()` (Write-back)**:
    - `RegisterFile.write(X1, result)`.
    - `MicroStepState` được tạo (WB, log, active paths: ALU_Result -> Regs_WriteData, Regs_WriteEnable).

Thiết kế module này cho phép mỗi phần của trình mô phỏng tập trung vào một nhiệm vụ cụ thể, làm cho toàn bộ hệ thống trở nên dễ hiểu, dễ gỡ lỗi và dễ mở rộng hơn.
