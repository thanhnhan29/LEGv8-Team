
_start:
        // x = 10, y = 10
        ADDI    X1, XZR, 10      // x
        ADDI    X2, XZR, 10      // y

        SUBS    XZR, X1, X2      // cập nhật cờ, bỏ kết quả

        // Nhảy nếu bằng
        B.EQ    if_equal

        // Nếu không bằng, result = 0
        ADDI    X3, XZR, 0
        B       end

if_equal:
        ADDI    X3, XZR, 1

end:
        // result trong X3