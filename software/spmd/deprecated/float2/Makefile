bsg_tiles_X = 2
bsg_tiles_Y = 2
#########################################################
#each bytes defines the core type
# 00: vanilla core
# 01  vscale  core
TYPE_VEC="64'h00_00_00_00"

#########################################################
#            FPU OPTION
#     The number of horizon node must be two and must 
#     be vanilla core 
BSG_FPU_OP=1

RISCV_GCC_EXTRA_OPTS ?= -O2 -funroll-loops
OBJECT_FILES=main.o bsg_set_tile_x_y.o cvt_sgn_class_test.o fam_test.o stall_fam_fpi_test.o fcsr_test.o fmac_test.o

include ../Makefile.include

all: main.run

main.riscv:  $(OBJECT_FILES) $(SPMD_COMMON_OBJECTS) ../common/crt.o
	$(RISCV_LINK) $(OBJECT_FILES) -o $@ $(RISCV_LINK_OPTS)

clean:
	-rm $(OBJECT_FILES) *.jou *.log *.pb bsg_manycore_io_complex_rom.v main.riscv *.wdb main.bin main.hex
	-rm -rf xsim.dir
	-rm -rf ./simv csrc simv.daidir ucli.key DVEfiles *.vpd

main.o: Makefile










