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
//    , input [addr_width_p-1:0] addr_tl_r
//    , input [data_width_p-1:0] data_tl_r
//    , input bsg_cache_pkt_decode_s decode_tl_r
    , input [bsg_cache_pkt_width_lp-1:0] cache_pkt_i
    , input bsg_cache_pkt_decode_s decode


    // For responses going out of verify stage
    , input v_o
    , input yumi_i
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
  logic inc_req;
  logic inc_req_ld;
  logic inc_req_st;

  logic inc_ld;
  logic inc_st;
  logic inc_ld_miss;
  logic inc_st_miss;


  assign inc_req = ready_o & v_i;
  assign inc_req_ld = ready_o & v_i & decode.ld_op;
  assign inc_req_st = ready_o & v_i & decode.st_op;

  assign inc_ld = v_o & yumi_i & decode_v_r.ld_op;
  assign inc_st = v_o & yumi_i & decode_v_r.st_op;
  assign inc_ld_miss = v_o & yumi_i & decode_v_r.ld_op & miss_v;
  assign inc_st_miss = v_o & yumi_i & decode_v_r.st_op & miss_v;


  // stats counting
  //
  integer req_count_r;
  integer req_ld_count_r;
  integer req_st_count_r;

  // outgoing response
  integer ld_count_r;
  integer st_count_r;
  integer ld_miss_count_r;
  integer st_miss_count_r;


  always_ff @ (negedge clk_i) begin

    if (reset_i) begin
      req_count_r <= '0;
      req_ld_count_r <= '0;
      req_st_count_r <= '0;

      ld_count_r <= '0;
      st_count_r <= '0;
      ld_miss_count_r <= '0;
      st_miss_count_r <= '0;
    end
    else begin
      if (inc_req) req_count_r <= req_count_r + 1;
      if (inc_req_ld) req_ld_count_r <= req_ld_count_r +1;
      if (inc_req_st) req_st_count_r <= req_st_count_r +1;

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
      $fwrite(fd2, "time,x,addr,data,operation\n");
      $fclose(fd2);
    //end


    forever begin
      @(negedge clk_i) begin
	if (~reset_i & trace_en_i) begin
          fd2 = $fopen(tracefile_lp, "a");


          if (miss_v)
                $fwrite(fd2, "%0d,%s,%s\n", $time, my_name, "miss");


          if (inc_req) begin
              if (inc_req_ld)
                $fwrite(fd2, "%0d,%s,%0d,0x%0h,%s\n", $time, my_name, cache_pkt.addr, cache_pkt.data, "req_ld");
              else if (inc_req_st)
                $fwrite(fd2, "%0d,%s,%0d,0x%0h,%s\n", $time, my_name, cache_pkt.addr, cache_pkt.data, "req_st");
              else
                $fwrite(fd2, "%0d,%s,%0d,0x%0h,%s\n", $time, my_name, cache_pkt.data, cache_pkt.data, "req_unk");
          end



          if(inc_ld) begin
            if(inc_ld_miss) 
              $fwrite(fd2, "%0d,%s,%0d,%0d,%s\n", $time, my_name, addr_v_r, data_v_r, "ld_miss");
            else
               $fwrite(fd2, "%0d,%s,%0d,%0d,%s\n", $time, my_name, addr_v_r, data_v_r, "ld");
          end

          if (inc_st) begin
            if (inc_st_miss)
              $fwrite(fd2, "%0d,%s,%0d,%0d,%s\n", $time, my_name, addr_v_r, data_v_r, "st_miss");
            else 
              $fwrite(fd2, "%0d,%s,%0d,%0d,%s\n", $time, my_name, addr_v_r, data_v_r, "st");
          end

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
