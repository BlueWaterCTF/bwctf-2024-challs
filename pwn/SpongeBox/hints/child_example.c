#define _GNU_SOURCE         
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

#define OUR_STDIN (100)
#define OUR_STDOUT (101)
#define STDIN (0)
#define STDOUT (1)

int main(void) {
    int pipe1[2] = {0};  // pipe1: [0] we read, [1] they write
    int pipe2[2] = {0};  // pipe2: [0] they read, [1] we write

    // Set up pipes
    if (pipe(pipe1) == -1) {
        perror("pipe1");
        exit(1);
    }

    if (pipe(pipe2) == -1) {
        perror("pipe2");
        exit(1);
    }   

    // FDs for sandbox communicaton
    dup2(pipe1[1], STDIN);
    dup2(pipe2[0], STDOUT);
    
    // FDs for our communication (read from OUR_STDIN, write to OUR_STDOUT)
    dup2(pipe1[0], OUR_STDIN);
    dup2(pipe2[1], OUR_STDOUT);

    // Do whatever :) 
    sleep(100);
    return 0;
}