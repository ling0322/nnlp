package errors

import "fmt"

type unexpectedErrorImpl struct {
	Message string
}

func (e *unexpectedErrorImpl) Error() string {
	return fmt.Sprintf("Unexpected: %s", e.Message)
}

func Unexpected(message string) error {
	return &unexpectedErrorImpl{
		Message: message,
	}
}
