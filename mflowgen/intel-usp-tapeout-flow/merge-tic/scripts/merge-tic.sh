
# Usage
# calibredrv -64 layout_merge_calibre.tcl \
#    <convert|fill_merge|merge|filemerge> top_layout output_layout layout_format <list_of_merge_files>
calibredrv -HC -64 -threads 16 ./inputs/adk/layout_merge_calibre.tcl \
    merge \
    ./inputs/design.oas \
    ./outputs/design.oas \
    oas \
    ./inputs/adk/intel22custom.oas \
    ./inputs/adk/intel22sram.oas \
    ./inputs/adk/intel22rf.oas \
    ./inputs/adk/intel22tic.oas \
    > design-merge-tic.log 2>&1

# Not sure if these are needed, because they are already merged in innovus
    # ./inputs/sram_1.oas \
    # ./inputs/sram_2.oas \
    # ./inputs/adk/guardring.oas \
    # ./inputs/adk/ring_terminator_e1.oas \
    # ./inputs/adk/ring_terminator_n1.oas \
    # ./inputs/adk/sdio_1v8_e1.oas \
    # ./inputs/adk/sdio_1v8_n1.oas \
    # ./inputs/adk/spacer_2lego_e1.oas \
    # ./inputs/adk/spacer_2lego_n1.oas \
    # ./inputs/adk/sup1v8_e1.oas \
    # ./inputs/adk/sup1v8_n1.oas \
    # ./inputs/adk/corner_nw1.oas \