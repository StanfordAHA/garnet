source ../../scripts/tool_settings.tcl
#### Route Design
routeDesign
setAnalysisMode -aocv true
saveDesign init_route.enc -def -tcon -verilog
optDesign -postRoute -hold -setup
