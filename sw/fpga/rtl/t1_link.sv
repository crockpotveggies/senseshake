`timescale 1ns/1ps
// Conservative SPI mode-0 bring-up mailbox. 50 MHz clock, SPI <=1 MHz.
// All logic uses clk50; SPI pins are oversampled, never used as fabric clocks.
// A one-frame mailbox provides explicit backpressure. No quad capability.
module t1_link (
    input wire clk50, reset_n, sclk, cs_n, dq0,
    output wire dq1,
    inout wire dq2, dq3,
    input wire uart_rx,
    output wire uart_tx
);
    (* ASYNC_REG="TRUE" *) reg [2:0] rst_sync=0;
    always @(posedge clk50 or negedge reset_n)
        if (!reset_n) rst_sync<=0; else rst_sync<={rst_sync[1:0],1'b1};
    wire rst=!rst_sync[2];
    (* ASYNC_REG="TRUE" *) reg [2:0] ck=0, cs=7, di=0;
    always @(posedge clk50) begin
        ck<={ck[1:0],sclk}; cs<={cs[1:0],cs_n}; di<={di[1:0],dq0};
    end
    reg old_ck=0, old_cs=1;
    wire rise=ck[2]&&!old_ck, fall=!ck[2]&&old_ck;
    reg [7:0] memory [0:205];
    reg [7:0] rx=0, tx=0, command=0, error=0;
    reg [2:0] bits=0;
    reg [9:0] bytes_seen=0;
    reg ready=0, overflow=0;
    reg [15:0] ack=0;
    reg [31:0] crc=32'hffffffff;
    wire [7:0] received={rx[6:0],di[2]};
    wire [15:0] length={memory[9],memory[8]};
    wire [15:0] sequence_id={memory[7],memory[6]};
    wire [9:0] frame_length={2'b0,memory[8]}+10'd14;
    // Immediate CS disables output; synchronous logic prepares the next bit.
    assign dq1=cs_n ? 1'bz : tx[7];
    assign dq2=1'bz;
    assign dq3=1'bz;
    // Electrical UART loopback only; no software protocol is implied.
    assign uart_tx=uart_rx;

    function automatic [31:0] crc_byte(input [31:0] previous,input [7:0] data);
        reg [31:0] c; integer i;
        begin
            c=previous ^ {24'b0,data};
            for(i=0;i<8;i=i+1) c=c[0] ? (c>>1)^32'hedb88320 : c>>1;
            crc_byte=c;
        end
    endfunction
    function automatic [7:0] status_byte(input [9:0] index);
        begin
            case(index)
            0:status_byte=8'h53; 1:status_byte=8'h53;
            2:status_byte=8'h46; 3:status_byte=8'h50;
            4:status_byte=1; 5:status_byte=0;
            6:status_byte=ready?2:1; 7:status_byte=error;
            default:status_byte=0;
            endcase
        end
    endfunction
    always @(posedge clk50) begin
        old_ck<=ck[2]; old_cs<=cs[2];
        if(rst) begin
            rx<=0;tx<=0;command<=0;error<=0;bits<=0;bytes_seen<=0;
            ready<=0;overflow<=0;ack<=0;crc<=32'hffffffff;
        end else if(!cs[2] && old_cs) begin
            rx<=0;tx<=0;command<=0;bits<=0;bytes_seen<=0;
            overflow<=0;ack<=0;crc<=32'hffffffff;
        end else if(cs[2] && !old_cs) begin
            // Commit only after a complete CS-delimited transaction.
            if(bits!=0 || bytes_seen==0) error<=4;
            else case(command)
            0: if(bytes_seen!=9) error<=4;
            1: if(ready) error<=5;
               else if(overflow || bytes_seen>207) error<=1;
               else if(bytes_seen<15 || length>192 || bytes_seen!=frame_length+1
                    || memory[0]!=8'h53 || memory[1]!=8'h53
                    || memory[2]!=8'h46 || memory[3]!=8'h50
                    || memory[4]!=1 || memory[5]!=1) error<=2;
               // CRC-32/IEEE residue includes the transmitted little-endian CRC.
               else if(crc!=32'hdebb20e3) error<=3;
               else if(error==0) ready<=1;
            2: if(!ready || bytes_seen!=207) error<=4;
            3: if(bytes_seen!=3 || !ready || ack!=sequence_id) error<=6;
               else ready<=0;
            default:error<=7;
            endcase
        end else if(!cs[2]) begin
            if(rise) begin
                rx<=received; bits<=bits+1'b1;
                if(bits==7) begin
                    if(bytes_seen<1023) bytes_seen<=bytes_seen+1'b1;
                    else overflow<=1;
                    if(bytes_seen==0) command<=received;
                    else if(command==1 && !ready) begin
                        if(bytes_seen<=206) begin
                            memory[bytes_seen-1]<=received;
                            crc<=crc_byte(crc,received);
                        end else overflow<=1;
                    end else if(command==3) begin
                        if(bytes_seen==1) ack[7:0]<=received;
                        if(bytes_seen==2) ack[15:8]<=received;
                    end
                end
            end
            if(fall) begin
                if(bits==0) begin
                    case(command)
                    0:tx<=status_byte(bytes_seen-1);
                    2:tx<=(ready && bytes_seen>=1 && bytes_seen<=frame_length)
                             ? memory[bytes_seen-1] : 0;
                    default:tx<=0;
                    endcase
                end else tx<={tx[6:0],1'b0};
            end
        end
    end
endmodule
