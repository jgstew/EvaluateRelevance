// Project: evaluate_relevance
// File: evaluate_relevance.go
// This does not work with concurrency due to use of files!
// Need to use Stdin/Stdout instead of files.
// This is a Go program that evaluates relevance expressions using the QNA tool.
package main

import (
	"errors"
	"fmt"
	"os"
	"os/exec"
	"regexp"
	"strings"
	"time"
)

const (
	defaultInputFile = "relevance_tmp.txt"
)

func getPathQNA() (string, error) {
	testFilePaths := []string{
		"/usr/local/bin/qna",
		"/Library/BESAgent/BESAgent.app/Contents/MacOS/QnA",
		"/opt/BESClient/bin/qna",
		"C:/Program Files (x86)/BigFix Enterprise/BES Client/qna.exe",
		"qna",
		"qna.exe",
	}

	for _, filePath := range testFilePaths {
		if fileInfo, err := os.Stat(filePath); err == nil {
			// Check if it's a regular file and executable
			if fileInfo.Mode().IsRegular() {
				// Check executable bit (simplified check - more robust checks needed for cross-platform)
				if fileInfo.Mode()&0111 != 0 {
					return filePath, nil
				}
			}
		}
	}

	return "", errors.New("valid QNA path not found")
}

func parseRawResultArray(result string) []string {
	// Split the result string into an array using regex
	re := regexp.MustCompile(`\r\n|\r|\n`)
	resultsArrayRaw := re.Split(result, -1)
	var resultsArray []string

	for _, resultRaw := range resultsArrayRaw {
		if strings.HasPrefix(resultRaw, "A: ") {
			resultsArray = append(resultsArray, strings.SplitN(resultRaw, "A: ", 2)[1])
		}
	}
	return resultsArray
}

func evaluateRelevanceString(relevance string, separator string) string {
	return strings.Join(evaluateRelevanceArray(relevance), separator)
}

func evaluateRelevanceArray(relevance string) []string {
	return parseRawResultArray(evaluateRelevanceRaw(relevance, defaultInputFile))
}

func evaluateRelevanceRawFile(relFilePath string) string {
	startTime := time.Now()

	qnaPath, err := getPathQNA()
	if err != nil {
		return "Error: " + err.Error()
	}

	cmd := exec.Command(qnaPath, "-t", "-showtypes", relFilePath)
	output, err := cmd.CombinedOutput()
	if err != nil {
		return "Error: " + err.Error() + "\nOutput: " + string(output)
	}

	outputData := string(output)
	elapsedTime := time.Since(startTime)

	outputData += "Time Taken: " + elapsedTime.String() + " as measured by Go.\n"

	if strings.Contains(outputData, `E: The operator "string" is not defined.`) {
		outputData += "\nInfo: This error means a result was found, but it does not have a string representation."
	}

	err = os.WriteFile("relevance_out.txt", []byte(outputData), 0644)
	if err != nil {
		fmt.Println("Error writing relevance_out.txt:", err)
	}

	results := parseRawResultArray(outputData)
	err = os.WriteFile("relevance_str.txt", []byte(strings.Join(results, "\n")), 0644)
	if err != nil {
		fmt.Println("Error writing relevance_str.txt:", err)
	}

	return outputData
}

func evaluateRelevanceRaw(relevance string, relFilePath string) string {
	if !strings.HasPrefix(relevance, "Q: ") {
		relevance = "Q: " + relevance
	}

	err := os.WriteFile(relFilePath, []byte(relevance), 0644)
	if err != nil {
		return "Error writing to temp file: " + err.Error()
	}

	return evaluateRelevanceRawFile(relFilePath)
}

func main() {
	relevance := "version of client"
	args := os.Args[1:]

	if len(args) == 1 {
		cmdArg := args[0]
		if fileInfo, err := os.Stat(cmdArg); err == nil && !fileInfo.IsDir() {
			fmt.Println(evaluateRelevanceRawFile(cmdArg))
			return
		} else {
			if strings.HasPrefix(cmdArg, "Q: ") {
				fmt.Println(cmdArg + "\n")
			} else {
				fmt.Println("Q: " + cmdArg + "\n")
			}
			fmt.Println("Note: this will not work on the command line directly in all cases. May require odd quote escaping.")
			relevance = cmdArg
		}
	} else if len(args) > 1 {
		cmdArg := strings.Join(args, " ")
		if strings.HasPrefix(cmdArg, "Q: ") {
			fmt.Println(cmdArg + "\n")
		} else {
			fmt.Println("Q: " + cmdArg + "\n")
		}
		fmt.Println("Note: this will not work on the command line directly in all cases. May require odd quote escaping.")
		relevance = cmdArg
	} else {
		if fileInfo, err := os.Stat(defaultInputFile); err == nil && !fileInfo.IsDir() {
			fmt.Println(evaluateRelevanceRawFile(defaultInputFile))
			return
		} else {
			relevance = `("No Relevance Specified", TRUE, version of client)`
		}
	}

	fmt.Println(evaluateRelevanceRaw(relevance, defaultInputFile))

	// Clean up temp file
	err := os.Remove(defaultInputFile)
	if err != nil && !os.IsNotExist(err) {
		fmt.Println("Error removing temp file:", err)
	}
}
