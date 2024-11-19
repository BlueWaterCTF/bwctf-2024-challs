#ifndef SANDBOX_H
#define SANDBOX_H

#define _GNU_SOURCE
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
#include <sys/socket.h>
#include <sys/types.h>
#include <ctype.h>

// ----- Constants ----
// Global variables for sandbox management
#define DEFAULT_UID (1000)
#define DEFAULT_GID (1000)
#define ROOT_UID (0)
#define ROOT_GID (0)

// Generic consts
#define nullptr (NULL)
#define STACK_SIZE (1024 * 1024)
#define STDIN (0)
#define STDOUT (1)

// Max sizes
#define MAX_STRING_SIZE (4096)
#define MAX_SANDBOXES (5)

// Command types
#define CMD_CREATE (1)
#define CMD_CONNECT (2)
#define CMD_COMMUNICATE (3)
// ----- </Constants> ----

// ---- Structures ----
typedef struct sandbox{
    pid_t pid;
    int stdin_fd;
    int stdout_fd;
} sandbox_t;

// Modify the sandbox_args_t structure
typedef struct sandbox_args {
    int fd;
    char *uid;
    char *gid;
} sandbox_args_t;

// Command structure
struct command {
    uint8_t type;
};
// ----- </Structures> -----

#endif
