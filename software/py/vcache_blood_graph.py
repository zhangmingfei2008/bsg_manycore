#
#   vcache_blood_graph.py
#
#   victim cache operation visualizer.
# 
#   input: vcache_operation_trace.log
#   output: bitmap file (vcache_blood.bmp)
#
#   @author borna
#
#   How to use:
#   python vcache_blood_graph.py --time {start_time@end_time} --timestamp{timestep} 
      #                          --abstract {optional} --input {vcache_operation_trace.log}
#
#   ex) python vcache_blood_graph.py --time 6000000@15000000 --timestamp 20 
#                                    --abstract --input vcache_operation_trace.log
#
#   {time}        start_time@end_time in picosecond
#   {timestep}    Distance between two consecutive traces (clock period) in picoseconds
#   {abstract}    used for abstract simplifed bloodgraph
# 


import sys
import csv
import argparse
from PIL import Image, ImageDraw, ImageFont
from itertools import chain


DEFAULT_START_TIME = 18000000000
DEFAULT_END_TIME   = 20000000000
DEFAULT_TIMESTAMP  = 8000
DEFAULT_MODE       = "detailed"
DEFAULT_INPUT_FILE = "vcache_operation_trace.log"


class VcacheBloodGraph:
  # for generating the key
  KEY_WIDTH  = 256
  KEY_HEIGHT = 256
  # default constructor
  def __init__(self, start_time, end_time, timestep, abstract):

    self.start_time = start_time
    self.end_time = end_time
    self.timestep = timestep
    self.abstract = abstract

    # List of types of vcache operations
    self.operation_list = {"ld",
                           "st",
                           "miss_ld",
                           "miss_st",
                           "miss_unk",
                           "idle"}

    # Coloring scheme for different types of operations
    # For detailed mode 
    self.detailed_operation_color = {    "miss_ld"          : (0xff, 0x00, 0x00), ## red
                                         "miss_st"          : (0x00, 0x00, 0xff), ## blue
                                         "miss_unk"         : (0xff, 0xff, 0x00), ## yellow
                                         "ld"               : (0xff, 0xff, 0xff), ## white
                                         "st"               : (0x00, 0xff, 0x00), ## green
                                         "idle"             : (0x40, 0x40, 0x40), ## gray
                                    }

    # Coloring scheme for different types of operations
    # For abstract mode 
    self.astract_operation_color =  {    "miss_ld"          : (0xff, 0x00, 0x00), ## red
                                         "miss_st"          : (0x00, 0x00, 0xff), ## blue
                                         "miss_unk"         : (0xff, 0xff, 0x00), ## yellow
                                         "ld"               : (0xff, 0xff, 0xff), ## white
                                         "st"               : (0x00, 0xff, 0x00), ## green
                                         "idle"             : (0x40, 0x40, 0x40), ## gray
                                    }


    # Determine coloring rules based on mode {abstract / detailed}
    if (self.abstract):
      self.operation_color     = self.abstract_operation_color
    else:
      self.operation_color     = self.detailed_operation_color
    return

  
  # main public method
  def generate(self, input_file):
    # parse vcache_operation_trace.log
    traces = []
    with open(input_file) as f:
      csv_reader = csv.DictReader(f, delimiter=",")
      for row in csv_reader:
        trace = {}
        trace["x"] = int(row["x"])  
        trace["y"] = int(row["y"])  
        trace["operation"] = row["operation"]
        trace["addr"] = row["operation"]
        trace["data"] = row["operation"]
        trace["timestamp"] = int(row["timestamp"])
        traces.append(trace)
  
    # get tile-group dim
    self.__get_tg_dim(traces)

    # init image
    self.__init_image()

    # create image
    for trace in traces:
      self.__mark_trace(trace)

    #self.img.show()
    self.img.save("vcache_blood.bmp")
    return

  # public method to generate key for bloodgraph
  # called if --generate-key argument is true
  def generate_key(self, key_image_fname = "vcache_key"):
    img  = Image.new("RGB", (self.KEY_WIDTH, self.KEY_HEIGHT), "black")
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default()
    # the current row position of our key
    yt = 0
    # for each color in stalls...
    for (operation,color) in chain(self.stall_bubble_color.iteritems(),
                             [("unified_instr"    ,self.unified_instr_color),
                              ("unified_fp_instr" ,self.unified_fp_instr_color),
                              ("unknown"          ,self.unknown_color)]):
        # get the font size
        (font_height,font_width) = font.getsize(operation)
        # draw a rectangle with color fill
        yb = yt + font_width
        # [0, yt, 64, yb] is [top left x, top left y, bottom right x, bottom left y]
        draw.rectangle([0, yt, 64, yb], color)
        # write the label for this color in white
        # (68, yt) = (top left x, top left y)
        # (255, 255, 255) = white
        draw.text((68, yt), operation, (255,255,255))
        # create the new row's y-coord
        yt += font_width

    # save the key
    img.save("{}.bmp".format(key_image_fname))
    return

  # look through the input file to get the tile group dimension (x,y)
  def __get_tg_dim(self, traces):
    xs = list(map(lambda t: t["x"], traces))
    ys = list(map(lambda t: t["y"], traces))
    self.xmin = min(xs)
    self.xmax = max(xs)
    self.ymin = min(ys)
    self.ymax = max(ys)
    
    self.xdim = self.xmax-self.xmin+1
    self.ydim = self.ymax-self.ymin+1
    return


  # initialize image
  def __init_image(self):
    self.img_width = 1024   # default
    self.img_height = ((((self.end_time-self.start_time)//self.timestep)+self.img_width)//self.img_width)*(2+(self.xdim*self.ydim))
    self.img = Image.new("RGB", (self.img_width, self.img_height), "black")
    self.pixel = self.img.load()
    return  
  
  # mark the trace on output image
  def __mark_trace(self, trace):

    # ignore trace outside the time range
    if trace["timestamp"] < self.start_time or trace["timestamp"] >= self.end_time:
      return

    # determine pixel location
    cycle = (trace["timestamp"]-self.start_time)//self.timestep
    col = cycle % self.img_width
    floor = cycle // self.img_width
    tg_x = trace["x"] - self.xmin 
    tg_y = trace["y"] - self.ymin
    row = floor*(2+(self.xdim*self.ydim)) + (tg_x+(tg_y*self.xdim))

    # determine color
    if trace["operation"] in self.operation_color.keys():
      self.pixel[col,row] = self.operation_color[trace["operation"]]
    else:
      print ("Error: invalid operaiton in operation log: " + trace["operation"])
      sys.exit()
    return


# The action to take in two input arguments for start and 
# end time of execution in the form of start_time@end_time
class TimeAction(argparse.Action):
  def __call__(self, parser, namespace, time, option_string=None):
    start_str,end_str = time.split("@")

    # Check if start time is given as input
    if(not start_str):
      start_time = DEFAULT_START_TIME
    else:
      start_time = int(start_str)

    # Check if end time is given as input
    if(not end_str):
      end_time = DEFAULT_END_TIME
    else:
      end_time = int(end_str)

    # check if start time is before end time
    if(start_time > end_time):
      raise ValueError("start time {} cannot be larger than end time {}.".format(start_time, end_time))

    setattr(namespace, "start", start_time)
    setattr(namespace, "end", end_time)
 
# Parse input arguments and options 
def parse_args():  
  parser = argparse.ArgumentParser(description="Argument parser for blood_graph.py")
  parser.add_argument("--input", default=DEFAULT_INPUT_FILE, type=str,
                      help="Vanilla operation log file")
  parser.add_argument("--time", nargs='?', required=1, action=TimeAction, 
                      const = (str(DEFAULT_START_TIME)+"@"+str(DEFAULT_END_TIME)),
                      help="Time window of bloodgraph as start_time@end_time in picoseconds")
  parser.add_argument("--abstract", default=False, action='store_true',
                      help="Type of bloodgraph - abstract / detailed")
  parser.add_argument("--timestamp", default=DEFAULT_TIMESTAMP, type=int,
                      help="Distance between each trace (clock period) in picoseconds")
  parser.add_argument("--generate-key", default=False, action='store_true',
                      help="Generate a key image")
  parser.add_argument("--no-blood-graph", default=False, action='store_true',
                      help="Skip blood graph generation")

  args = parser.parse_args()
  return args


# main()
if __name__ == "__main__":
  args = parse_args()
  
  bg = VcacheBloodGraph(args.start, args.end, args.timestamp, args.abstract)
  if not args.no_blood_graph:
    bg.generate(args.input)
  if args.generate_key:
    bg.generate_key()

