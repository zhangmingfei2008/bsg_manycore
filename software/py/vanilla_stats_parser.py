#
#   vanilla_stats_parser.py
#
#   vanilla core stats extractor
# 
#   input: vanilla_stats.log
#   output: manycore_stats.log
#   output: tile_stats/tile_#_stats.log for all tiles 
#
#   @author Borna
#
#   How to use:
#   python3 generate_stats.py {manycore_dim_y} {manycore_dim_x} {total OR per_tile} {vanilla_stats.log}
#
#   ex) python3 generate_stats.py 4 4 per_tile vanilla_stats.log
#
#   {manycore_dim_y}  Mesh Y dimension of manycore
#   {manycore_dim_x}  Mesh X dimension of manycore



import sys
import os
import re
from enum import Enum
import csv

# These values are used by the manycore library in bsg_print_stat instructions
# They are added to the tag value to detremine wether the message is from the 
# start or the end of the kernel 
# the value of these paramters should match their counterpart inside 
# bsg_manycore/software/bsg_manycore_lib/bsg_manycore.h
bsg_PRINT_STAT_START_VAL = 0x00000000
bsg_PRINT_STAT_END_VAL   = 0xDEAD0000
bsg_TILE_GROUP_ORG_X = 0
bsg_TILE_GROUP_ORG_Y = 1


# formatting parameters for aligned printing
name_length = 25
type_length = 15
int_length = 15
float_length=15.4
percent_length=15.2

stats_timing_header_format = ("{:<"+str(name_length)+"}{:>"+str(type_length)+"}{:>"+str(type_length)+"}\n")
stats_timing_data_format   = ("{:<"+str(name_length)+"}{:>"+str(int_length)+"}{:>"+str(percent_length)+"f}\n") 
stats_instr_header_format  = ("{:<"+str(name_length)+"}{:>"+str(int_length)+"}{:>"+str(type_length)+"}\n")
stats_instr_data_format    = ("{:<"+str(name_length)+"}{:>"+str(int_length)+"}{:>"+str(percent_length)+"f}\n")
stats_stall_header_format  = ("{:<"+str(name_length)+"}{:>"+str(type_length)+"}{:>"+str(type_length)+"}\n")
stats_stall_data_format    = ("{:<"+str(name_length)+"}{:>"+str(int_length)+"}{:>"+str(percent_length)+"f}\n")
stats_miss_header_format   = ("{:<"+str(name_length)+"}{:>"+str(type_length)+"}{:>"+str(type_length)+"}{:>"+str(type_length)+"}\n")
stats_miss_data_format     = ("{:<"+str(name_length)+"}{:>"+str(int_length)+"}{:>"+str(int_length)+"}{:>"+str(float_length)+"f}\n")
separating_line = ('=' * 80 + '\n')



# List of instructions, operations and events parsed from vanilla_stats.log
stats_list = ["time", "x", "y", "tag", "global_ctr", "cycle"]

instr_list = ['instr','fadd','fsub','fmul','fsgnj','fsgnjn',
                     'fsgnjx','fmin','fmax','fcvt_s_w','fcvt_s_wu',
                     'fmv_w_x','feq','flt','fle','fcvt_w_s','fcvt_wu_s',
                     'fclass','fmv_x_w','local_ld','local_st',
                     'remote_ld','remote_st','local_flw','local_fsw',
                     'remote_flw','remote_fsw','lr','lr_aq',
                     'swap_aq','swap_rl','beq','bne','blt','bge','bltu',
                     'bgeu','jalr','jal', 'sll',
                     'slli','srl','srli','sra','srai','add','addi','sub',
                     'lui','auipc','xor','xori','or','ori','and','andi',
                     'slt','slti','sltu','sltiu','mul','mulh','mulhsu',
                     'mulhu','div','divu','rem','remu','fence']

miss_list =         ['icache_miss', 'beq_miss', 'bne_miss', 'blt_miss',
                     'bge_miss', 'bltu_miss', 'bgeu_miss', 'jalr_miss']

stalls_list =       ['stall_fp_remote_load','stall_fp_local_load',
                     'stall_depend','stall_depend_remote_load',
                     'stall_depend_local_load','stall_force_wb',
                     'stall_ifetch_wait','stall_icache_store',
                     'stall_lr_aq','stall_md','stall_remote_req','stall_local_flw']



class VanillaStatsParser:

  # default constructor
  def __init__(self, manycore_dim_y, manycore_dim_x, per_tile_stat):

    self.manycore_dim_y = manycore_dim_y
    self.manycore_dim_x = manycore_dim_x
    self.manycore_dim = manycore_dim_y * manycore_dim_x
    self.per_tile_stat = per_tile_stat

    self.manycore_stats_file = open("manycore_stats.log", "w")

    self.max_tile_groups = 1024
    self.num_tile_groups = 0
#    self.num_tile_groups = [[0] * self.manycore_dim_x] * self.manycore_dim_y

    self.timing_start_list = [0] * self.max_tile_groups 
    self.timing_end_list =   [0] * self.max_tile_groups
#    self.timing_start_list = [[[0] * self.max_tile_groups] * self.manycore_dim_x] * self.manycore_dim_y
#    self.timing_end_list =   [[[0] * self.max_tile_groups] * self.manycore_dim_x] * self.manycore_dim_y

    self.total_execution_time = 0
    self.total_instr_cnt = 0
    self.total_stall_cnt = 0
    self.total_miss_cnt = 0

    self.tile_stat_dict = [[dict() for x in range(self.manycore_dim_x)] for y in range(self.manycore_dim_y)]
    self.manycore_stat_dict = dict()


  def generate_stats_timing(self, trace):
    y = trace["y"]
    x = trace["x"]
    relative_y = y - bsg_TILE_GROUP_ORG_Y
    relative_x = x - bsg_TILE_GROUP_ORG_X
    tg_num = trace["tag"]
    # Only count those coming from the origin tile (0,0)
    if (relative_x == 0 and relative_y == 0):
      if(tg_num < bsg_PRINT_STAT_END_VAL):
        self.timing_start_list[tg_num] = trace["time"]
        self.num_tile_groups += 1
      else:
        self.timing_end_list[tg_num - bsg_PRINT_STAT_END_VAL] = trace["time"]


  # Sum up all other stats for all tiles based on the last bsg_print_stat instr
  def generate_stats_all(self):
      # Generate timing stats 
      for trace in self.traces:
        self.generate_stats_timing(trace)


      #other stats are only read once per tile from the end of file
      #i.e. if mesh dimensions are 4x4, only last 16 lines are needed 
      trace_idx = len(self.traces)
      for y in range(self.manycore_dim_y):
        for x in range(self.manycore_dim_x):
          trace_idx -= 1
          trace = self.traces[trace_idx]
          for stat in stats_list:
            self.tile_stat_dict[y][x][stat] = trace[stat]
          for instr in instr_list:
            self.tile_stat_dict[y][x][instr] = trace[instr]
          for stall in stalls_list:
            self.tile_stat_dict[y][x][stall] = trace[stall]
          for miss in miss_list:
            self.tile_stat_dict[y][x][miss] = trace[miss]


  # Print execution timing for the entire manycore 
  def print_manycore_stats_timing(self, stat_file):
    # For total execution time, we only sum up the execution time of origin tile in tile groups
    # The origin tile's relative coordinates is always 0,0 
    stat_file.write("Timing Stats\n")
    stat_file.write(stats_timing_header_format.format("tile group", "exec time", "share (%)"))
    stat_file.write("{}".format(separating_line))

    # Sum up execution time for all tile groups 
    for i in range (0, self.num_tile_groups):
      self.total_execution_time += (self.timing_end_list[i] - self.timing_start_list[i])

    for i in range (0, self.num_tile_groups):
      tg_time = self.timing_end_list[i] - self.timing_start_list[i]
      stat_file.write(stats_timing_data_format.format(i,
                                                      tg_time,
                                                      (tg_time / self.total_execution_time * 100)))

    stat_file.write(stats_timing_data_format.format("total",
                                                    self.total_execution_time,
                                                    (self.total_execution_time / self.total_execution_time * 100)))
    stat_file.write("{}\n".format(separating_line))
    return


  # Print instruction stats for the entire manycore
  def print_manycore_stats_instructions(self, stat_file):

    stat_file.write("Instruction Stats\n")
    stat_file.write(stats_instr_header_format.format("instruction", "count", " share (%)"))
    stat_file.write("{}".format(separating_line))

   
    # Print instruction stats for manycore
    for instr in instr_list:
       stat_file.write(stats_instr_data_format.format(instr,
                                                      self.manycore_stat_dict[instr],
                                                      (100 * self.manycore_stat_dict[instr] / self.total_instr_cnt)))

    stat_file.write(stats_instr_data_format.format("total",
                                                   self.total_instr_cnt, 
                                                   (100 * self.total_instr_cnt / self.total_instr_cnt)))
    stat_file.write("{}\n".format(separating_line))
    return


  # Print instruction stats for each tile in a separate file 
  # y,x are tile coordinates 
  def print_per_tile_stats_instructions(self, y, x, stat_file):

    stat_file.write("Instruction Stats\n")
    stat_file.write(stats_instr_header_format.format("instruction", "count", " share (%)"))
    stat_file.write("{}".format(separating_line))

    # Calculate total instruction count for tile 
    tile_total_instr_cnt = 0
    for instr in instr_list:
      if (instr != "instr"):
        tile_total_instr_cnt += self.tile_stat_dict[y][x][instr]
   
    # Print instruction stats for manycore
    for instr in instr_list:
       stat_file.write(stats_instr_data_format.format(instr,
                                                      self.tile_stat_dict[y][x][instr],
                                                      (100 * self.tile_stat_dict[y][x][instr] / tile_total_instr_cnt)))

    stat_file.write(stats_instr_data_format.format("total",
                                                   tile_total_instr_cnt, 
                                                   (100 * tile_total_instr_cnt / tile_total_instr_cnt)))
    stat_file.write("{}\n".format(separating_line))
    return




  # Print stall stats for the entire manycore
  def print_manycore_stats_stalls(self, stat_file):
    stat_file.write("Stall Stats\n")
    stat_file.write(stats_stall_header_format.format("stall", "cycles", "share (%)"))
    stat_file.write("{}".format(separating_line))

    # Print stall stats for manycore
    for stall in stalls_list:
       stat_file.write(stats_stall_data_format.format(stall,
                                                      self.manycore_stat_dict[stall],
                                                      (100 * self.manycore_stat_dict[stall] / self.total_stall_cnt)))

    stat_file.write(stats_stall_data_format.format("total",
                                                   self.total_stall_cnt,
                                                   (100 * self.total_stall_cnt / self.total_stall_cnt)))
    stat_file.write("{}\n".format(separating_line))
    return


  # Print stall stats for each tile in a separate file
  # y,x are tile coordinates 
  def print_per_tile_stats_stalls(self, y, x, stat_file):
    stat_file.write("Stall Stats\n")
    stat_file.write(stats_stall_header_format.format("stall", "cycles", "share (%)"))
    stat_file.write("{}".format(separating_line))

    # Calculate total stall count for tile
    tile_total_stall_cnt = 0
    for stall in stalls_list:
      tile_total_stall_cnt += self.tile_stat_dict[y][x][stall]

    # Print stall stats for manycore
    for stall in stalls_list:
       stat_file.write(stats_stall_data_format.format(stall,
                                                      self.tile_stat_dict[y][x][stall],
                                                      (100 * self.tile_stat_dict[y][x][stall] / tile_total_stall_cnt)))

    stat_file.write(stats_stall_data_format.format("total",
                                                   tile_total_stall_cnt,
                                                   (100 * tile_total_stall_cnt / tile_total_stall_cnt)))
    stat_file.write("{}\n".format(separating_line))
    return




  # Print miss stats for the entire manycore
  def print_manycore_stats_miss(self, stat_file):
    stat_file.write("Miss Stats\n")
    stat_file.write(stats_miss_header_format.format("unit", "miss", "total", "hit rate"))
    stat_file.write("{}".format(separating_line))

    for miss in miss_list:
       # Find total number of operations for that miss
       # If operation is icache, the total is total # of instruction
       # otherwise, search for the specific instruction
       if (miss == "icache_miss"):
         operation = "icache"
         operation_cnt = self.manycore_stat_dict["instr"]
       else:
         operation = miss.replace("_miss", '')
         operation_cnt = self.manycore_stat_dict[operation]
       miss_cnt = self.manycore_stat_dict[miss]
       hit_rate = 1 if operation_cnt == 0 else (1 - miss_cnt/operation_cnt)
         
       stat_file.write(stats_miss_data_format.format(operation, miss_cnt, operation_cnt, hit_rate ))
    stat_file.write("{}\n".format(separating_line))
    return


  # Print miss stats for each tile in a separate file
  # y,x are tile coordinates 
  def print_per_tile_stats_miss(self, y, x, stat_file):
    stat_file.write("Miss Stats\n")
    stat_file.write(stats_miss_header_format.format("unit", "miss", "total", "hit rate"))
    stat_file.write("{}".format(separating_line))

    for miss in miss_list:
       # Find total number of operations for that miss
       # If operation is icache, the total is total # of instruction
       # otherwise, search for the specific instruction
       if (miss == "icache_miss"):
         operation = "icache"
         operation_cnt = self.tile_stat_dict[y][x]["instr"]
       else:
         operation = miss.replace("_miss", '')
         operation_cnt = self.tile_stat_dict[y][x][operation]
       miss_cnt = self.tile_stat_dict[y][x][miss]
       hit_rate = 1 if operation_cnt == 0 else (1 - miss_cnt/operation_cnt)
         
       stat_file.write(stats_miss_data_format.format(operation, miss_cnt, operation_cnt, hit_rate ))
    stat_file.write("{}\n".format(separating_line))
    return





  # Sums up all stats from all tiles to generate manycore stats 
  def calculate_manycore_stats_all(self):

    # Initialize counts to zero
    for instr in instr_list:
      self.manycore_stat_dict[instr] = 0
    for stall in stalls_list:
      self.manycore_stat_dict[stall] = 0
    for miss in miss_list:
      self.manycore_stat_dict[miss] = 0

    for y in range(self.manycore_dim_y):
      for x in range(self.manycore_dim_x):

        # Calculate total instruction count for each tile and for manycore
        for instr in instr_list: 
          self.manycore_stat_dict[instr] += self.tile_stat_dict[y][x][instr]
          if (instr != "instr"):
            self.total_instr_cnt += self.tile_stat_dict[y][x][instr]

        # Calculate total stall count for each tile and for manycore
        for stall in stalls_list: 
          self.manycore_stat_dict[stall] += self.tile_stat_dict[y][x][stall]
          self.total_stall_cnt += self.tile_stat_dict[y][x][stall]

        # Calculate total miss count for each tile and for manycore
        for miss in miss_list: 
          self.manycore_stat_dict[miss] += self.tile_stat_dict[y][x][miss]
          self.total_miss_cnt += self.tile_stat_dict[y][x][miss]
    return 
 


  def print_manycore_stats_all(self):
    self.calculate_manycore_stats_all()
    self.print_manycore_stats_timing(self.manycore_stats_file)
    self.print_manycore_stats_miss(self.manycore_stats_file)
    self.print_manycore_stats_stalls(self.manycore_stats_file)
    self.print_manycore_stats_instructions(self.manycore_stats_file)

  def print_per_tile_stats_all(self):
    stats_path = os.getcwd() + "/tile_stats/"
    if not os.path.exists(stats_path):
      os.mkdir(stats_path)
    for y in range(self.manycore_dim_y):
      for x in range(self.manycore_dim_x):
        stat_file = open( (stats_path + "tile_" + str(y) + "_" + str(x) + "_stats.log"), "w")
#        self.print_per_tile_stats_timing(y, x, stat_file)
        self.print_per_tile_stats_miss(y, x, stat_file)
        self.print_per_tile_stats_stalls(y, x, stat_file)
        self.print_per_tile_stats_instructions(y, x, stat_file)



  # default stats generator
  def generate_stats(self, input_file):
    self.traces = []
    with open(input_file) as f:
      csv_reader = csv.DictReader (f, delimiter=",")
      for row in csv_reader:
        trace = {}
        for stat in stats_list:
          trace[stat] = int(row[stat])
        for instr in instr_list:
          trace[instr] = int(row[instr])
        for stall in stalls_list:
          trace[stall] = int(row[stall])
        for miss in miss_list:
          trace[miss] = int(row[miss])
        self.traces.append(trace)

    # generate all other stats
    self.generate_stats_all()

    # print all manycore stats 
    self.print_manycore_stats_all()

    # If requested, print all per tile stats
    if(per_tile_stat):
      self.print_per_tile_stats_all()

    # cleanup
    self.manycore_stats_file.close()


# main()
if __name__ == "__main__":

  if len(sys.argv) != 5:
    print("Error: wrong number of arguments.")
    print("python3 vanilla_stats_parser.py {manycore_dim_x} {manycore_dim_y} {total/per_tile} {vanilla_stats.log} ")
    sys.exit()
 
  manycore_dim_y = int(sys.argv[1])
  manycore_dim_x = int(sys.argv[2])

  stat_type = sys.argv[3]
  if stat_type == "total":
    per_tile_stat = False
  elif stat_type == "per_tile":
    per_tile_stat = True
  else:
    print("Error: invalid stat type " + stat_type + ". Can be total or per_tile.")
    print("python3 vanilla_stats_parser.py {manycore_dim_x} {manycore_dim_y} {vanilla_stats.log} {total/per_tile}")
    sys.exit()

  input_file = sys.argv[4]


  st = VanillaStatsParser(manycore_dim_y, manycore_dim_x, per_tile_stat)
  st.generate_stats(input_file)
