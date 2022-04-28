package nmutfst

import "strings"

// NormalizeFstText normailzes the format of Fst text
func NormalizeFstText(text string) string {
	lines := strings.Split(text, "\n")
	normLines := []string{}
	for _, line := range lines {
		line = strings.TrimSpace(line)
		if line == "" {
			continue
		}
		normLines = append(normLines, line)
	}

	return strings.Join(normLines, "\n") + "\n"
}
