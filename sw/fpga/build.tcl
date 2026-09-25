# Run from an ignored output directory; no generated Vivado files in sw/fpga.
set source_dir [file dirname [file normalize [info script]]]
read_verilog -sv [file join $source_dir rtl t1_link.sv]
read_xdc [file join $source_dir t1.xdc]
synth_design -top t1_link -part xc7a200tfbg484-1
opt_design
place_design
phys_opt_design
route_design
report_timing_summary -file timing.rpt -report_unconstrained
report_cdc -details -file cdc.rpt
report_drc -file drc.rpt
report_utilization -file utilization.rpt
write_checkpoint -force t1-link.dcp
if {[get_property SLACK [get_timing_paths -delay_type max -max_paths 1]] < 0} {
    error "Setup timing failed"
}
if {[get_property SLACK [get_timing_paths -delay_type min -max_paths 1]] < 0} {
    error "Hold timing failed"
}
write_bitstream -force t1-link.bit
