~/soda-compiler/src/sodac ${app}.soda --xocl-kernel ${app}_kernel.cpp --xocl-platform "$VITIS_DIR/aws_platform/xilinx_aws-vu9p-f1_shell-v04261818_201920_1"
g++ -std=c++0x tb_soda_${app}.cpp ${app}_kernel.cpp -I ../../../ -I ${XILINX_VIVADO}/include || { echo 'compilation failed'; exit 1; }
./a.out
