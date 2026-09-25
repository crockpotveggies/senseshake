`timescale 1ns/1ps
// Interactive physical-pin peer for the production Python packet client.
module tb_host;
    reg clk=0,rst=0,sck=0,cs=1,mosi=0,uart=1;
    wire miso,dq2,dq3,utx;
    t1_link dut(clk,rst,sck,cs,mosi,miso,dq2,dq3,uart,utx);
    always #10 clk=~clk;
    integer op,count,low_ns,high_ns,phase,partial,rc,n,b,value;
    reg [7:0] answer[0:1099];
    initial begin
        forever begin
            rc=$fscanf(32'h80000000,"%d %d %d %d %d %d",op,count,low_ns,high_ns,phase,partial);
            if(rc!=6)$finish;
            if(op==0)begin
                cs=1;sck=0;rst=0;#317;rst=1;#1000;
            end else begin
                if(count<0 || count>1100 || low_ns<500 || high_ns<500)$fatal(1,"bad stimulus");
                #(phase);cs=0;#1000;
                for(n=0;n<count;n=n+1)begin
                    rc=$fscanf(32'h80000000,"%h",value);
                    if(rc!=1)$fatal(1,"missing byte");
                    for(b=7;b>=0;b=b-1)begin
                        mosi=(value>>b)&1;#(low_ns);sck=1;
                        #1;answer[n][b]=miso;#(high_ns-1);sck=0;
                    end
                end
                for(b=0;b<partial;b=b+1)begin
                    mosi=1;#(low_ns);sck=1;#(high_ns);sck=0;
                end
                if(op==3)begin
                    rst=0;#1;if(miso!==1'bz)$fatal(1,"reset must release MISO");
                    #316;rst=1;#1000;
                end
                #1000;cs=1;#1000;
            end
            if(miso!==1'bz || dq2!==1'bz || dq3!==1'bz)$fatal(1,"idle bus contention");
            $write("RX ");
            if(op!=0)for(n=0;n<count;n=n+1)$write("%02x",answer[n]);
            $write("\n");$fflush();
        end
    end
endmodule
