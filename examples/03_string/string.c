#include <stdio.h>
#include <emscripten.h>
#include <string.h>
#include <stdlib.h>

EMSCRIPTEN_KEEPALIVE
int square(int n)
{
    return n * n;
}


char* temp(const char* str){
    char buffer1[11] = "helloworld";
    char *buffer2 = (char *)malloc(3000);
    printf("Malloced %d\n", buffer2);
    strncpy(buffer2, buffer1, 11);
    strncpy(buffer2 + 10, str, 12);
    printf("Returning %s\n", buffer2);
    return buffer2;
}

EMSCRIPTEN_KEEPALIVE
char *allocateBuffer(const char *str)
{
    char buffer1[11] = "helloworld";
    char *buffer2 = (char *)malloc(3000);
    printf("Malloced %d\n", buffer2);
    strncpy(buffer2, buffer1, 11);
    strncpy(buffer2 + 10, str, 12);
    printf("Returning %s\n", buffer2);
    return temp(str);
}

