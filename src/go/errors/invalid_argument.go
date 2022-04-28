package errors

import "fmt"

type InvalidArgumentError struct {
	Message string
}

func (e *InvalidArgumentError) Error() string {
	return fmt.Sprintf("Invalid argument: %s", e.Message)
}

func InvalidArgument(message string) *InvalidArgumentError {
	return &InvalidArgumentError{
		Message: message,
	}
}
