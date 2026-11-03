/* Runs a child, passes its stdout through, then prints seconds=<wall> maxrss_kb=<peak memory> cpu_s=<user+sys>.
   cpu_s well above seconds means the program used more than one thread. */
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <time.h>
#include <sys/wait.h>
#include <sys/resource.h>
int main(int argc, char **argv) {
    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    pid_t pid = fork();
    if (pid == 0) { execvp(argv[1], argv + 1); perror("execvp"); _exit(127); }
    int status; struct rusage ru;
    wait4(pid, &status, 0, &ru);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double s = (t1.tv_sec - t0.tv_sec) + (t1.tv_nsec - t0.tv_nsec) / 1e9;
    double cpu = ru.ru_utime.tv_sec + ru.ru_utime.tv_usec / 1e6 + ru.ru_stime.tv_sec + ru.ru_stime.tv_usec / 1e6;
    printf("seconds=%.4f maxrss_kb=%ld cpu_s=%.4f\n", s, (long)(ru.ru_maxrss / 1024), cpu);
    return WEXITSTATUS(status);
}
