module alu_clean (
    input [1:0] op, input [3:0] a, input [3:0] b, output reg [3:0] out, output reg cout
);
    wire [4:0] sum, diff;
    assign sum = a + b;
    assign diff = a - b;

    always @(*) begin
        out = 4'b0000; cout = 1'b0;
        case (op)
            2'b00: begin    //Add
                out = sum[3:0];
                cout = sum[4];
            end
            2'b01: begin    //Subtract
                out = diff[3:0];
                cout = diff[4];
            end
            2'b10: begin    //And
                out = a & b;
            end
            2'b11: begin    //Or
                out = a | b;
            end
            default: begin
                out = 4'b0000;
                cout = 1'b0;
            end
        endcase
    end
endmodule