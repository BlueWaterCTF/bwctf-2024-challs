#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <stdint.h>
#include "openssl/sha.h"

#define BSIZE
#define BNUM BSIZE*BSIZE

uint64_t row_cells[BNUM] = {0};
uint64_t col_cells[BNUM] = {0};

uint64_t row_values[BNUM] = {0};
uint64_t col_values[BNUM] = {0};

int answer_count = 0;

// NOTE: FUNCS

__attribute__((constructor))
void setup_start_values() {
    // NOTE: START_VALUES
}

void (*row_func_ptr[BNUM])(uint64_t, uint64_t) = {
    // NOTE: ROW_FUNC_PTRS
};
void (*col_func_ptr[BNUM])(uint64_t, uint64_t) = {
    // NOTE: COL_FUNC_PTRS
};

int main()
{
    char buf[1024] = {0};

    setvbuf(stdin, NULL, _IONBF, 0);
    setvbuf(stdout, NULL, _IONBF, 0);

    scanf("%400s", buf);
    
    if (strlen(buf) != BNUM / 4)
        return 1;

    for (int i = 0; i < BNUM / 4; i++) {
        uint64_t v = 0;
        if ('0' <= buf[i] && buf[i] <= '9')
            v = buf[i] - '0';
        else if ('a' <= buf[i] && buf[i] <= 'f')
            v = buf[i] - 'a' + 10;
        else
            return 1;
        
        for (int j = 0; j < 4; j++) {
            row_cells[4 * i + j] = v & 1;
            col_cells[4 * i + j] = v & 1;

            v >>= 1;
        }
    }

    int count = 0;

    while (count < BNUM * 2) {
        for (int i = 0; i < BNUM; i++) {
            if (row_values[i]) {
                row_func_ptr[i](row_values[i], row_cells[i]);
                count++;
                row_values[i] = 0;
            }
            if (col_values[i]) {
                col_func_ptr[i](col_values[i], col_cells[i]);
                count++;
                col_values[i] = 0;
            }
        }
    }

    if (answer_count == BSIZE * 2) {
        printf("Correct!\n");

        uint8_t res[SHA256_DIGEST_LENGTH] = {0};
        SHA256_CTX ctx;
        SHA256_Init(&ctx);
        SHA256_Update(&ctx, buf, strlen(buf));
        SHA256_Final(res, &ctx);

        printf("The flag is: bwctf{");
        for (int i = 0; i < SHA256_DIGEST_LENGTH; i++)
            printf("%02x", res[i]);
        printf("}\n");

    } else {
        printf("Wrong!\n");
    }
    return 0;
}