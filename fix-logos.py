import os
import re

# Fix services pages - replace text logo with image logo
services_count = 0
for root, dirs, files in os.walk('services'):
    for f in files:
        if f.endswith('.html'):
            path = os.path.join(root, f)
            with open(path, 'r') as file:
                content = file.read()
            
            # Replace text logo with image logo
            old_pattern = r'<a href="/" class="logo">Southern California Well Service</a>'
            new_logo = '<a href="/" class="logo"><img src="/images/logo.png" alt="Southern California Well Service" style="height: 40px;"></a>'
            
            if old_pattern in content or re.search(old_pattern, content):
                new_content = re.sub(old_pattern, new_logo, content)
                with open(path, 'w') as file:
                    file.write(new_content)
                services_count += 1

print(f"Fixed {services_count} service pages")

# Fix blog pages - replace text logo with image logo
blog_count = 0
for f in os.listdir('blog'):
    if f.endswith('.html'):
        path = os.path.join('blog', f)
        with open(path, 'r') as file:
            content = file.read()
        
        # Check if missing logo.png
        if 'logo.png' not in content:
            # Replace text logo with image logo
            old_pattern = r'<a href="/" class="logo">Southern California Well Service</a>'
            new_logo = '<a href="/" class="logo"><img src="/images/logo.png" alt="Southern California Well Service" style="height: 40px;"></a>'
            
            if re.search(old_pattern, content):
                new_content = re.sub(old_pattern, new_logo, content)
                with open(path, 'w') as file:
                    file.write(new_content)
                blog_count += 1

print(f"Fixed {blog_count} blog pages")
print(f"Total: {services_count + blog_count} pages fixed")
