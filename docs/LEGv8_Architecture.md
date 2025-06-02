# Kiến trúc LEGv8

LEGv8 là một tập lệnh (Instruction Set Architecture - ISA) được thiết kế cho mục đích giáo dục, dựa trên kiến trúc ARMv8-A 64-bit. Nó đơn giản hóa một số khía cạnh của ARMv8 để dễ hiểu và triển khai hơn trong các trình mô phỏng và các khóa học về kiến trúc máy tính.

## Đặc điểm chính

- **Kiến trúc 64-bit:** Các thanh ghi và địa chỉ bộ nhớ đều là 64-bit.
- **Load-Store Architecture:** Chỉ các lệnh load (tải) và store (lưu trữ) mới có thể truy cập bộ nhớ. Các lệnh số học và logic chỉ hoạt động trên các giá trị trong thanh ghi hoặc giá trị tức thời (immediate values).
- **Tập thanh ghi (Register File):**
  - 32 thanh ghi đa dụng 64-bit: `X0` đến `X30`.
  - Thanh ghi Zero (`XZR` hoặc `X31`): Luôn có giá trị 0 khi đọc, và việc ghi vào nó không có tác dụng.
  - Program Counter (`PC`): Thanh ghi 64-bit chứa địa chỉ của lệnh tiếp theo sẽ được thực thi.
  - Thanh ghi trạng thái (`PSTATE` - Program Status Register): Chứa các cờ điều kiện (condition flags) như N (Negative), Z (Zero), C (Carry), V (Overflow).
- **Định dạng lệnh cố định:** Hầu hết các lệnh LEGv8 có độ dài cố định 32-bit.

## Các định dạng lệnh (Instruction Formats)

LEGv8 sử dụng các định dạng lệnh khác nhau để mã hóa các loại thao tác khác nhau. Các trường bit trong mỗi định dạng xác định opcode, thanh ghi nguồn, thanh ghi đích, và các giá trị tức thời.

### 1. R-format (Register format)

Sử dụng cho các lệnh thực hiện thao tác giữa các thanh ghi.

```
| opcode (11) | Rm (5) | shamt (6) | Rn (5) | Rd (5) |
```

- **opcode (11 bits):** Mã định danh thao tác (ví dụ: ADD, SUB, AND, ORR, EOR).
- **Rm (5 bits):** Thanh ghi nguồn thứ hai.
- **shamt (6 bits):** Số lượng bit dịch chuyển (shift amount), sử dụng cho các lệnh dịch chuyển.
- **Rn (5 bits):** Thanh ghi nguồn thứ nhất.
- **Rd (5 bits):** Thanh ghi đích, nơi kết quả được lưu trữ.

**Ví dụ:** `ADD X0, X1, X2` (X0 = X1 + X2)

### 2. I-format (Immediate format)

Sử dụng cho các lệnh thực hiện thao tác giữa một thanh ghi và một giá trị tức thời.

```
| opcode (10) | immediate (12) | Rn (5) | Rd (5) |
```

- **opcode (10 bits):** Mã định danh thao tác (ví dụ: ADDI, SUBI).
- **immediate (12 bits):** Giá trị tức thời (có dấu hoặc không dấu tùy lệnh).
- **Rn (5 bits):** Thanh ghi nguồn.
- **Rd (5 bits):** Thanh ghi đích.

**Ví dụ:** `ADDI X0, X1, #100` (X0 = X1 + 100)

### 3. D-format (Data transfer format)

Sử dụng cho các lệnh tải (load) và lưu trữ (store) dữ liệu giữa thanh ghi và bộ nhớ.

```
| opcode (11) | address (9) | op2 (2) | Rn (5) | Rt (5) |
```

- **opcode (11 bits):** Mã định danh thao tác (ví dụ: LDUR, STUR).
- **address (9 bits):** Địa chỉ offset (có dấu) so với địa chỉ cơ sở trong Rn.
- **op2 (2 bits):** Thường là 00 cho LDUR/STUR.
- **Rn (5 bits):** Thanh ghi chứa địa chỉ cơ sở.
- **Rt (5 bits):** Thanh ghi nguồn (cho store) hoặc thanh ghi đích (cho load).

**Ví dụ:** `LDUR X0, [X1, #8]` (Tải giá trị từ địa chỉ bộ nhớ [X1 + 8] vào X0)
`STUR X2, [X3, #16]` (Lưu giá trị từ X2 vào địa chỉ bộ nhớ [X3 + 16])

### 4. B-format (Unconditional Branch format)

Sử dụng cho các lệnh rẽ nhánh không điều kiện.

```
| opcode (6) | address (26) |
```

- **opcode (6 bits):** Mã định danh thao tác (ví dụ: B, BL).
- **address (26 bits):** Địa chỉ rẽ nhánh (có dấu, tương đối so với PC), được dịch trái 2 bit để tạo ra một offset 28-bit, cho phép nhảy trong phạm vi +/- 128MB.

**Ví dụ:** `B target_label` (Nhảy đến `target_label`)

### 5. CB-format (Conditional Branch format)

Sử dụng cho các lệnh rẽ nhánh có điều kiện dựa trên giá trị của một thanh ghi.

```
| opcode (8) | address (19) | Rt (5) |
```

- **opcode (8 bits):** Mã định danh thao tác (ví dụ: CBZ, CBNZ).
- **address (19 bits):** Địa chỉ rẽ nhánh (có dấu, tương đối so với PC), được dịch trái 2 bit.
- **Rt (5 bits):** Thanh ghi được kiểm tra điều kiện.

**Ví dụ:** `CBZ X0, target_label` (Nếu X0 bằng 0, nhảy đến `target_label`)

### 6. IW-format (Immediate Wide format)

Sử dụng cho các lệnh di chuyển một giá trị tức thời rộng (16-bit) vào một thanh ghi, có thể kèm theo dịch chuyển.

```
| opcode (11) | op2 (2) | immediate (16) | Rd (5) |
```

- **opcode (11 bits):** Mã định danh thao tác (ví dụ: MOVZ, MOVK).
- **op2 (2 bits):** Xác định vị trí dịch chuyển (LSL 0, LSL 16, LSL 32, LSL 48).
  - `00`: LSL 0
  - `01`: LSL 16
  - `10`: LSL 32
  - `11`: LSL 48
- **immediate (16 bits):** Giá trị tức thời 16-bit.
- **Rd (5 bits):** Thanh ghi đích.

**Ví dụ:** `MOVZ X0, #0x1234, LSL #16` (Di chuyển giá trị 0x1234 vào X0, sau đó dịch trái 16 bit. Các bit khác của X0 được xóa thành 0.)

## Opcode (Mã thao tác)

Opcode là phần của lệnh máy chỉ định thao tác sẽ được thực hiện. Trong LEGv8, độ dài của opcode thay đổi tùy theo định dạng lệnh.

- **R-format:** 11 bits
- **I-format:** 10 bits
- **D-format:** 11 bits
- **B-format:** 6 bits
- **CB-format:** 8 bits
- **IW-format:** 11 bits

Trình mô phỏng sử dụng opcode để:

1.  **Xác định loại lệnh:** Dựa vào các bit cao của lệnh.
2.  **Gửi tín hiệu điều khiển:** `ControlUnit` sẽ dựa vào opcode để tạo ra các tín hiệu điều khiển phù hợp cho các thành phần khác của đường dẫn dữ liệu (ALU, Memory, Register File).

### Một số Opcode phổ biến và ý nghĩa (ví dụ):

(Lưu ý: Giá trị opcode cụ thể là các số nhị phân, ở đây chỉ liệt kê tên lệnh tượng trưng)

- **Số học:**
  - `ADD`, `ADDI`: Cộng
  - `SUB`, `SUBI`, `SUBS`: Trừ (SUBS cập nhật cờ)
  - `MUL`: Nhân
  - `SDIV`, `UDIV`: Chia có dấu/không dấu
- **Logic:**
  - `AND`, `ANDI`: Phép AND bit
  - `ORR`, `ORRI`: Phép OR bit (ORR là OR Register)
  - `EOR`, `EORI`: Phép XOR bit (EOR là Exclusive OR)
- **Dịch chuyển:**
  - `LSL`: Dịch trái logic
  - `LSR`: Dịch phải logic
  - `ASR`: Dịch phải số học
- **Truy cập bộ nhớ:**
  - `LDUR`: Load Register (Unscaled offset) - Tải từ bộ nhớ vào thanh ghi
  - `STUR`: Store Register (Unscaled offset) - Lưu từ thanh ghi vào bộ nhớ
  - (LEGv8 còn có các lệnh load/store khác như `LDXR`, `STXR`, `LDPSW`, etc. nhưng `LDUR`/`STUR` là cơ bản)
- **Rẽ nhánh:**
  - `B`: Branch (nhảy không điều kiện)
  - `BL`: Branch with Link (nhảy và lưu địa chỉ trả về vào X30 - Link Register)
  - `BR`: Branch to Register (nhảy đến địa chỉ trong thanh ghi)
  - `CBZ`: Conditional Branch on Zero
  - `CBNZ`: Conditional Branch on Non-Zero
  - `B.cond`: Conditional Branch (ví dụ: `B.EQ` - Branch if Equal, `B.NE` - Branch if Not Equal, `B.LT` - Branch if Less Than, etc. dựa trên cờ PSTATE)
- **Di chuyển dữ liệu:**
  - `MOVZ`: Move Wide with Zero (chèn giá trị 16-bit vào một phần của thanh ghi, các phần khác là 0)
  - `MOVK`: Move Wide with Keep (chèn giá trị 16-bit vào một phần của thanh ghi, giữ nguyên các phần khác)
- **Đặc biệt:**
  - `NOP`: No Operation (thường được mã hóa bằng một lệnh không làm gì, ví dụ `AND XZR, XZR, XZR`)
  - `HLT`: Halt (dừng trình mô phỏng/CPU)

Việc hiểu rõ các định dạng lệnh và opcode là rất quan trọng để xây dựng trình biên dịch (assembler) và trình mô phỏng (simulator) cho kiến trúc LEGv8.
