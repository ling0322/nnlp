package errors

import "fmt"

type keyErrorImpl struct {
	Message string
}

func (e *keyErrorImpl) Error() string {
	return fmt.Sprintf("KeyError: %s", e.Message)
}

func KeyError(message string) error {
	return &keyErrorImpl{
		Message: message,
	}
}
