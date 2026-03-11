#!/usr/bin/env node
const fs = require('fs');
const path = require('path');

const blogDir = path.join(__dirname, '..', 'blog');

const files = fs.readdirSync(blogDir)
  .filter(f => f.endsWith('.html') && f !== 'index.html')
  .map(f => ({ name: f, size: fs.statSync(path.join(blogDir, f)).size }))
  .sort((a, b) => b.size - a.size)
  .slice(0, 100);

let modified = 0;

for (const file of files) {
  const fp = path.join(blogDir, file.name);
  let html = fs.readFileSync(fp, 'utf8');
  
  // Skip if already has FAQPage schema
  if (html.includes('"FAQPage"')) continue;
  
  // Find Q&A patterns: h2/h3 that look like questions followed by paragraphs
  const qaPairs = [];
  
  // Pattern 1: h2/h3 ending with ?
  const questionRegex = /<h[23][^>]*>([^<]*\?)<\/h[23]>/gi;
  let match;
  while ((match = questionRegex.exec(html)) !== null) {
    const question = match[1].replace(/<[^>]+>/g, '').trim();
    // Get the next paragraph as the answer
    const afterQ = html.slice(match.index + match[0].length, match.index + match[0].length + 2000);
    const pMatch = afterQ.match(/<p[^>]*>([\s\S]*?)<\/p>/i);
    if (pMatch) {
      const answer = pMatch[1].replace(/<[^>]+>/g, '').replace(/\s+/g, ' ').trim();
      if (answer.length > 30 && question.length > 15) {
        qaPairs.push({ question, answer: answer.slice(0, 300) });
      }
    }
  }
  
  if (qaPairs.length < 3) continue;
  
  // Build FAQ schema
  const faqSchema = {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    "mainEntity": qaPairs.slice(0, 8).map(qa => ({
      "@type": "Question",
      "name": qa.question,
      "acceptedAnswer": {
        "@type": "Answer",
        "text": qa.answer
      }
    }))
  };
  
  const schemaTag = '<script type="application/ld+json">\n' + JSON.stringify(faqSchema, null, 2) + '\n</script>';
  
  // Insert before </head>
  const headEnd = html.indexOf('</head>');
  if (headEnd > 0) {
    html = html.slice(0, headEnd) + schemaTag + '\n' + html.slice(headEnd);
    fs.writeFileSync(fp, html);
    modified++;
  }
}

console.log('FAQ schema: ' + modified + ' posts updated');
