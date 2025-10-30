#!/bin/bash

# Path to .gitignore
GITIGNORE_FILE=".gitignore"

# Check if .gitignore exists
if [ ! -f "$GITIGNORE_FILE" ]; then
  echo ".gitignore file not found!"
  exit 1
fi
# Iterate through each line in .gitignore
while IFS= read -r line; do
  # Skip empty lines and comments
  if [[ -n "$line" && ! "$line" =~ ^# ]]; then
    # Remove trailing slash for directories
    target="${line%/}"
    echo "Removing cached files for: $target"
    git rm -r --cached "$target" 2>/dev/null
  fi
done < "$GITIGNORE_FILE"

echo "✅ Finished removing tracked files listed in .gitignore"