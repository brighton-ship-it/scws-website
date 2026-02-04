#!/bin/bash
# SEO Fix Script - Add breadcrumb schema to all blog posts

cd ~/clawd/scws-website/blog

echo "Adding breadcrumb schema to blog posts..."

for file in *.html; do
    # Skip if already has BreadcrumbList
    if grep -q "BreadcrumbList" "$file"; then
        continue
    fi
    
    # Get the title from the file
    title=$(grep -o '<title>[^<]*</title>' "$file" | sed 's/<[^>]*>//g' | head -1)
    
    # Create breadcrumb schema
    breadcrumb_schema='<script type="application/ld+json">
    {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": 1,
                "name": "Home",
                "item": "https://scwellservice.com/"
            },
            {
                "@type": "ListItem",
                "position": 2,
                "name": "Resources",
                "item": "https://scwellservice.com/blog/"
            },
            {
                "@type": "ListItem",
                "position": 3,
                "name": "'"${title//\"/\\\"}"'"
            }
        ]
    }
    </script>'
    
    # Insert after the first </script> in head (after Article schema)
    if grep -q 'type="application/ld\+json"' "$file"; then
        # Add breadcrumb after existing schema
        sed -i '' '/<\/script>/,/<\/head>/{
            /<\/script>/{
                a\
'"$(echo "$breadcrumb_schema" | sed 's/$/\\/' | sed '$ s/\\$//')"'
                b
            }
        }' "$file" 2>/dev/null || echo "  Skipped $file (sed issue)"
    fi
done

echo "Done adding breadcrumb schema"
