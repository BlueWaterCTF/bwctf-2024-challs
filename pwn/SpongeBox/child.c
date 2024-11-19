#define _GNU_SOURCE         
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

int main(void) {
   
    // Use pipe() calls to set up communication with the sandboxer.
    // ...
    
    // Do whatever :) 
    sleep(100);
    return 0;
}
