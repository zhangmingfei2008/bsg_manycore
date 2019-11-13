//====================================================================
// bsg_dram_load_store.c
// 11/05/2019, borna
//====================================================================
// this program will perform load stores to various dram banks 
// to verify the correctness of vcache profiler
//

#include "bsg_manycore.h"
#include "bsg_set_tile_x_y.h"

#define CACHE_NUM_SET 256
#define CACHE_NUM_WAY 2

#define BSG_TILE_GROUP_X_DIM bsg_tiles_X
#define BSG_TILE_GROUP_Y_DIM bsg_tiles_Y
#include "bsg_tile_group_barrier.h"
INIT_TILE_GROUP_BARRIER(r_barrier, c_barrier, 0, bsg_tiles_X-1, 0, bsg_tiles_Y-1);


int main()
{
	bsg_set_tile_x_y();
	int id = bsg_x_y_to_id(bsg_x, bsg_y);

	if (id == 0)
	{
		int val, val2;

		// ld + st
//		bsg_dram_store(0, 0xdead);
//		bsg_dram_load(512, val);

		// ld + ld
//		bsg_dram_load(0, val);
//		bsg_dram_load(4, val2);


		// ld_miss + ld_miss to different addresses
//		bsg_dram_load(2048, val);
//		bsg_dram_load(2052, val2);
//		bsg_dram_load(3072, val2);


	


		// ld_miss + ld_miss to same block
//		bsg_dram_load(2048, val);
//		bsg_dram_load(2052, val2);


		// ld_miss + ld
//		bsg_dram_load(2048, val);
//		bsg_dram_load(0, val2);


		// batch load
		for (int i = 0; i < 1024; i += 4) {
			bsg_dram_load(1024 + i, val);
		}

		// batch store
		for (int i = 0; i < 1024; i += 4) {
			bsg_dram_store(1024 + i, 0xdea0 + i);
		}


	}
	
	bsg_tile_group_barrier(&r_barrier, &c_barrier);	

	bsg_finish_x(IO_X_INDEX);
}
