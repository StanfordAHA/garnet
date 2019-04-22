# -u means just give me the name, don't create anything
# TMDIR := $(shell mktemp -u old_design_XXX)

# E.g. CLEANDIR=
TIMESTAMP := $(shell date +%y%m%d_%H%M)
CLEANDIR  := old_design_$(TIMESTAMP)


GENESIS_CORE_FILES := \
    genesis.log \
    genesis_work/ \
    genesis_raw/ \
    genesis_verif/ \
    genesis_synth/ \
    genesis_vlog.vf \
    genesis_vlog.synth.vf \
    genesis_vlog.verif.vf \
    genesis_clean.cmd

GENESIS_ADJUNCT_FILES := \
    MEMmemory_core \
    PEtest_pe \
    PECOMPtest_pe_comp_unq1 \
    REGMODEtest_opt_reg_file \
    REGMODEtest_opt_reg

GARNET_FILES := \
    garnet.v \
    garnet.json \
    __pycache__/ \
    parser.out \
    parsetab.py

clean:
	@echo Building cleanup dir $(CLEANDIR)...
	mkdir $(CLEANDIR)
	@echo ""

	@echo Moving core Genesis files...
	@echo mv $(GENESIS_CORE_FILES) $(CLEANDIR)/ | fold -s | sed 's/^/  /'
	@mv $(GENESIS_CORE_FILES) $(CLEANDIR)/
	@echo ""

	@echo Moving build-specific Genesis files...
	@echo mv $(GENESIS_ADJUNCT_FILES) $(CLEANDIR)/ | fold -s | sed 's/^/  /'
	@mv $(GENESIS_ADJUNCT_FILES) $(CLEANDIR)/
	@echo ""

	@echo Moving Garnet files...
	@echo mv $(GARNET_FILES) $(CLEANDIR)/ | fold -s | sed 's/^/  /'
	mv $(GARNET_FILES) $(CLEANDIR)/
	@echo ""

	ls -l $(CLEANDIR)

test:
	pytest

pytest:
	pytest

build:
	@echo "Example build:"
	@echo "  python garnet.py --width 2 --height 2"
	@echo ""

help:
	@echo "For help do this:"
	@echo "  python garnet.py --help"
	@echo ""
