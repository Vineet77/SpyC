#include <stdio.h>
#include <emscripten.h>
#include <string.h>
#include <stdlib.h>


EMSCRIPTEN_KEEPALIVE
char *allocateBuffer(const char *str)
{
    char *buffer1 = (char *)malloc(32);
    strcpy(buffer1, str);
    return buffer1; 
}

