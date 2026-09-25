`timescale 1ns/1ps
module tb_link;
    reg clk=0,rst=0,sck=0,cs=1,mosi=0,uart=1;
    wire miso,dq2,dq3,utx;
    t1_link dut(clk,rst,sck,cs,mosi,miso,dq2,dq3,uart,utx);
    always #10 clk=~clk;
    reg [7:0] frame[0:205], result[0:205], rx;
    integer length,i,k,checks=0;
    reg [31:0] crc;
    task reset_peer;
        begin cs=1;sck=0;rst=0;#317;rst=1;#1000; end
    endtask
    task start;
        begin cs=0;#1103;end
    endtask
    task stop;
        begin #1003;cs=1;#1107;end
    endtask
    task byte_io(input [7:0] data,output [7:0] value);
        integer b;
        begin
            for(b=7;b>=0;b=b-1) begin
                mosi=data[b];#503;sck=1;#1;value[b]=miso;#500;sck=0;
            end
            #503;
        end
    endtask
    task status(input [7:0] flags,input [7:0] error);
        reg [7:0] expected;
        integer n;
        begin
            start;byte_io(0,rx);
            for(n=0;n<8;n=n+1) begin
                byte_io(0,rx);
                case(n)
                0,1:expected=8'h53;2:expected=8'h46;3:expected=8'h50;
                4:expected=1;5:expected=0;6:expected=flags;7:expected=error;
                endcase
                if(rx!==expected)$fatal(1,"status byte %d expected %h got %h",n,expected,rx);
            end
            stop;checks=checks+1;
        end
    endtask
    task make_frame(input integer size);
        integer n,b;
        begin
            length=size+14;
            frame[0]=8'h53;frame[1]=8'h53;frame[2]=8'h46;frame[3]=8'h50;
            frame[4]=1;frame[5]=1;frame[6]=8'h39;frame[7]=8'hc2;
            frame[8]=size;frame[9]=0;
            for(n=0;n<size;n=n+1)frame[10+n]=(n*73+29)&255;
            crc=32'hffffffff;
            for(n=0;n<size+10;n=n+1)begin
                crc=crc^frame[n];
                for(b=0;b<8;b=b+1)begin
                    if(crc[0])crc=(crc>>1)^32'hedb88320;else crc=crc>>1;
                end
            end
            crc=~crc;
            for(n=0;n<4;n=n+1)frame[size+10+n]=(crc>>(8*n))&255;
        end
    endtask
    task write_frame(input integer count);
        integer n;
        begin
            start;byte_io(1,rx);
            for(n=0;n<count;n=n+1)byte_io(n<206?frame[n]:8'hff,rx);
            stop;
        end
    endtask
    task read_frame;
        integer n;
        begin
            start;byte_io(2,rx);
            for(n=0;n<206;n=n+1)begin
                byte_io(0,rx);result[n]=rx;
                if(rx!==(n<length?frame[n]:8'h00))$fatal(1,"payload mismatch %d",n);
            end
            stop;checks=checks+1;
        end
    endtask
    task acknowledge(input [15:0] seq);
        begin start;byte_io(3,rx);byte_io(seq[7:0],rx);byte_io(seq[15:8],rx);stop;end
    endtask
    initial begin
        reset_peer;status(1,0);
        if(miso!==1'bz || dq2!==1'bz || dq3!==1'bz)$fatal(1,"idle contention");
        uart=0;#1;if(utx!==0)$fatal(1,"UART");uart=1;
        // Empty, short and maximum payload, repeated reads until matching ACK.
        for(k=0;k<3;k=k+1)begin
            make_frame(k==0?0:k==1?17:192);write_frame(length);status(2,0);
            read_frame;read_frame;acknowledge(16'hc239);status(1,0);
        end
        // CRC corruption, truncated frame, overflow, unsupported operation.
        make_frame(17);frame[12]=frame[12]^1;write_frame(length);status(1,3);
        reset_peer;make_frame(17);write_frame(length-1);status(1,2);
        reset_peer;make_frame(192);write_frame(220);status(1,1);
        reset_peer;start;byte_io(8'h80,rx);stop;status(1,7);
        // Busy mailbox never overwrites existing result; wrong ACK retains it.
        reset_peer;make_frame(17);write_frame(length);write_frame(length);status(2,5);read_frame;
        reset_peer;make_frame(17);write_frame(length);acknowledge(0);status(2,6);read_frame;
        // Partial byte abort and reset during a transaction recover to empty.
        reset_peer;start;mosi=1;#503;sck=1;#503;sck=0;stop;status(1,4);
        reset_peer;start;byte_io(1,rx);byte_io(8'h53,rx);reset_peer;status(1,0);
        $display("PASS RTL: %0d checked status/read transactions, bounds/CRC/abort/reset/backpressure/UART/tri-state",checks);
        $finish;
    end
    initial begin #50000000;$fatal(1,"simulation timeout");end
endmodule
