
def first_half_of_body(f):
    string = """/* Linker Script
*
* It defines following symbols, which code can use without definition:
*   __exidx_start
*   __exidx_end
*   __copy_table_start__
*   __copy_table_end__
*   __zero_table_start__
*   __zero_table_end__
*   __etext
*   __data_start__
*   __preinit_array_start
*   __preinit_array_end
*   __init_array_start
*   __init_array_end
*   __fini_array_start
*   __fini_array_end
*   __data_end__
*   __bss_start__
*   __bss_end__
*   __end__
*   end
*   __HeapLimit
*   __StackLimit
*   __StackTop
*   __stack
*/

__STACK_SIZE = 1024;
__HEAP_SIZE = 2048;

ENTRY(_start)"""
    f.write(string)


def bottom_half_of_body(f):
    string = """

.isr_vectors : ALIGN(4)
{
    __vectors_start = ABSOLUTE(.);
    KEEP(*(.isr_vectors))
    *(.after_vectors .after_vectors.*)
} > FLASH

.text :
{

    *(.text*)

    KEEP(*(.init))
    KEEP(*(.fini))

    /* .ctors */
    *crtbegin.o(.ctors)
    *crtbegin?.o(.ctors)
    *(EXCLUDE_FILE(*crtend?.o *crtend.o) .ctors)
    *(SORT(.ctors.*))
    *(.ctors)

    /* .dtors */
    *crtbegin.o(.dtors)
    *crtbegin?.o(.dtors)
    *(EXCLUDE_FILE(*crtend?.o *crtend.o) .dtors)
    *(SORT(.dtors.*))
    *(.dtors)

    *(.rodata .rodata.* .constdata .constdata.*)

    *(vtable) /* C++ virtual tables */

    KEEP(*(.eh_frame*))
} > FLASH

/*
* SG veneers:
* All SG veneers are placed in the special output section .gnu.sgstubs. Its start address
* must be set, either with the command line option ‘--section-start’ or in a linker script,
* to indicate where to place these veneers in memory.
*/
/*
.gnu.sgstubs :
{
    . = ALIGN(32);
} > FLASH
*/
.ARM.extab :
{
    *(.ARM.extab* .gnu.linkonce.armextab.*)
} > FLASH

__exidx_start = .;
.ARM.exidx :
{
    *(.ARM.exidx* .gnu.linkonce.armexidx.*)
} > FLASH
__exidx_end = .;

.copy.table :
{
    . = ALIGN(4);
    __copy_table_start__ = .;

    LONG (__etext)
    LONG (__data_start__)
    LONG ((__data_end__ - __data_start__) / 4)

    __copy_table_end__ = .;
} > FLASH

/**
* Location counter can end up 2byte aligned with narrow Thumb code but
* __etext is assumed by startup code to be the LMA of a section in RAM
* which must be 4byte aligned
*/
__etext = ALIGN (4);

.data :
{
    __data_start__ = .;
    *(.data)
    *(.data.*)

    . = ALIGN(4);
    /* preinit data */
    PROVIDE_HIDDEN (__preinit_array_start = .);
    KEEP(*(.preinit_array))
    PROVIDE_HIDDEN (__preinit_array_end = .);

    . = ALIGN(4);
    /* init data */
    PROVIDE_HIDDEN (__init_array_start = .);
    KEEP(*(SORT(.init_array.*)))
    KEEP(*(.init_array))
    PROVIDE_HIDDEN (__init_array_end = .);

    . = ALIGN(4);
    /* finit data */
    PROVIDE_HIDDEN (__fini_array_start = .);
    KEEP(*(SORT(.fini_array.*)))
    KEEP(*(.fini_array))
    PROVIDE_HIDDEN (__fini_array_end = .);

    KEEP(*(.jcr*))
    . = ALIGN(4);
    /* All data end */
    __data_end__ = .;

} > RAM AT > RAM

.bss :
{
    . = ALIGN(4);
    __bss_start__ = .;
    *(.bss)
    *(.bss.*)
    *(COMMON)
    . = ALIGN(4);
    __bss_end__ = .;
} > RAM AT > RAM

.heap (COPY) :
{
    . = ALIGN(8);
    __end__ = .;
    PROVIDE(end = .);
    . = . + __HEAP_SIZE;
    . = ALIGN(8);
    __HeapLimit = .;
} > RAM

.stack (ORIGIN(RAM) + LENGTH(RAM) - __STACK_SIZE) (COPY) :
{
    . = ALIGN(8);
    __StackLimit = .;
    . = . + __STACK_SIZE;
    . = ALIGN(8);
    __StackTop = .;
} > RAM
PROVIDE(__stack = __StackTop);

/* Check if data + heap + stack exceeds RAM limit */
ASSERT(__StackLimit >= __HeapLimit, "region RAM overflowed with stack")

/* This can remove the debugging information from the standard libraries */
/*
DISCARD :
{
libc.a ( * )
libm.a ( * )
libgcc.a ( * )
}
*/

/* Stabs debugging sections.  */
.stab          0 : { *(.stab) }
.stabstr       0 : { *(.stabstr) }
.stab.excl     0 : { *(.stab.excl) }
.stab.exclstr  0 : { *(.stab.exclstr) }
.stab.index    0 : { *(.stab.index) }
.stab.indexstr 0 : { *(.stab.indexstr) }
.comment       0 : { *(.comment) }
/*
* DWARF debug sections.
* Symbols in the DWARF debugging sections are relative to the beginning
* of the section so we begin them at 0.
*/
/* DWARF 1 */
.debug          0 : { *(.debug) }
.line           0 : { *(.line) }
/* GNU DWARF 1 extensions */
.debug_srcinfo  0 : { *(.debug_srcinfo) }
.debug_sfnames  0 : { *(.debug_sfnames) }
/* DWARF 1.1 and DWARF 2 */
.debug_aranges  0 : { *(.debug_aranges) }
.debug_pubnames 0 : { *(.debug_pubnames) }
/* DWARF 2 */
.debug_info     0 : { *(.debug_info .gnu.linkonce.wi.*) }
.debug_abbrev   0 : { *(.debug_abbrev) }
.debug_line     0 : { *(.debug_line) }
.debug_frame    0 : { *(.debug_frame) }
.debug_str      0 : { *(.debug_str) }
.debug_loc      0 : { *(.debug_loc) }
.debug_macinfo  0 : { *(.debug_macinfo) }
/* SGI/MIPS DWARF 2 extensions */
.debug_weaknames 0 : { *(.debug_weaknames) }
.debug_funcnames 0 : { *(.debug_funcnames) }
.debug_typenames 0 : { *(.debug_typenames) }
.debug_varnames  0 : { *(.debug_varnames) }
}"""
    f.write(string)


def write_sections(f, app_name):
    if "mat" in app_name:
        #matrix app
        if "matmul" in app_name:
            string = """SECTIONS
{

.data_at_specific_location 0x20400000 : {
    *(.app_tensor_B_mode_0_data)
    KEEP(*(.app_tensor_B_mode_0_data))
}
.data_at_specific_location 0x20440000 : {
    *(.app_tensor_C_mode_0_data)
    KEEP(*(.app_tensor_C_mode_0_data))
}
.data_at_specific_location 0x20480000 : {
    *(.app_tensor_B_mode_1_data)
    KEEP(*(.app_tensor_B_mode_1_data))
}
.data_at_specific_location 0x204C0000 : {
    *(.app_tensor_C_mode_1_data)
    KEEP(*(.app_tensor_C_mode_1_data))
}
.data_at_specific_location 0x20500000 : {
    *(.app_tensor_B_mode_vals_data)
    KEEP(*(.app_tensor_B_mode_vals_data))
}
.data_at_specific_location 0x20540000 : {
    *(.app_tensor_C_mode_vals_data)
    KEEP(*(.app_tensor_C_mode_vals_data))
}"""
        else:
            string = """SECTIONS
{

.data_at_specific_location 0x20400000 : {
    *(.app_tensor_B_mode_0_data)
    KEEP(*(.app_tensor_B_mode_0_data))
}
.data_at_specific_location 0x20440000 : {
    *(.app_tensor_B_mode_1_data)
    KEEP(*(.app_tensor_B_mode_1_data))
}
.data_at_specific_location 0x20480000 : {
    *(.app_tensor_C_mode_1_data)
    KEEP(*(.app_tensor_C_mode_1_data))
}
.data_at_specific_location 0x204C0000 : {
    *(.app_tensor_C_mode_0_data)
    KEEP(*(.app_tensor_C_mode_0_data))
}
.data_at_specific_location 0x20500000 : {
    *(.app_tensor_B_mode_vals_data)
    KEEP(*(.app_tensor_B_mode_vals_data))
}
.data_at_specific_location 0x20540000 : {
    *(.app_tensor_C_mode_vals_data)
    KEEP(*(.app_tensor_C_mode_vals_data))
}"""
    f.write(string)

def generate_linker(linker_name, app_name):
    f = open(linker_name, "w")

    first_half_of_body(f)
    write_sections(f, app_name)
    bottom_half_of_body(f)

    f.close()