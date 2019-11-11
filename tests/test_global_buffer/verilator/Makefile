MODULE_NAME = global_buffer
SRC_DIR := ../../../global_buffer/rtl
OBJ_DIR := ./obj_dir
SRC_FILES := $(wildcard $(SRC_DIR)/*)

all: test_$(MODULE_NAME)

obj_dir/V$(MODULE_NAME).mk: $(SRC_FILES)
	verilator $(MODULE_NAME).sv -cc -I$(SRC_DIR) -I$(SRC_DIR2) -O3 -Wno-fatal -exe test_$(MODULE_NAME).cpp --trace -CFLAGS "-std=c++11" 

test_$(MODULE_NAME): $(OBJ_DIR)/V$(MODULE_NAME).mk
	make -C $(OBJ_DIR) -f V$(MODULE_NAME).mk
	./$(OBJ_DIR)/V$(MODULE_NAME)

clean:
	rm -rf obj_dir/*

