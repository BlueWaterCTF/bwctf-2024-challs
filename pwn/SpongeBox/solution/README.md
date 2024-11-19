# SpongeBox BWCTF 2024

## How to run the solution scripts?
Basically the challenge allows to create sandboxes and execute binaries in them.
First, run the container as described in the parent directory's `README.md`.

The way you run the exploit here is the following:
1. Run `run_challenge.sh` from within the container, as a privileged user.
    - It will create 2 FIFOs to emulate stdin/stdout instead of using sockets.
2. Run `run_solution.sh` from within the container which runs `exploit.py` and uses the FIFOs to communicate with the sandbox.
    - It uses `first_sandboxee` and `second_sanboxee` which are 2 binaries that are precompiled.

## About the challenge
This is a Linux namespaces sandbox challenge, where you can do the following:
1. **Create a new sandbox** - which will run in separate namespaces, and execute a binary you pass to it.
    * You can choose what UID and GID to use INSIDE the sandbox. This is not problematic, as it only has a meaning INSIDE the User namespace of the sandbox.

2. **Connect to a sandbox** - the sandboxer will use `pidfd()` syscalls to fetch `fd == 0` and `fd == 1` from the launched sandboxee process, and use them to communicate with the sandboxee later on.

3. **Interact with the sandbox** - you can write to the sandboxee's stdin, and read from its stdout (the ones that were mapped to the sandboxer's side using connect).

## The backstory
The main idea behind the challenge is the fact that `uid_map` (and `gid_map`) are writable by different types of users, and some users are allowed to write certain things, while others are not (for example: root is allowed to map the root user, while others non-privileged users can't map the root user).

The idea was to somehow get an arbitrary mapping for a `uid_map`, by somehow getting an FD for a writable `uid_map` file, and then somehow getting that FD into the sandbox.

### Obstacales
When writing to `uid_map`, there are many limitations. But essentially you have to:
1. Be "capable" in the namespace you are writing to (the one you're configuring).
2. The `uid_map` is only writable one time! So this has to be the first mapping.
3. You can only map your outside-uid to a (any) uid inside the namespace.
    * Or, if you're privileged in the parent user-ns, you can map whatever you want. 
    * In our case we won't be privileged.

#### A Linux Kernel history lesson
There used to be an old Linux vulnerability that went like this:
What if I get a privileged process to write whatever I want, to `uid_map`?

This used to be possible if you `open()` the `uid_map` and have it be your stdout/stderr, and then for example `execve()` a setuid binary like sudo.
If you give a wrong password to sudo it will write `sudo: incorrect password` or whatever. So... if you change the `argv[0]` of the `execve()` call to be anything you want, you'd be able to write anything to the `uid_map`.

The way this was fixed is by adding an additional check that the **opener** of the `uid_map` is also privileged over the target `uid_map` file's user namespace.

### The vulnerability

#### Part 1: Getting a privileged FD to a `uid_map`
This analysis examines the flow of creating a new sandbox.

The first issue is that when choosing what UID to be mapped to inside the sandbox, the client passes a numeric string.
In the linux kernel, if the written string is too long, it will fail (in `map_write()`, it will fail if the `write()` tries to write more than `PAGE_SIZE` bytes).

The `setup_idmaps()` function does not check return values, which means that the FD of the `uid_map` will stay in the sandboxer's FD table, and will not be closed.

Cool. We got an interesting primitive as the opener of the `uid_map` is a privileged process. Now we just gotta write to it as a privileged process somehow.

#### Part 2: Writing to the `uid_map`
Alright, we created a sandbox, and it does not have proper mappings. Also, the parent process has a privileged FD leaked to the `uid_map`.
If we then create a new sandbox, we will have that FD in our process.

We can't simply write to it as we don't have the capabilities to do so - there are permission checks upon writing to the `uid_map`.

This is where the `connect` and `communicate` functions come into play - if we use the leaked FD as the stdin of the NEW sandboxee - what's going to happen is as follows:

1. **Connect:** The parent process will call `pidfd_getfd()` which gets the leaked FD back, and it is going to be configured in the same way (opener is still privileged).
2. **Communicate:** During `communicate()` the parent process will write to that same FD, controlled data!
    * Now we have a privileged opener and a privileged writer, which is everything we need to be able to arbitrarily write to the `uid_map`!


We managed to create an arbitrary mapping for the `uid_map`. Nice!

#### Part 3: Escalating privileges
Now, using the first sandboxee we created, we can simply `setuid(0); seteuid(0)` and become privileged in the parent (base) namespace, and read the flag! Win! 

