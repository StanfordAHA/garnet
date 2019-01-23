


TAG ?= build_FFT2Top_final
step = postroute
top = FFT2Top
base_dir=$(abspath ../../)

default: drc

###################################

drcrundir ?= $(abspath .)/drcRunDir
lvsrundir ?= $(abspath .)/lvsRunDir
SITE_CALIBRE_LSF_SMT_RUNSET_FILE = $(abspath .)/lsf_runset

merge_tcl = merge_all.tcl

serdes_gds = $(abspath .)/../flow/tech/gds/serdes_afe.gds
rxadc_gds = $(abspath .)/../flow/tech/gds/RX_ADC_TOP.gds
tisar_gds = $(abspath .)/../flow/tech/gds/TISARADC_SFFT.gds
clkrx_gds = $(abspath .)/../flow/tech/gds/CLK_RX_amp_buf.gds

rename_gds = $(serdes_gds) $(rxadc_gds) $(tisar_gds) $(clkrx_gds)
merge_infiles2 = $(foreach gds_file, $(addprefix $(drcrundir)/, $(notdir $(rename_gds))), -in $(gds_file))

all_gdss = $(filter-out $(rename_gds), $(wildcard $(abspath .)/../flow/tech/gds/*))
merge_infiles = $(foreach gds_file, $(all_gdss), -in $(gds_file) )
merge_options = -overwrite -topcell $(top)

###################################

#DRC

# uniquify IP
$(drcrundir)/rename.stamp: $(rename_gds)
	mkdir -p $(drcrundir)
	calibredrv -a "layout filemerge -in $(serdes_gds) -in $(rxadc_gds) -in $(tisar_gds) -in $(clkrx_gds) -out $(drcrundir)/rename.gds -mode forcerename"
	calibredrv -a "set L0 [layout create $(drcrundir)/rename.gds -dt_expand -preserveTextAttributes -preserveProperties]; \$$L0 cellname RX_ADC_TOP_WB2 RX_ADC_TOP; \$$L0 cellname serdes_afe_WB1 serdes_afe; \$$L0 cellname TISARADC_SFFT_WB3 TISARADC_SFFT; \$$L0 cellname CLK_RX_amp_buf_WB4 CLK_RX_amp_buf; \$$L0 gdsout $(drcrundir)/CLK_RX_amp_buf.gds CLK_RX_amp_buf; \$$L0 gdsout $(drcrundir)/serdes_afe.gds serdes_afe; \$$L0 gdsout $(drcrundir)/RX_ADC_TOP.gds RX_ADC_TOP; \$$L0 gdsout $(drcrundir)/TISARADC_SFFT.gds TISARADC_SFFT"
	touch $(drcrundir)/rename.stamp

# remerge because Innovus messes things up
$(drcrundir)/$(top).innovus.gds: $(abspath .)/../flow/$(TAG)/dbs/$(step)/$(top).merge.gds $(all_gdss) $(drcrundir)/rename.stamp
	echo -e 'layout filemerge \' > $(drcrundir)/$(merge_tcl)
	echo -e '-in $< $(merge_infiles) $(merge_infiles2) $(merge_options) -out $@' >> $(drcrundir)/$(merge_tcl)
	cd $(drcrundir); \
	calibredrv $(merge_tcl)

prefill: $(drcrundir)/$(top).innovus.gds
	cp prefill_deck.template $(drcrundir)/prefill_deck
	sed -e 's|MYLAYOUT|$(top).innovus.gds|' -i $(drcrundir)/prefill_deck
	sed -e 's|MYTOP|$(top)|' -i $(drcrundir)/prefill_deck
	cd $(drcrundir); calibre -64 -drc -hier -turbo -hyper prefill_deck

antenna: $(drcrundir)/$(top).innovus.gds
	cp antenna_deck.template $(drcrundir)/antenna_deck
	sed -e 's|MYLAYOUT|$(top).innovus.gds|' -i $(drcrundir)/antenna_deck
	sed -e 's|MYTOP|$(top)|' -i $(drcrundir)/antenna_deck
	cd $(drcrundir); calibre -64 -drc -hier -turbo -hyper antenna_deck

bump: $(drcrundir)/$(top).innovus.gds
	cp bump_deck.template $(drcrundir)/bump_deck
	sed -e 's|MYLAYOUT|$(top).innovus.gds|' -i $(drcrundir)/bump_deck
	sed -e 's|MYTOP|$(top)|' -i $(drcrundir)/bump_deck
	cd $(drcrundir); calibre -64 -drc -hier -turbo -hyper bump_deck

drc: prefill antenna bump

###################################

#LVS


spis = \
	$(wildcard $(abspath .)/../flow/tech/spice/*)

verilog = $(abspath .)/../flow/$(TAG)/dbs/postroute/$(top).lvs.v

# uniqify IP
serdes_spi = $(abspath .)/../flow/tech/spice/serdes_afe.spi
rxadc_spi =  $(abspath .)/../flow/tech/spice/RX_ADC_TOP.spi
tisar_spi =  $(abspath .)/../flow/tech/spice/TISARADC_SFFT.spi
clkrx_spi =  $(abspath .)/../flow/tech/spice/CLK_RX_amp_buf.spi
mem_spi =  $(wildcard $(abspath .)/../flow/tech/spice/ts*.spi)

uc = $(subst a,A,$(subst b,B,$(subst c,C,$(subst d,D,$(subst e,E,$(subst f,F,$(subst g,G,$(subst h,H,$(subst i,I,$(subst j,J,$(subst k,K,$(subst l,L,$(subst m,M,$(subst n,N,$(subst o,O,$(subst p,P,$(subst q,Q,$(subst r,R,$(subst s,S,$(subst t,T,$(subst u,U,$(subst v,V,$(subst w,W,$(subst x,X,$(subst y,Y,$(subst z,Z,$1))))))))))))))))))))))))))
rename_spi = $(serdes_spi) $(rxadc_spi) $(tisar_spi) $(clkrx_spi)
spis2 = $(foreach spi_file, $(addprefix $(lvsrundir)/, $(notdir $(rename_spi))), $(spi_file))
spis3 = $(foreach spi_file, $(addprefix $(lvsrundir)/, $(notdir $(mem_spi))), $(spi_file))
py_arg = $(foreach spi_file, $(spis2), $(spi_file) $(basename $(notdir $(spi_file)))) $(foreach spi_file, $(spis3), $(spi_file) $(call uc,$(subst _100a,,$(basename $(notdir $(spi_file))))))
all_spis = $(filter-out $(rename_spi) $(mem_spi), $(spis))

$(lvsrundir)/rename.stamp: $(rename_spi) $(abspath .)/rename/uniquify_netlists.py
	mkdir -p $(lvsrundir)
	cp $(rename_spi) $(mem_spi) $(lvsrundir)
	$(abspath .)/rename/uniquify_netlists.py $(py_arg)

#$(lvsrundir)/$(top).netlist.spi: $(all_spis) $(verilog) $(lvsrundir)/rename.stamp
#	cd $(lvsrundir); v2lvs $(foreach spi, $(all_spis), $(addprefix -lsr , $(spi)))  $(foreach spi, $(spis2), $(addprefix -lsr , $(spi))) -v $(verilog) -o $(top).netlist.spi | tee v2lvs.log

$(lvsrundir)/lvs_include.net: $(lvsrundir)/rename.stamp
	echo -e '$(addprefix .INCLUDE ",$(addsuffix "\n,$(all_spis)))' > $@
	echo -e '$(addprefix .INCLUDE ",$(addsuffix "\n,$(spis2)))' >> $@
	echo -e '$(addprefix .INCLUDE ",$(addsuffix "\n,$(spis3)))' >> $@
	echo -e '$(addprefix .INCLUDE ",$(addsuffix "\n,/tools/tstech16/CLN16FFC/PDK/Calibre/lvs/source.added))' >> $@
	
lvs: $(lvsrundir)/lvs_include.net $(drcrundir)/$(top).innovus.gds
	#cp lvs_deck.template $(lvsrundir)/lvs_deck
	#sed -e 's|MYLAYOUT|$(drcrundir)/$(top).innovus.gds|' -i $(lvsrundir)/lvs_deck
	#sed -e 's|MYTOP|$(top)|' -i $(lvsrundir)/lvs_deck
	#sed -e 's|MYSOURCE|lvs_include.net|' -i $(lvsrundir)/lvs_deck
	#cd $(lvsrundir); calibre -64 -lvs -hier -turbo -spice FFT2Top.layout.spi -hyper lvs_deck

###################################

clean:
	rm -rf $(drcrundir) $(lvsrundir)
