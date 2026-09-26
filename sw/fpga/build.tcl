# Run from an ignored output directory; no generated Vivado files in sw/fpga.
set source_dir [file dirname [file normalize [info script]]]
read_verilog -sv [file join $source_dir rtl daqhat_01_link.sv]
read_xdc [file join $source_dir daqhat-01.xdc]
synth_design -top daqhat_01_link -part xc7a200tfbg484-1
opt_design
place_design
phys_opt_design
route_design
set timing_report [report_timing_summary -file timing.rpt -report_unconstrained -return_string]
set cdc_report [report_cdc -details -file cdc.rpt -return_string]
report_drc -file drc.rpt
report_utilization -file utilization.rpt
write_checkpoint -force daqhat-01-link.dcp
foreach category {no_clock constant_clock unconstrained_internal_endpoints multiple_clock loops latch_loops} {
    if {![regexp "checking $category \\(0\\)" $timing_report]} {
        error "Missing or failing timing coverage: $category"
    }
}
foreach delay {max min} {
    set paths [get_timing_paths -delay_type $delay -max_paths 1]
    if {[llength $paths] != 1 || [get_property SLACK $paths] < 0} {
        error "Missing or failing $delay timing path"
    }
}
if {[regexp {CDC-[0-9]+\s+(Critical|Warning)} $cdc_report]} {error "CDC review failed"}
if {[llength [get_drc_violations -quiet]] != 0} {error "FPGA DRC review failed"}
write_bitstream -force daqhat-01-link.bit
