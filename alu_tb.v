module alu_tb;
    reg [1:0] op;
    reg [3:0] a, b;
    wire [3:0] out_clean;
    wire cout_clean;
    wire [3:0] out_trojan;
    wire cout_trojan;
    wire [3:0] out_error;
    wire cout_error;
    assign out_error = out_clean ^ out_trojan;
    assign cout_error = cout_clean ^ cout_trojan;
    integer i, j, k;

    alu_clean dut(
        .op(op),
        .a(a),
        .b(b),
        .out(out_clean),
        .cout(cout_clean)
    );

    alu_trojan dut_trojan(
        .op(op),
        .a(a),
        .b(b),
        .out(out_trojan),
        .cout(cout_trojan)
    );

    initial begin
        for (i = 0; i < 16; i = i + 1) begin
            a = i[3:0];
            for (j = 0; j < 16; j = j + 1) begin
                b = j[3:0];
                for (k = 0; k < 4; k = k + 1) begin
                    op = k[1:0];
                    #10;
                end
            end
        end
        $finish;
    end

    initial begin 
        $dumpfile("alu_tb.vcd");
        $dumpvars(0, alu_tb);
    end

endmodule