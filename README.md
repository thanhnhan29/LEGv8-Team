# LEGv8 Simulator

Đây là một trình mô phỏng kiến trúc LEGv8, được xây dựng bằng Python và Flask cho giao diện web. Trình mô phỏng này cho phép người dùng viết mã hợp ngữ LEGv8, biên dịch và chạy từng bước để quan sát trạng thái của CPU, bộ nhớ và các thành phần đường dẫn dữ liệu.

## Kiến trúc LEGv8

LEGv8 là một tập lệnh đơn giản hóa dựa trên ARMv8, thường được sử dụng trong giáo dục để dạy các khái niệm cơ bản về kiến trúc máy tính. Nó có một tập lệnh cố định 32-bit và sử dụng kiến trúc load-store.

### Đặc điểm chính của LEGv8:

- **Thanh ghi (Registers):** Có 32 thanh ghi đa dụng 64-bit (X0-X30, XZR - Zero Register).
- **Định dạng lệnh (Instruction Formats):** LEGv8 sử dụng nhiều định dạng lệnh khác nhau cho các loại thao tác khác nhau:
  - **R-format (Register):** Cho các phép toán số học/logic giữa các thanh ghi.
    - Ví dụ: `ADD X0, X1, X2` (X0 = X1 + X2)
  - **I-format (Immediate):** Cho các phép toán với một giá trị tức thời.
    - Ví dụ: `ADDI X0, X1, #10` (X0 = X1 + 10)
  - **D-format (Data):** Cho các lệnh tải/lưu trữ dữ liệu từ/vào bộ nhớ.
    - Ví dụ: `LDUR X0, [X1, #8]` (Tải giá trị từ địa chỉ bộ nhớ X1+8 vào X0)
  - **B-format (Branch):** Cho các lệnh rẽ nhánh không điều kiện.
    - Ví dụ: `B label` (Nhảy đến nhãn `label`)
  - **CB-format (Conditional Branch):** Cho các lệnh rẽ nhánh có điều kiện.
    - Ví dụ: `CBZ X0, label` (Nếu X0 == 0 thì nhảy đến `label`)
  - **IW-format (Immediate Wide):** Cho các lệnh di chuyển giá trị tức thời rộng vào thanh ghi.
    - Ví dụ: `MOVZ X0, #0x1234, LSL #16` (Di chuyển 0x1234 vào X0, dịch trái 16 bit)
- **Opcode:** Mỗi lệnh LEGv8 có một mã opcode (operation code) xác định loại thao tác sẽ được thực hiện. Trình mô phỏng sử dụng opcode này để điều khiển các đơn vị chức năng.

## Cấu trúc dự án

Dự án được tổ chức thành các thành phần chính sau:

- **`app.py`**: File chính của ứng dụng Flask, xử lý các yêu cầu HTTP từ frontend, điều phối hoạt động của trình biên dịch và trình mô phỏng.
- **`simulator/`**: Thư mục chứa logic cốt lõi của trình mô phỏng.
  - **`assembler.py`**: Chịu trách nhiệm phân tích (parse) mã hợp ngữ LEGv8 do người dùng nhập vào, chuyển đổi nó thành mã máy (hoặc một dạng biểu diễn trung gian mà trình mô phỏng có thể hiểu) và giải quyết các nhãn (labels).
  - **`simulator_engine.py`**: Động cơ chính của trình mô phỏng. Nó quản lý trạng thái CPU (thanh ghi, PC), bộ nhớ, và thực thi từng lệnh theo các giai đoạn của pipeline (Fetch, Decode, Execute, Memory, Write-back - mặc dù ở đây có thể được đơn giản hóa thành các micro-steps).
  - **`control_unit.py`**: Mô phỏng đơn vị điều khiển. Dựa trên opcode của lệnh, nó tạo ra các tín hiệu điều khiển cần thiết cho các thành phần khác của đường dẫn dữ liệu (ví dụ: chọn đầu vào cho ALU, cho phép ghi vào thanh ghi, v.v.).
  - **`alu.py`**: Mô phỏng Đơn vị Số học và Logic (ALU), thực hiện các phép toán như cộng, trừ, AND, OR, v.v.
  - **`memory.py`**: Mô phỏng bộ nhớ chính, nơi lưu trữ cả lệnh và dữ liệu.
  - **`register_file.py`**: Mô phỏng tập tin thanh ghi của CPU.
  - **`datapath_components.py`**: Chứa các thành phần nhỏ hơn của đường dẫn dữ liệu như MUX, Adder, Sign Extender.
  - **`instruction_handlers.py`**: Định nghĩa cách xử lý (decode, execute) cho từng loại lệnh LEGv8 cụ thể.
  - **`micro_step.py`**: Định nghĩa cấu trúc dữ liệu cho trạng thái của một micro-step trong quá trình thực thi lệnh, giúp trực quan hóa từng bước nhỏ.
- **`static/`**: Chứa các file tĩnh cho frontend (JavaScript, CSS, hình ảnh SVG của đường dẫn dữ liệu).
  - **`script.js`**: Xử lý logic phía client, gửi yêu cầu đến backend, cập nhật giao diện người dùng với trạng thái mô phỏng.
  - **`datapath.svg`**: Hình ảnh SVG của đường dẫn dữ liệu LEGv8, được sử dụng để trực quan hóa luồng dữ liệu.
- **`templates/`**: Chứa các template HTML (ví dụ: `index.html`) được render bởi Flask.

## Cách hoạt động

1.  **Nhập mã**: Người dùng nhập mã hợp ngữ LEGv8 vào trình soạn thảo trên giao diện web.
2.  **Tải/Biên dịch (Load/Compile)**:
    - Khi người dùng nhấn nút "Load" hoặc "Compile", mã hợp ngữ được gửi đến endpoint `/api/load` (hoặc `/api/compile`) trên server Flask.
    - `app.py` nhận mã và chuyển cho `Assembler`.
    - `Assembler` (`assembler.py`) thực hiện:
      - **Phân tích cú pháp (Parsing):** Tách mã thành các lệnh riêng lẻ, xác định opcode, toán hạng (operands), và nhãn (labels).
      - **Giải quyết nhãn (Label Resolution):** Thay thế các nhãn bằng địa chỉ bộ nhớ tương ứng.
      - **Tạo mã máy/Biểu diễn trung gian:** Chuyển đổi lệnh thành một định dạng mà `SimulatorEngine` có thể xử lý. Kết quả là một danh sách các lệnh đã được xử lý và thông tin về nhãn.
    - Dữ liệu đã xử lý này sau đó được nạp vào `SimulatorEngine` (`simulator_engine.py`) để chuẩn bị cho việc thực thi.
3.  **Thực thi từng bước (Micro-stepping)**:
    - Người dùng nhấn nút "Step" (hoặc tương tự) để thực thi một micro-step của lệnh hiện tại.
    - Yêu cầu được gửi đến endpoint `/api/micro_step`.
    - `SimulatorEngine` thực hiện một phần nhỏ của quá trình xử lý lệnh (ví dụ: chỉ giai đoạn Fetch, hoặc một phần của giai đoạn Decode).
    - Quá trình này thường được chia thành các giai đoạn chính của một pipeline CPU cổ điển, nhưng được mô phỏng tuần tự ở đây:
      - **IF (Instruction Fetch):** Lấy lệnh tiếp theo từ bộ nhớ dựa trên Program Counter (PC).
      - **ID (Instruction Decode & Register Fetch):** Giải mã lệnh để xác định thao tác cần thực hiện, đọc giá trị từ các thanh ghi cần thiết. `ControlUnit` tạo tín hiệu điều khiển.
      - **EX (Execute):** `ALU` thực hiện phép toán được chỉ định (ví dụ: cộng, trừ, so sánh).
      - **MEM (Memory Access):** Nếu là lệnh load/store, truy cập bộ nhớ để đọc hoặc ghi dữ liệu.
      - **WB (Write Back):** Nếu có, ghi kết quả trở lại vào thanh ghi.
    - `SimulatorEngine` cập nhật trạng thái nội bộ của nó (PC, thanh ghi, bộ nhớ) và trả về thông tin về micro-step vừa thực hiện, bao gồm các khối và đường dẫn dữ liệu nào đang hoạt động, giá trị của các tín hiệu điều khiển, và log chi tiết.
4.  **Cập nhật giao diện**:
    - `script.js` ở phía client nhận dữ liệu từ server.
    - Nó cập nhật giao diện người dùng để hiển thị:
      - Trạng thái hiện tại của các thanh ghi.
      - Nội dung bộ nhớ.
      - Lệnh đang được thực thi.
      - Đánh dấu các thành phần đang hoạt động trên hình ảnh SVG của đường dẫn dữ liệu.
      - Log mô phỏng.
5.  **Reset**: Người dùng có thể reset trình mô phỏng về trạng thái ban đầu thông qua endpoint `/api/reset`.

## Thiết lập và Chạy

1.  **Cài đặt dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
2.  **Chạy ứng dụng Flask**:
    ```bash
    python app.py
    ```
3.  Mở trình duyệt và truy cập vào địa chỉ được cung cấp (thường là `http://localhost:5010` hoặc `http://127.0.0.1:5010`).

## Giải thích chi tiết hơn về các thành phần

Để hiểu rõ hơn về cách từng phần hoạt động, vui lòng tham khảo các tài liệu sau:

- **`LEGv8_Architecture.md`**: Giải thích chi tiết về kiến trúc LEGv8, các định dạng lệnh và opcode.
- **`Simulator_Design.md`**: Mô tả thiết kế của các module trong trình mô phỏng (`assembler.py`, `simulator_engine.py`, `control_unit.py`, v.v.) và cách chúng tương tác.
- **`Code_Execution_Flow.md`**: Mô tả từng bước cách một lệnh được thực thi từ khi nạp đến khi hoàn thành.
