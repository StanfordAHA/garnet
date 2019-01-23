


TAG ?= build_FFT2Top_final
top = FFT2Top
base_dir=$(abspath ../..)

default: drc

###################################

drcrundir = $(abspath .)/drcRunDir
lvsrundir = $(abspath .)/lvsRunDir
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
$(drcrundir)/$(top).innovus.gds: $(abspath .)/../flow/$(TAG)/dbs/postroute/$(top).merge.gds $(all_gdss) $(drcrundir)/rename.stamp
	echo -e 'layout filemerge \' > $(drcrundir)/$(merge_tcl)
	echo -e '-in $< $(merge_infiles) $(merge_infiles2) $(merge_options) -out $@' >> $(drcrundir)/$(merge_tcl)
	cd $(drcrundir); \
	calibredrv $(merge_tcl)

$(drcrundir)/FEOL.gds: $(drcrundir)/$(top).innovus.gds
	cp feol_deck.template $(drcrundir)/feol_deck
	sed -e 's|MYLAYOUT|$(top).innovus.gds|' -i $(drcrundir)/feol_deck
	sed -e 's|MYTOP|$(top)|' -i $(drcrundir)/feol_deck
	cd $(drcrundir); bsub -K calibre -64 -drc -hier -turbo -hyper feol_deck

$(drcrundir)/BEOL.gds: $(drcrundir)/$(top).innovus.gds
	cp beol_deck.template $(drcrundir)/beol_deck
	sed -e 's|MYLAYOUT|$(top).innovus.gds|' -i $(drcrundir)/beol_deck
	sed -e 's|MYTOP|$(top)|' -i $(drcrundir)/beol_deck
	cd $(drcrundir); bsub -K calibre -64 -drc -hier -turbo -hyper beol_deck

$(drcrundir)/COD.gds: $(drcrundir)/$(top).innovus.gds
	cp cut_deck.template $(drcrundir)/cut_deck
	sed -e 's|MYLAYOUT|$(top).innovus.gds|' -i $(drcrundir)/cut_deck
	sed -e 's|MYTOP|$(top)|' -i $(drcrundir)/cut_deck
	cd $(drcrundir); bsub -K calibre -64 -drc -hier -turbo -hyper cut_deck

$(drcrundir)/$(top).finish.gds: $(drcrundir)/FEOL.gds $(drcrundir)/BEOL.gds $(drcrundir)/COD.gds
	cp tile.template $(drcrundir)/tile
	sed -e 's|MYLAYOUT|$(top).innovus.gds|' -i $(drcrundir)/tile
	sed -e 's|MYTOP|$(top)|' -i $(drcrundir)/tile
	sed -e 's|MYDIR|$(drcrundir)|' -i $(drcrundir)/tile
	chmod u+x $(drcrundir)/tile
	$(drcrundir)/tile

finish: $(drcrundir)/$(top).finish.gds
	cp finish_deck.template $(drcrundir)/finish_deck
	sed -e 's|MYLAYOUT|$(top).finish.gds|' -i $(drcrundir)/finish_deck
	sed -e 's|MYTOP|$(top)|' -i $(drcrundir)/finish_deck
	cd $(drcrundir); calibre -64 -drc -hier -turbo -hyper finish_deck

antenna: $(drcrundir)/$(top).finish.gds
	cp antenna_deck.template $(drcrundir)/antenna_deck
	sed -e 's|MYLAYOUT|$(top).finish.gds|' -i $(drcrundir)/antenna_deck
	sed -e 's|MYTOP|$(top)|' -i $(drcrundir)/antenna_deck
	cd $(drcrundir); calibre -64 -drc -hier -turbo -hyper antenna_deck
	
bump: $(drcrundir)/$(top).finish.gds
	cp bump_deck.template $(drcrundir)/bump_deck
	sed -e 's|MYLAYOUT|$(top).finish.gds|' -i $(drcrundir)/bump_deck
	sed -e 's|MYTOP|$(top)|' -i $(drcrundir)/bump_deck
	cd $(drcrundir); calibre -64 -drc -hier -turbo -hyper bump_deck

drc: finish antenna bump

###################################

#LVS


spis = \
	$(wildcard $(abspath .)/../flow/tech/spice/*)

verilog = $(abspath .)/../flow/$(TAG)/dbs/postroute/$(top).lvs.v

$(lvsrundir)/$(top).netlist.spi: $(spis) $(verilog)
	mkdir -p $(lvsrundir)
	cd $(lvsrundir); v2lvs $(foreach spi, $(spis), $(addprefix -lsr , $(spi))) -v $(verilog) -o $(top).netlist.spi | tee v2lvs.log

$(lvsrundir)/lvs_include.net: $(lvsrundir)/$(top).netlist.spi
	echo -e '$(addprefix .INCLUDE ",$(addsuffix "\n,$(spis)))' > $@
	echo -e '$(addprefix .INCLUDE ",$(addsuffix "\n,$(top).netlist.spi))' >> $@
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
