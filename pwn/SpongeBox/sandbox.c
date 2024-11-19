#include "sandbox.h"

sandbox_t sandboxes[MAX_SANDBOXES];
size_t sandbox_count = 0;
int sync_socket[2];

void FAIL(const char* msg) {
  printf("ERROR MSG : %s | ERRNO: %s\n", msg, strerror(errno));
  exit(-1);
}

void CHECK(bool cond, const char* msg) {
  if (!cond) {
    FAIL(msg);
  }
}

void PCHECK(bool cond, const char* msg) {
  CHECK(cond, msg);
}

void send_error(int socket, const char* msg) {
    write(socket, msg, strlen(msg) + 1);
    write(socket, "\n", 1);
}

void deny_setgroups(pid_t pid) {
    char path[256] = {0};
    int fd = -1;

    snprintf(path, sizeof(path), "/proc/%d/setgroups", pid);

    fd = open(path, O_WRONLY);
    PCHECK(fd != -1, "Couldn't open setgroups");
    
    PCHECK(dprintf(fd, "deny") >= 0, "Could not write to setgroups");
    close(fd);
}

bool is_valid_number(const char *str) {
    // If the string is empty, it's not a valid number
    if (*str == '\0') return false;

    // Iterate through the string and check if all characters are digits
    while (*str) {
        if (!isdigit(*str)) return false; // If any character is not a digit, return false
        str++;
    }
    return true;  // If we made it through the whole string, it's a valid number
}

void become_user_group(uid_t uid, gid_t gid) {
    // Switch to the newly mapped user and group
    setresgid(gid, gid, gid);
    setresuid(uid, uid, uid);
}

void setup_idmaps(pid_t pid, char *uid, char *gid) {
    int uid_map_fd = -1, gid_map_fd = -1; 
    char *uid_map = NULL, *gid_map = NULL;
    char *uid_map_path = NULL, *gid_map_path = NULL;

    // Open the uid_map file
    asprintf(&uid_map_path, "/proc/%d/uid_map", pid);
    uid_map_fd = open(uid_map_path, O_WRONLY);

    // Write the mapping
    asprintf(&uid_map, "%s %d 1", uid, DEFAULT_UID);
    write(uid_map_fd, uid_map, strlen(uid_map) + 1);

    // Open the gid_map file
    asprintf(&gid_map_path, "/proc/%d/gid_map", pid);
    gid_map_fd = open(gid_map_path, O_WRONLY);
    
    // Write the mapping
    asprintf(&gid_map, "%s %d 1", gid, DEFAULT_GID);
    write(gid_map_fd, gid_map, strlen(gid_map) + 1);
}

static int setup_sandbox(char *uid, char *gid) {
    char sync_char = '\x00';
    uid_t uid_num  = 0;
    gid_t gid_num = 0;

    // Wait for parent to set up UID/GID mappings and setgroup configuration
    if (read(sync_socket[1], &sync_char, 1) != 1) {
        FAIL("Failed to read from sync socket");
    }

    uid_num = atoi(uid);
    gid_num = atoi(gid);

    // Set the newly mapped user and group ids
    become_user_group(uid_num, gid_num);
    return 0;
}

void run_sandbox(sandbox_args_t *args) {
    // Close the parent's end of the sync socket
    close(sync_socket[0]);

    PCHECK(setup_sandbox(args->uid, args->gid) == 0, "setup_sandbox failed");
    // Close the child's end of the sync socket
    close(sync_socket[1]);

    execveat(args->fd, "", NULL, NULL, AT_EMPTY_PATH);
    PCHECK(false, "execveat failed");
}

void drop_privileges(void) {
    if (setegid(DEFAULT_GID) != 0) {
        perror("setegid failed in drop_privileges");
        exit(-1);
    }

    if (seteuid(DEFAULT_UID) != 0) {
        perror("seteuid failed in drop_privileges");
        exit(-1);
    }
}

void gain_privileges(void) {
    if (setegid(ROOT_GID) != 0) {
        perror("setegid failed in gain_privileges");
        exit(-1);
    }

    if (seteuid(ROOT_UID) != 0) {
        perror("seteuid failed in gain_privileges");
        exit(-1);
    }
}

int create_sandbox(sandbox_args_t *args) {
    char *stack;
    char *stackTop;
    pid_t child_pid;

    // Allocate stack for child
    stack = mmap(NULL, STACK_SIZE, PROT_READ | PROT_WRITE,
                 MAP_PRIVATE | MAP_ANONYMOUS | MAP_STACK, -1, 0);
    if (stack == MAP_FAILED) {
        perror("mmap");
        return -1;
    }
    
    stackTop = stack + STACK_SIZE;  // Assume stack grows downward

    // Create a socketpair for synchronization
    if (socketpair(AF_UNIX, SOCK_STREAM, 0, sync_socket) == -1) {
        perror("socketpair");
        munmap(stack, STACK_SIZE);
        return -1;
    }

    // Drop privileges before creating the sandboxee
    drop_privileges();

    child_pid = clone(run_sandbox, stackTop, 
                      CLONE_NEWPID | CLONE_NEWNET | CLONE_NEWUTS | CLONE_NEWCGROUP | CLONE_NEWIPC | CLONE_NEWNS | CLONE_NEWUSER | SIGCHLD, 
                      args);

    // Gain capabilities to continue the sandboxer
    gain_privileges();

    if (child_pid == -1) {
        perror("clone");
        munmap(stack, STACK_SIZE);
        close(sync_socket[0]);
        close(sync_socket[1]);
        return -1;
    }

    // Parent process: set up UID/GID mappings for the child
    deny_setgroups(child_pid);
    setup_idmaps(child_pid, args->uid, args->gid);

    // Signal the child that UID/GID mappings are set up
    if (write(sync_socket[0], "x", 1) != 1) {
        perror("Failed to write to sync socket");
    }

    // Close the parent's end of the sync socket
    close(sync_socket[0]);

    return child_pid;
}

int connect_sandbox(sandbox_t *sandbox) {
    int pidfd = -1;
    int stdin_fd = -1;
    int stdout_fd = -1;

    // Open a file descriptor to the sandbox process
    pidfd = syscall(SYS_pidfd_open, sandbox->pid, 0);
    if (pidfd == -1) {
        printf("pidfd_open failed\n");
        goto cleanup;
    }

    // Get file descriptor (stdin) from the sandbox process
    stdin_fd = syscall(SYS_pidfd_getfd, pidfd, STDIN, 0);
    if (stdin_fd == -1) {
        printf("pidfd_getfd failed for stdin with err %s\n", strerror(errno));
        goto cleanup;
    }

    // Get file descriptor 1 (stdout) from the sandbox process
    stdout_fd = syscall(SYS_pidfd_getfd, pidfd, STDOUT, 0);
    if (stdout_fd == -1) {
        printf("pidfd_getfd failed for stdout with err %s\n", strerror(errno));
        goto cleanup;
    }

    sandbox->stdin_fd = stdin_fd;
    sandbox->stdout_fd = stdout_fd;
    close(pidfd);
    return 0;

cleanup:
    if (pidfd != -1) {
        close(pidfd);
    }
    if (stdin_fd != -1) {
        close(stdin_fd);
    }
    if (stdout_fd != -1) {
        close(stdout_fd);
    }
    return -1;
}


int communicate(sandbox_t *sandbox, char *message) {
    char *buffer = NULL;
    ssize_t bytes_written = -1, bytes_read = -1;

    // Write message to sandbox's stdin
    bytes_written = write(sandbox->stdin_fd, message, strlen(message));
    if (bytes_written < 0) {
        printf("err = %s\n", strerror(errno));
        printf("Failed to write to sandbox stdin\n");
        return -1;
    }

    buffer = calloc(1, MAX_STRING_SIZE);
    if (!buffer) {
        printf("Failed to allocate buffer\n");
        return -1;
    }

    // Read response from sandbox's stdout
    bytes_read = read(sandbox->stdout_fd, buffer, MAX_STRING_SIZE - 1);
    if (bytes_read < 0) {
        printf("Failed to read from sandbox stdout\n");
        free(buffer);
        return -1;
    }

    // Null-terminate the response
    buffer[bytes_read] = '\0';
    printf("Received message from sandboxed pid : %d, message: %s\n", sandbox->pid, buffer);
    free(buffer);
    return 0;
}

int main(void) {
    struct command cmd = { 0 };
    ssize_t bytes_read = -1;
    char *uid = NULL;
    char *gid = NULL;
    char *message = NULL;

    // Setup buffering
    setvbuf(stdout, NULL, _IOLBF, 0);  // Line-buffered stdout
    setvbuf(stdin, NULL, _IOLBF, 0);  // Line-buffered stdin
    setvbuf(stderr, NULL, _IOLBF, 0);  // Line-buffered stderr

    while (1) {
        // Read command type and length
        bytes_read = read(0, &cmd, sizeof(cmd));
        if (bytes_read == 0)
            continue;
        
        if (bytes_read < 0)
            break;

        // Handle
        switch(cmd.type) {
            case CMD_CREATE: {
                size_t uid_size = 0, gid_size = 0, elf_size = 0;
                int memfd = -1;

                if (sandbox_count >= MAX_SANDBOXES) {
                    send_error(1, "Max sandboxes reached");
                    break;
                }

                // Setup!
                if (!uid) {
                    uid = calloc(1, MAX_STRING_SIZE);
                    if (!uid)
                        FAIL("Failed to allocate uid");
                }
                if (!gid){
                    gid = calloc(1, MAX_STRING_SIZE);
                    if (!gid)
                        FAIL("Failed to allocate gid");
                }

                // Clear them
                memset(uid, '\x00', MAX_STRING_SIZE);
                memset(gid, '\x00', MAX_STRING_SIZE);
                
                // Receive uid string and its size
                bytes_read = read(0, &uid_size, sizeof(uid_size));
                if ((bytes_read != sizeof(uid_size)) || 
                    (uid_size >= MAX_STRING_SIZE)) {
                    send_error(1, "Failed to receive UID size");
                    break;
                }

                bytes_read = read(0, uid, uid_size);
                if (bytes_read != uid_size) {
                    send_error(1, "Failed to receive UID");
                    break;
                }
                uid[uid_size] = '\0';  // Ensure null-termination

                // Verify this is an actual number
                if (!is_valid_number(uid)) {
                    send_error(1, "Invalid UID");
                    break;
                }

                bytes_read = read(0, &gid_size, sizeof(gid_size));
                // Receive gid string and its size
                if ((bytes_read != sizeof(gid_size)) ||
                    (gid_size >= MAX_STRING_SIZE)) {
                    send_error(1, "Failed to receive GID size");
                    break;
                }

                bytes_read = read(0, gid, gid_size);
                if (bytes_read != gid_size) {
                    send_error(1, "Failed to receive GID");
                    break;
                }
                gid[gid_size] = '\0';  // Ensure null-termination

                // Verify this is an actual number
                if (!is_valid_number(gid)) {
                    send_error(1, "Invalid GID");
                    break;
                }

                // Receive ELF binary size
                if (read(0, &elf_size, sizeof(elf_size)) != sizeof(elf_size)) {
                    send_error(1, "Failed to receive ELF size");
                    break;
                }

                // Create memfd
                memfd = memfd_create("sandbox_elf", MFD_CLOEXEC);
                if (memfd == -1) {
                    send_error(1, "Failed to create memfd");
                    break;
                }

                // Receive ELF binary directly into memfd
                size_t total_received = 0;
                while (total_received < elf_size) {
                    char buffer[1024] = { 0 };
                    size_t to_receive = ((elf_size - total_received) < sizeof(buffer)) ? 
                                        (elf_size - total_received) : sizeof(buffer);
                    
                    ssize_t received = read(0, buffer, to_receive);
                    if (received <= 0) {
                        close(memfd);
                        send_error(1, "Failed to receive ELF binary");
                        break;
                    }

                    if (write(memfd, buffer, received) != received) {
                        close(memfd);
                        send_error(1, "Failed to write ELF to memfd");
                        break;
                    }

                    total_received += received;
                }

                if (total_received != elf_size) {
                    close(memfd);
                    send_error(1, "Incomplete ELF binary received");
                    break;
                }

                printf("Creating sandbox: received ELF binary of size: %zu bytes\n", elf_size);

                // Prepare sandbox arguments
                sandbox_args_t args_param = {
                    .uid = uid,
                    .gid = gid,
                    .fd = memfd
                };

                // Create the sandbox (placeholder)
                pid_t child_pid = create_sandbox(&args_param);
                if (child_pid == -1) {
                    close(memfd);
                    send_error(1, "Failed to create sandbox");
                    break;
                }
                sandboxes[sandbox_count].pid = child_pid;
                sandbox_count++;
                printf("Sucessfully created sandbox!\n");
                break;
            }
            case CMD_CONNECT: {
                int sandbox_id = -1;
                int bytes_read = -1 ;
                
                bytes_read = read(0, &sandbox_id, sizeof(sandbox_id));
                if (bytes_read != sizeof(sandbox_id)) {
                    send_error(1, "Failed to receive sandbox id");
                    break;
                }

                if (sandbox_id >= 0 && sandbox_id < sandbox_count) {
                    int result = connect_sandbox(&sandboxes[sandbox_id]);

                    if (result == -1) {
                        printf("Connect sandbox error returned: %d\n", result);
                    }
                    else{
                        printf("Successfully connected to sandbox id: %d, PID: %d\n", sandbox_id, sandboxes[sandbox_id].pid);
                    }
                } else {
                    printf("Connect sandbox failed with invalid sandbox id\n");
                }
                break;
            }
            case CMD_COMMUNICATE: {
                int sandbox_id = -1;
                // Allocate message if it does not exist
                if (!message) {
                    message = calloc(1, MAX_STRING_SIZE);
                    if (!message)
                        FAIL("Failed to allocate message");
                }
                
                // Clear it
                memset(message, '\x00', MAX_STRING_SIZE);

                // Read sandbox_id
                if (read(0, &sandbox_id, sizeof(int)) != sizeof(int)) {
                    perror("Failed to read sandbox_id");
                    break;
                }

                // Read message
                ssize_t message_len = read(0, message, MAX_STRING_SIZE - 1);
                if (message_len < 0) {
                    perror("Failed to read message");
                    break;
                }
                message[message_len] = '\0';  // Null-terminate the message

                // Validate sandbox_id
                if (sandbox_id < 0 || sandbox_id >= sandbox_count || sandboxes[sandbox_id].stdin_fd == -1 || sandboxes[sandbox_id].stdout_fd == -1) {
                    printf("Invalid sandbox_id: %d\n", sandbox_id);
                    break;
                }

                // Communicate with the sandbox
                if (communicate(&sandboxes[sandbox_id], message) < 0) {
                    printf("Communication with sandbox %d failed\n", sandbox_id);
                }

                printf("Successfully communicated with sandbox %d!\n", sandbox_id);
                break;
            }
            default: {
                printf("Invalid option\n");
                break;
            }
        }
    }

    return 0;
}
