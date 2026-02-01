#!/bin/bash

# Function to update a single HTML file
update_file() {
    local file="$1"
    echo "Updating: $file"
    
    # Create temp file
    local temp=$(mktemp)
    
    # Remove Tailwind CDN and config, add CSS link
    # Also fix Google Fonts to use display=swap
    sed -E '
        # Remove Tailwind CDN script
        /<script src="https:\/\/cdn\.tailwindcss\.com"><\/script>/d
        
        # Remove tailwind.config block (multiline - mark for deletion)
        /<script>/{
            N
            /tailwind\.config/,/<\/script>/{
                /<\/script>/!d
                s/.*<\/script>//
            }
        }
        
        # Add font-display=swap to Google Fonts if not present
        s/(fonts\.googleapis\.com\/css2[^"]*)/\1\&display=swap/
        s/display=swap\&display=swap/display=swap/
        
    ' "$file" > "$temp"
    
    mv "$temp" "$file"
}

# Process all HTML files
for file in *.html blog/*.html; do
    if [ -f "$file" ]; then
        update_file "$file"
    fi
done

echo "Done!"
