#!/usr/bin/env python3
"""Generate unique AI images for each blog article category."""

import os
import requests
import base64
from openai import OpenAI

client = OpenAI()
output_dir = "/Users/jarvis/clawd/scws-website/assets/images/article-categories"

categories = {
    "troubleshooting": "Professional photograph of a well service technician using diagnostic equipment to test a submersible well pump, tools laid out, pump house setting, realistic lighting, no text",
    
    "pressure-issues": "Professional photograph of a pressure gauge on a well water system showing pressure reading, blue pressure tank in background, residential pump house, realistic, no text",
    
    "maintenance": "Professional photograph of well technician performing annual maintenance on a well pump system, checking connections, clean professional work, realistic, no text",
    
    "emergency": "Dramatic photograph of an emergency well repair at dusk, service truck with lights on, technician working urgently, residential setting, realistic, no text",
    
    "water-quality": "Professional photograph of clear water being poured into a glass from a well faucet, water testing kit visible nearby, clean kitchen setting, realistic, no text",
    
    "cost-guide": "Professional photograph of a well service estimate clipboard with pen on a pressure tank, professional documentation, residential pump house, realistic, no text",
    
    "equipment": "Professional photograph of new submersible well pump and motor components laid out on a workbench, professional quality equipment, realistic, no text",
    
    "warning-signs": "Professional photograph of a well pressure tank with visible condensation and a flickering pressure gauge, subtle signs of issues, realistic lighting, no text",
    
    "treatment": "Professional photograph of a whole-house water treatment and filtration system installed next to a well pressure tank, clean installation, realistic, no text",
    
    "urgent": "Professional photograph of a well technician responding to an emergency call, arriving at a rural property with service van, golden hour lighting, realistic, no text"
}

for name, prompt in categories.items():
    output_path = os.path.join(output_dir, f"{name}.png")
    
    if os.path.exists(output_path):
        print(f"⏭️  Skipping {name} (already exists)")
        continue
    
    print(f"🎨 Generating {name}...")
    
    try:
        response = client.images.generate(
            model="gpt-image-1",
            prompt=prompt,
            n=1,
            size="1536x1024",
            quality="medium"
        )
        
        # Get image data
        image_url = response.data[0].url
        if response.data[0].b64_json:
            image_data = base64.b64decode(response.data[0].b64_json)
        else:
            image_data = requests.get(image_url).content
        
        with open(output_path, "wb") as f:
            f.write(image_data)
        
        print(f"✅ Saved {name}.png")
        
    except Exception as e:
        print(f"❌ Error generating {name}: {e}")

print("\n✅ Done generating article category images!")
