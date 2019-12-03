#
#   blood_graph.py
#
#   vanilla_core execution visualizer.
# 
#   input: vanilla_operation_trace.csv.log
#   output: bitmap file (blood.bmp)
#
#   @author tommy and borna
#
#   How to use:
#   python blood_graph.py --cycle {start_cycle@end_cycle}  
#                         --abstract {optional} --input {vanilla_operation_trace.csv.log}
#
#   ex) python blood_graph.py --cycle 6000000@15000000  
#                             --abstract --input vanilla_operation_trace.csv.log
#
#   {cycle}       start_cycle@end_cycle of execution
#   {abstract}    used for abstract simplifed bloodgraph


import sys
import csv
import argparse
from itertools import chain
from collections import Counter


class PCHistogram:
    _DEFAULT_START_CYCLE = 0 
    _DEFAULT_END_CYCLE   = 500000

    # default constructor
    def __init__(self, input_file):

        self.traces = []
        self.pc_cnt = Counter()
        self.max_pc_val = 0
        self.min_pc_val = 0

       # parse vanilla_operation_trace.log
        with open(input_file) as f:
            csv_reader = csv.DictReader(f, delimiter=",")
            for row in csv_reader:
                trace = {}
                trace["x"] = int(row["x"])  
                trace["y"] = int(row["y"])  
                trace["operation"] = row["operation"]
                trace["cycle"] = int(row["cycle"])
                trace["pc"] = int(row["pc"], 16)

                # update min and max pc read from traces 
                self.max_pc_val = max(self.max_pc_val, trace["pc"])
                self.min_pc_val = min(self.min_pc_val, trace["pc"])

                self.traces.append(trace)

        self.pc_cnt = self.__generate_pc_cnt(self.traces)

        self.__print_pc_histogram(self.pc_cnt)
        return 


    # Go through input file traces and count 
    # how many times each pc has been executed
    def __generate_pc_cnt(self, traces):
        pc_cnt = Counter()
        for trace in traces:
            pc_cnt[trace["pc"]] += 1
        return pc_cnt



    # Traverse the pc counter in order, and 
    # print number of executions for every range
    def __print_pc_histogram(self, pc_cnt):
        pc_file = open("pc_histogram.log", "w")
        pc_start = self.min_pc_val 
        pc_end   = self.min_pc_val

        while (pc_start <= self.max_pc_val and pc_end <= self.max_pc_val):
            if (pc_cnt[pc_start] == pc_cnt[pc_end]):
                 pc_end += 1
            else:
                 if (pc_cnt[pc_start] > 0):
                     pc_file.write("[{:>08x} - {:>08x}]: {:>16}\n".format((pc_start << 2),
                                                                          ((pc_end-1) << 2),
                                                                          pc_cnt[pc_start]))
                 pc_start = pc_end

        if(pc_start < self.max_pc_val-1):
            if (pc_cnt[pc_start] > 0):
                 pc_file.write("[{:>08x} - {:>08x}]: {:>16}\n".format((pc_start << 2),
                                                                      ((pc_end-1) << 2),
                                                                      pc_cnt[pc_start]))

        pc_file.close()
        return


# Parse input arguments and options 
def parse_args():  
    parser = argparse.ArgumentParser(description="Argument parser for blood_graph.py")
    parser.add_argument("--input", default="vanilla_operation_trace.csv.log", type=str,
                        help="Vanilla operation log file")
    args = parser.parse_args()
    return args


# main()
if __name__ == "__main__":
    args = parse_args()
    pch = PCHistogram(args.input)

