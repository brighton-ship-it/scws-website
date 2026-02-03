const fs = require('fs');
const path = require('path');

const blogDir = path.join(__dirname, 'blog');
const files = fs.readdirSync(blogDir).filter(f => f.endsWith('.html') && f !== 'index.html');

let updated = 0;
let skipped = 0;

files.forEach(file => {
    const filePath = path.join(blogDir, file);
    let content = fs.readFileSync(filePath, 'utf8');
    
    // Skip if already has BreadcrumbList
    if (content.includes('BreadcrumbList')) {
        skipped++;
        return;
    }
    
    // Extract title
    const titleMatch = content.match(/<title>([^<]+)<\/title>/);
    const title = titleMatch ? titleMatch[1].replace(/"/g, '\\"') : file.replace('.html', '');
    
    // Breadcrumb schema
    const breadcrumbSchema = `
    <script type="application/ld+json">
    {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": "https://scwellservice.com/"},
            {"@type": "ListItem", "position": 2, "name": "Resources", "item": "https://scwellservice.com/blog/"},
            {"@type": "ListItem", "position": 3, "name": "${title}"}
        ]
    }
    </script>`;
    
    // Insert before </head>
    content = content.replace('</head>', breadcrumbSchema + '\n</head>');
    
    fs.writeFileSync(filePath, content);
    updated++;
});

console.log(`✅ Added breadcrumb schema to ${updated} blog posts`);
console.log(`⏭️ Skipped ${skipped} (already had breadcrumbs)`);
