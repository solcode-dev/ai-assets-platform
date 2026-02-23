import sys
import re

# ANSI Color Codes
RESET = "\033[0m"
BG_RED = "\033[41;37m"     # Error
BG_GREEN = "\033[42;30m"   # Success (OK)
BG_PURPLE = "\033[45;37m"  # Warning

def colorize(line):
    # Strip existing newline
    clean_line = line.rstrip()
    if not clean_line:
        return line

    # Split label and content (usually separated by ' | ')
    parts = clean_line.split('|', 1)
    label = parts[0]
    content = parts[1] if len(parts) > 1 else ""

    # Determine status color based on full line content
    status_bg = None
    if re.search(r"(?i)(error|failed|exception|failure|refused|critical|fatal| 500 |🔴)", clean_line):
        status_bg = BG_RED
    elif re.search(r"(?i)(Warning|WARNING|warning|warn| 400 | 404 |🟣)", clean_line):
        status_bg = BG_PURPLE
    elif re.search(r"(?i)(success|completed|ready|started| 200 | 304 |✓|successfully|🟢)", clean_line):
        status_bg = BG_GREEN

    if status_bg:
        # Only colorize the label part
        return f"{status_bg}{label}|{RESET}{content}\n"
    
    return line

def main():
    try:
        # sys.stdin is buffered by default, but we want real-time
        for line in sys.stdin:
            print(colorize(line), end='', flush=True)
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
