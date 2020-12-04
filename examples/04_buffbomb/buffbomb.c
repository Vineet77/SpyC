/* Bomb program that is solved using a buffer overflow attack */

#include <stdio.h>
#include <stdlib.h>
#include <ctype.h>
#include <signal.h>
#include <unistd.h>

/* Signal handler to catch bus errors */
void bushandler(int sig)
{
    printf("Crash!: You caused a bus error!\n");
    printf("Better luck next time\n");
    exit(0);
}

/* Signal handler to catch segmentation violations */
void seghandler(int sig)
{
    printf("Ouch!: You caused a segmentation fault!\n");
    printf("Better luck next time\n");
    exit(0);
}

/* Alarm handler to catch infinite loops */
static int alarm_time = 600;

void alarmhandler(int sig)
{
    printf("Dead!: getbuf didn't complete within %d seconds\n", alarm_time);
    printf("Better luck next time\n");
    exit(0);
}

/* Illegal instruction handler */
void illegalhandler(int sig)
{
    printf("Oops!: You executed an illegal instruction\n");
    printf("Better luck next time\n");
    exit(0);
}

/* Like gets, except that characters are typed as pairs of hex digits.
   Nondigit characters are ignored.  Stops when encounters newline */
char *getxs(char *dest)
{
  int c;
  int even = 1; /* Have read even number of digits */
  int otherd = 0; /* Other hex digit of pair */
  char *sp = dest;
  while ((c = getchar()) != EOF && c != '\n') {
    if (isxdigit(c)) {
      int val;
      if ('0' <= c && c <= '9')
	val = c - '0';
      else if ('A' <= c && c <= 'F')
	val = c - 'A' + 10;
      else
	val = c - 'a' + 10;
      if (even) {
	otherd = val;
	even = 0;
      } else {
	*sp++ = otherd * 16 + val;
	even = 1;
      }
    }
  }
  *sp++ = '\0';
  return dest;
}

int getbuf() {
	char buf[16];

	getxs(buf);
	return 1;
}

void test() {
	int val;

	printf("Type Hex String: ");
	val = getbuf();
	printf("getbuf returned 0x%x\n", val);
}

void smoke() {
	printf("Smoke: You called smoke()\n");
	exit(0);
}

void fizz(int val) {
	if (val == 0xdeadbeef) {
		printf("Fizz!: You called fizz (0x%x)\n", val);
	}
	else {
		printf("Misfire: You called fizz (0x%x)\n", val);
	}
	exit(0);
}

int global_value = 0;

void bang() {
	if (global_value == 0xdeadbeef) {
		printf("Bang!: You set global_value to 0x%x\n", global_value);
	}
	else {
		printf("Misfire: global_value = 0x%x\n", global_value);
	}
	exit(0);
}

int main()
{

  int buf[16];
  /* This little hack is an attempt to get the stack to be in a
     stable position
  */
  int offset = (((int) buf) & 0xFFFF);
  int *space = (int *) alloca(offset);

  *space = 0; /* So that don't get complaint of unused variable */

  signal(SIGSEGV, seghandler);
  signal(SIGBUS, bushandler);
  signal(SIGALRM, alarmhandler);
  signal(SIGILL,  illegalhandler);

  /* Set up time out condition */
  alarm(alarm_time);

  test();
  return 0;
}
