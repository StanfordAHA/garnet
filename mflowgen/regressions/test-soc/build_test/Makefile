CXDT_TESTS	:= discovery
TEST_DIR 		:= $(abspath $(ARM_IP_DIR)/software/testcodes/$(TESTNAME))
CXDT_DIR 		:= $(abspath $(ARM_IP_DIR)/software/coresight/validation)
CUR_DIR 		:= $(abspath .)
OBJ_DIR 		:= $(CUR_DIR)/cxdt

ifneq ($(filter $(CXDT_TESTS),$(TESTNAME)),)
	ADD_CFLAGS := ""
else
	ADD_CFLAGS := -I$(TEST_DIR)/bootcode
endif

all:
ifneq ($(filter $(CXDT_TESTS),$(TESTNAME)),)
	$(MAKE) cxdt
else
	$(MAKE) non_cxdt
endif


non_cxdt:
	cd $(TEST_DIR) ; \
	$(MAKE) ; \
	mkdir -p bootcode
	cp $(TEST_DIR)/$(TESTNAME).bin $(TEST_DIR)/bootcode/bin
	cd $(TEST_DIR)/bootcode ; \
	xxd -i bin bootcode.h
	cd $(CXDT_DIR) ; \
	$(MAKE) clean_image BIN_TAG=$(TESTNAME) TESTNAME=cxdt_boot; \
	$(MAKE) image TOOLCHAIN=gcc TESTNAME=cxdt_boot CXDT=1 CPU=NONE BIN_TAG=$(TESTNAME) ADD_CFLAG=-I$(TEST_DIR)/bootcode
	cp $(CXDT_DIR)/bin-$(TESTNAME)/cxdt_boot-CXDT-1-CPU-NONE/CXDT.bin outputs/
	cd $(TEST_DIR) ; \
	$(MAKE) clean ; \
	rm -rf bootcode

cxdt:
	cd $(CXDT_DIR) ; \
	$(MAKE) clean_image BIN_TAG=$(TESTNAME)  TESTNAME=$(TESTNAME); \
	$(MAKE) image TOOLCHAIN=gcc TESTNAME=$(TESTNAME) CXDT=1 CPU=NONE BIN_TAG=$(TESTNAME)
	cp $(CXDT_DIR)/bin-$(TESTNAME)/$(TEST_NAME)-CXDT-1-CPU-NONE/CXDT.bin outputs/
