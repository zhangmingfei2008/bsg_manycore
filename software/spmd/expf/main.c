#include <math.h>
#include <stdio.h>

typedef union {
  int i;
  float f;
} float_or_int_t;

float data = 3.4;
int expected = 0x41efb67c; // expf(data)

int main() {
  float_or_int_t result;

  result.f = expf(data);
  printf("result=%x expected=%x\n", result.i, expected);  
  if (result.i != expected) 
    return -1;

  return 0;
}
