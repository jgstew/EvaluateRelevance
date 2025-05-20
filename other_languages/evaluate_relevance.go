// Project: evaluate_relevance
// File: evaluate_relevance.go
// This is a Go program that evaluates relevance expressions using the QNA tool.
// This is based upon: https://github.com/jgstew/EvaluateRelevance/blob/main/evaluate_relevance.py
package main

import (
	"bufio"
	"bytes"
	"errors"
	"fmt"
	"io"
	"os"
	"os/exec"
	"runtime"
	"strings"
	"sync"
	"time"
)

const (
	defaultInputFile     = "relevance_tmp.txt"
	fileWriteOutput      = false
	defaultRelevance     = "version of client"
	noRelevanceSpecified = `("No Relevance Specified", TRUE, version of client)`
)

var qnaPaths = []string{
	"/usr/local/bin/qna",
	"/Library/BESAgent/BESAgent.app/Contents/MacOS/QnA",
	"/opt/BESClient/bin/qna",
	"C:/Program Files (x86)/BigFix Enterprise/BES Client/qna.exe",
	"qna",
	"qna.exe",
}

func getQnaPath() (string, error) {
	for _, path := range qnaPaths {
		if _, err := os.Stat(path); err == nil {
			if isExecutable(path) {
				return path, nil
			}
		}
	}
	return "", errors.New("valid QNA path not found")
}

func isExecutable(path string) bool {
	info, err := os.Stat(path)
	if err != nil {
		return false
	}

	// Check if it's a regular file and has executable permissions
	if runtime.GOOS == "windows" {
		return !info.IsDir()
	}
	return !info.IsDir() && info.Mode()&0111 != 0
}

func parseRawResultArray(result string) []string {
	scanner := bufio.NewScanner(strings.NewReader(result))
	var results []string

	for scanner.Scan() {
		line := scanner.Text()
		if strings.HasPrefix(line, "Q: A: ") {
			results = append(results, strings.TrimPrefix(line, "Q: A: "))
		} else if strings.HasPrefix(line, "A: ") {
			results = append(results, strings.TrimPrefix(line, "A: "))
		}
	}

	return results
}

func evaluateRelevanceString(relevance, separator string, pathQna string) (string, error) {
	results, err := evaluateRelevanceArray(relevance, pathQna)
	if err != nil {
		return "", err
	}
	return strings.Join(results, separator), nil
}

func evaluateRelevanceArray(relevance, pathQna string) ([]string, error) {
	raw, err := evaluateRelevanceRaw(relevance, pathQna)
	if err != nil {
		return nil, err
	}
	return parseRawResultArray(raw), nil
}

func evaluateRelevanceRawStdin(relevance, pathQna string) (string, error) {
	// Remove Q: prefix if present
	if strings.HasPrefix(relevance, "Q: ") {
		relevance = relevance[3:]
	}

	// Check if running as root on MacOS
	if runtime.GOOS == "darwin" && os.Geteuid() != 0 {
		return "", errors.New("this script must be run as root or with sudo on MacOS")
	}

	if pathQna == "" {
		var err error
		pathQna, err = getQnaPath()
		if err != nil {
			return "", err
		}
	}

	startTime := time.Now()
	cmd := exec.Command(pathQna, "-t", "-showtypes")

	// Set up stdin
	stdin, err := cmd.StdinPipe()
	if err != nil {
		return "", err
	}

	// Write relevance to stdin in a goroutine
	go func() {
		defer stdin.Close()
		io.WriteString(stdin, relevance+"\n")
	}()

	// Capture output concurrently
	var stdoutBuf, stderrBuf bytes.Buffer
	cmd.Stdout = &stdoutBuf
	cmd.Stderr = &stderrBuf

	// Start the command
	err = cmd.Start()
	if err != nil {
		return "", err
	}

	// Wait for the command to finish in a goroutine
	done := make(chan error, 1)
	go func() {
		done <- cmd.Wait()
	}()

	// Wait for command to finish or timeout
	select {
	case err := <-done:
		if err != nil {
			return "", err
		}
	case <-time.After(30 * time.Second): // Timeout after 30 seconds
		cmd.Process.Kill()
		return "", errors.New("command timed out")
	}

	elapsed := time.Since(startTime)
	output := stdoutBuf.String()
	errorOutput := stderrBuf.String()

	output += fmt.Sprintf("Time Taken: %s as measured by Go.\n", elapsed)
	if errorOutput != "" {
		fmt.Printf("Error: %s\n", errorOutput)
	}

	if strings.Contains(output, `E: The operator "string" is not defined.`) {
		output += "\nInfo: This error means a result was found, but it does not have a string representation."
	}

	if fileWriteOutput {
		err := os.WriteFile("relevance_out.txt", []byte(output), 0644)
		if err != nil {
			return output, err
		}

		results := parseRawResultArray(output)
		err = os.WriteFile("relevance_str.txt", []byte(strings.Join(results, "\n")), 0644)
		if err != nil {
			return output, err
		}
	}

	return output, nil
}

func evaluateRelevanceRawFile(relFilePath string) (string, error) {
	if runtime.GOOS == "darwin" && os.Geteuid() != 0 {
		return "", errors.New("this script must be run as root or with sudo on MacOS")
	}

	startTime := time.Now()
	pathQna, err := getQnaPath()
	if err != nil {
		return "", err
	}

	cmd := exec.Command(pathQna, "-t", "-showtypes", relFilePath)
	var stdoutBuf, stderrBuf bytes.Buffer
	cmd.Stdout = &stdoutBuf
	cmd.Stderr = &stderrBuf

	err = cmd.Run()
	if err != nil {
		return "", err
	}

	elapsed := time.Since(startTime)
	output := stdoutBuf.String()
	errorOutput := stderrBuf.String()

	output += fmt.Sprintf("Time Taken: %s as measured by Go.\n", elapsed)
	if errorOutput != "" {
		fmt.Printf("Error: %s\n", errorOutput)
	}

	if strings.Contains(output, `E: The operator "string" is not defined.`) {
		output += "\nInfo: This error means a result was found, but it does not have a string representation."
	}

	if fileWriteOutput {
		err := os.WriteFile("relevance_out.txt", []byte(output), 0644)
		if err != nil {
			return output, err
		}

		results := parseRawResultArray(output)
		err = os.WriteFile("relevance_str.txt", []byte(strings.Join(results, "\n")), 0644)
		if err != nil {
			return output, err
		}
	}

	return output, nil
}

func writeRelevanceFile(relevance, relFilePath string) error {
	if !strings.HasPrefix(relevance, "Q: ") {
		relevance = "Q: " + relevance
	}
	return os.WriteFile(relFilePath, []byte(relevance), 0644)
}

func evaluateRelevancesArrayToMany(relevances []string, resultsType string, pathQna string) ([][]string, error) {
	if len(relevances) == 0 {
		return nil, errors.New("relevances list is empty")
	}

	if pathQna == "" {
		var err error
		pathQna, err = getQnaPath()
		if err != nil {
			return nil, err
		}
	}

	var wg sync.WaitGroup
	results := make([][]string, len(relevances))
	errChan := make(chan error, len(relevances))

	for i, relevance := range relevances {
		wg.Add(1)
		go func(idx int, rel string) {
			defer wg.Done()

			var res []string
			var err error

			if resultsType == "array" {
				res, err = evaluateRelevanceArray(rel, pathQna)
			} else {
				str, e := evaluateRelevanceString(rel, "\n", pathQna)
				res = []string{str}
				err = e
			}

			if err != nil {
				errChan <- err
				return
			}

			results[idx] = res
		}(i, relevance)
	}

	wg.Wait()
	close(errChan)

	for err := range errChan {
		if err != nil {
			return nil, err
		}
	}

	return results, nil
}

func evaluateRelevanceRaw(relevance, pathQna string) (string, error) {
	return evaluateRelevanceRawStdin(relevance, pathQna)
}

func main() {
	args := os.Args[1:]

	var cmdArgs string
	if len(args) == 1 {
		cmdArgs = args[0]
	} else if len(args) > 1 {
		cmdArgs = strings.Join(args, " ")
	}

	if cmdArgs != "" {
		if _, err := os.Stat(cmdArgs); err == nil {
			output, err := evaluateRelevanceRawFile(cmdArgs)
			if err != nil {
				fmt.Println("Error:", err)
				os.Exit(1)
			}
			fmt.Println(output)
			return
		} else {
			fmt.Println("Note: this will not work on the command line directly in all cases. May require odd quote escaping.")
			if strings.HasPrefix(cmdArgs, "Q: ") {
				fmt.Println(cmdArgs + "\n")
			} else {
				fmt.Println("Q: " + cmdArgs + "\n")
			}

			output, err := evaluateRelevanceRaw(cmdArgs, "")
			if err != nil {
				fmt.Println("Error:", err)
				os.Exit(1)
			}
			fmt.Println(output)

			os.Remove(defaultInputFile)
			return
		}
	}

	if _, err := os.Stat(defaultInputFile); err == nil {
		output, err := evaluateRelevanceRawFile(defaultInputFile)
		if err != nil {
			fmt.Println("Error:", err)
			os.Exit(1)
		}
		fmt.Println(output)
	} else {
		output, err := evaluateRelevanceRaw(noRelevanceSpecified, "")
		if err != nil {
			fmt.Println("Error:", err)
			os.Exit(1)
		}
		fmt.Println(output)
	}
	// fmt.Println("test many:")
	// var result [][]string
	// result, _ = evaluateRelevancesArrayToMany([]string{"version of client", "name of operating system", "version of operating system", "sum of integers in (1,1000)"}, "array", "")

	// // Print the results
	// for i, res := range result {
	// 	fmt.Printf("Result %d: %v\n", i+1, res)
	// }
}
