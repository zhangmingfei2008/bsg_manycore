/**
 *    vcache_profiler.v
 *    
 */


module vcache_profiler
  import bsg_cache_pkg::*;
  #(parameter data_width_p="inv"
    ,parameter addr_width_p="inv"
    ,parameter bsg_cache_pkt_width_lp=`bsg_cache_pkt_width(addr_width_p,data_width_p) 
  )
  (
    input clk_i
    , input reset_i

    // For request stats incoming to tl stage
    // As it takes one cycle from the time ready_o goes hight,
    // to load the incoming cache packet into tl registers,
    // We directly look at incoming cache_pkt into the cache
    , input v_i
    , input ready_o
    , input [addr_width_p-1:0] addr_tl_r
    , input [data_width_p-1:0] data_tl_r
    , input bsg_cache_pkt_decode_s decode_tl_r
    , input [bsg_cache_pkt_width_lp-1:0] cache_pkt_i
    , input bsg_cache_pkt_decode_s decode


    // For responses going out of verify stage
    , input v_o
    , input yumi_i
    , input v_v_r
    , input miss_v
    , input [addr_width_p-1:0] addr_v_r
    , input [data_width_p-1:0] data_v_r
    , input bsg_cache_pkt_decode_s decode_v_r


    , input [31:0] global_ctr_i
    , input print_stat_v_i
    , input [data_width_p-1:0] print_stat_tag_i

    , input trace_en_i // from top-level testbench
  );



  // For purpose of looking into the packed cache packet
  //
  `declare_bsg_cache_pkt_s(addr_width_p,data_width_p);
  bsg_cache_pkt_s cache_pkt;
  assign cache_pkt = cache_pkt_i;



  // event signals
  //

  logic miss;
  logic miss_ld;
  logic miss_st;

  logic inc_ld;
  logic inc_st;
  logic inc_ld_miss;
  logic inc_st_miss;


  // miss handler signals
  // when miss is high, miss handler is active and output is not ready
  // other signals (miss_ld/st) refer to the type of request
  assign miss = v_v_r & miss_v & ~(v_o | yumi_i); 
  assign miss_ld = v_v_r & miss_v & ~(v_o | yumi_i) & decode_v_r.ld_op;
  assign miss_st = v_v_r & miss_v & ~(v_o | yumi_i) & decode_v_r.st_op;

  // Load/store output is ready 
  // when inc_ld/st is high it means a hit load/store is ready
  // when inc_ld/st_miss is high it means a missed load/store is ready
  assign inc_ld = v_o & yumi_i & decode_v_r.ld_op;
  assign inc_st = v_o & yumi_i & decode_v_r.st_op;
  assign inc_ld_miss = v_o & yumi_i & decode_v_r.ld_op & miss_v;
  assign inc_st_miss = v_o & yumi_i & decode_v_r.st_op & miss_v;


  // stats counting
  // outgoing response
  integer ld_count_r;
  integer st_count_r;
  integer ld_miss_count_r;
  integer st_miss_count_r;


  always_ff @ (negedge clk_i) begin

    if (reset_i) begin
      ld_count_r <= '0;
      st_count_r <= '0;
      ld_miss_count_r <= '0;
      st_miss_count_r <= '0;
    end
    else begin
      if (inc_ld) ld_count_r <= ld_count_r + 1;
      if (inc_st) st_count_r <= st_count_r + 1;
      if (inc_ld_miss) ld_miss_count_r <= ld_miss_count_r + 1;
      if (inc_st_miss) st_miss_count_r <= st_miss_count_r + 1;
    end

  end


  // file logging
  //
  localparam logfile_lp = "vcache_stats.log";
  localparam tracefile_lp = "vcache_operation_trace.log";

  string my_name;
  integer fd, fd2;

  initial begin

    my_name = $sformatf("%m");
    if (str_match(my_name, "vcache[0]")) begin
      fd = $fopen(logfile_lp, "w");
      $fwrite(fd, "instance,global_ctr,tag,ld,st,ld_miss,st_miss\n");
      $fclose(fd);
    end

    // TODO: borna fix
    //if (trace_en_i) begin
      fd2 = $fopen(tracefile_lp, "w");
      $fwrite(fd2, "timestamp,x,y,addr,data,operation\n");
      $fclose(fd2);
    //end


    // TODO: borna fix the my_name[34] issue (x,y) coordinates

    forever begin
      @(negedge clk_i) begin
	if (~reset_i & trace_en_i) begin
          fd2 = $fopen(tracefile_lp, "a");

          if(v_v_r) begin
            if(inc_ld) begin
              $fwrite(fd2, "%0d,%s,%0d,%0d,0x%0h,%s\n", $time, my_name[34], 0, addr_v_r, data_v_r, "ld");
            end
            if (inc_st) begin
              $fwrite(fd2, "%0d,%s,%0d,%0d,0x%0h,%s\n", $time, my_name[34], 0, addr_v_r, data_v_r, "st");
            end

            if(miss) begin
              if(miss_ld)
                $fwrite(fd2, "%0d,%s,%0d,%0d,0x%0h,%s\n", $time, my_name[34], 0, addr_v_r, data_v_r, "miss_ld");
              else if(miss_st)
                $fwrite(fd2, "%0d,%s,%0d,%0d,0x%0h,%s\n", $time, my_name[34], 0, addr_v_r, data_v_r, "miss_st");
              else
                $fwrite(fd2, "%0d,%s,%0d,%0d,0x%0h,%s\n", $time, my_name[34], 0, addr_v_r, data_v_r, "miss_unk");
            end
          end
          else
            $fwrite(fd2, "%0d,%s,%0d,%0d,0x%0h,%s\n", $time, my_name[34], 0, addr_v_r, data_v_r, "idle");

          $fclose(fd2);
        end


        if (~reset_i & print_stat_v_i) begin

          $display("[BSG_INFO][VCACHE_PROFILER] %s t=%0t printing stats.", my_name, $time);

          fd = $fopen(logfile_lp, "a");
          $fwrite(fd, "%s,%0d,%0d,%0d,%0d,%0d,%0d\n",
            my_name, global_ctr_i, print_stat_tag_i, ld_count_r, st_count_r, ld_miss_count_r, st_miss_count_r);   
          $fclose(fd);
        end
      end
    end
  end


  // string match helper
  //
  function str_match(string s1, s2);

    int len1, len2;
    len1 = s1.len();
    len2 = s2.len();

    if (len2 > len1)
      return 0;

    for (int i = 0; i < len1-len2+1; i++)
      if (s1.substr(i,i+len2-1) == s2)
        return 1;
  
  endfunction

endmodule
