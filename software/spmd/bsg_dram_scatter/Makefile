
bsg_tiles_X = 3
bsg_tiles_Y = 1

RISCV_GCC_EXTRA_OPTS += -O2 #-DBSG_TOKEN_QUEUE_SHORT
# -funroll-loops
OBJECT_FILES=main.o bsg_set_tile_x_y.o
include ../Makefile.include

all: main.run

main.riscv:  $(OBJECT_FILES) $(SPMD_COMMON_OBJECTS) ../common/crt.o
	$(RISCV_LINK) $(OBJECT_FILES) -o $@ $(RISCV_LINK_OPTS) 

clean:
	-rm -rf $(OBJECT_FILES) *.jou *.log *.pb bsg_rom_hello.v main.riscv *.wdb main.bin main.hex *.cfg.h
	-rm -rf xsim.dir
	-rm -rf simv csrc simv.daidir ucli.key bsg_manycore_io_complex_rom.v *.vpd

main.o: Makefile


verify: main.c
	gcc -DVERIFY main.c -std=c99 -o verify
	./verify > verify.vals

# typing make foo.check will strip out the sum codes
%.check: 
	grep 'data ' trace | awk '{print $$9}' | cut -b4-9 > $@

include ../../mk/Makefile.tail_rules








