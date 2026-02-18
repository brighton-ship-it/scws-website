#!/usr/bin/env python3
"""
Generate AI images for SCWS blog posts.
Run with: python3 generate-blog-images.py
"""

import os
import subprocess
import json
import time
from pathlib import Path

# Output directory
OUTPUT_DIR = "/Users/jarvis/clawd/scws-website/assets/images/blog-images"
SKILL_SCRIPT = "/Users/jarvis/.npm-global/lib/node_modules/openclaw/skills/openai-image-gen/scripts/gen.py"

# Service type prompts (5 variations each)
SERVICE_PROMPTS = {
    "well-drilling": [
        "Photo-realistic image of a well drilling rig in action on rural California property, professional drill rig with crew, blue sky, dust and activity",
        "Photo-realistic image of well drilling equipment close-up, large drill bit penetrating earth, professional drilling operation",
        "Photo-realistic image of well drilling site with workers in safety gear, drilling rig on sandy California terrain, professional setup",
        "Photo-realistic image of completed well drilling with steel casing being installed, workers guiding pipe, professional operation",
        "Photo-realistic image of portable well drilling rig on hillside property, Southern California landscape, professional equipment",
    ],
    "well-pump-repair": [
        "Photo-realistic image of technician repairing submersible well pump, pump pulled from well, professional service",
        "Photo-realistic image of well pump diagnostic work, technician with multimeter testing pump motor, professional troubleshooting",
        "Photo-realistic image of well pump replacement, old pump next to new pump, technician working, professional service",
        "Photo-realistic image of pump control box repair, technician working on electrical panel, professional service call",
        "Photo-realistic image of well pump being lowered into well casing, technician guiding equipment, professional installation",
    ],
    "pressure-tank": [
        "Photo-realistic image of blue pressure tank installation in pump house, professional plumber connecting pipes",
        "Photo-realistic image of pressure tank replacement, old rusty tank next to new blue tank, professional service",
        "Photo-realistic image of technician checking pressure tank air pressure with gauge, professional maintenance",
        "Photo-realistic image of large commercial pressure tank system, multiple tanks in equipment room, professional setup",
        "Photo-realistic image of waterlogged pressure tank diagnosis, technician inspecting failed tank, professional service",
    ],
    "booster-pump": [
        "Photo-realistic image of booster pump installation for home, inline pump being connected to plumbing, professional work",
        "Photo-realistic image of commercial booster pump system, multiple pumps in mechanical room, professional installation",
        "Photo-realistic image of technician installing variable speed booster pump, modern pump equipment, professional service",
        "Photo-realistic image of booster pump and pressure tank setup, complete system installation, professional plumbing",
        "Photo-realistic image of irrigation booster pump installation, agricultural setting, professional farm service",
    ],
    "water-treatment": [
        "Photo-realistic image of whole house water filtration system installation, technician connecting filters, professional service",
        "Photo-realistic image of water softener system, salt tank and resin tank setup, professional installation",
        "Photo-realistic image of reverse osmosis system under kitchen sink, professional plumber installing",
        "Photo-realistic image of UV water treatment system installation, technician mounting UV unit, professional service",
        "Photo-realistic image of iron filter system for well water, large filtration tanks, professional installation",
    ],
    "well-service": [
        "Photo-realistic image of well service technician at wellhead, checking equipment, professional maintenance call",
        "Photo-realistic image of annual well inspection, technician with clipboard examining well components",
        "Photo-realistic image of well service truck at rural property, technician unloading equipment, professional service",
        "Photo-realistic image of well system check, technician monitoring pressure gauges, professional service call",
        "Photo-realistic image of well maintenance work, technician lubricating and checking well components, professional service",
    ],
    "well-rehabilitation": [
        "Photo-realistic image of well rehabilitation work, equipment lowered into old well, professional restoration service",
        "Photo-realistic image of well cleaning and development, surge equipment in use, professional rehabilitation",
        "Photo-realistic image of well video inspection, camera being lowered into well, professional diagnostic work",
        "Photo-realistic image of well acid treatment, technician handling rehabilitation chemicals safely, professional service",
        "Photo-realistic image of well yield testing after rehabilitation, flow measurement equipment, professional service",
    ],
    "well-abandonment": [
        "Photo-realistic image of well abandonment procedure, grout being pumped into old well, professional sealing work",
        "Photo-realistic image of old well being properly sealed, heavy equipment at site, professional abandonment service",
        "Photo-realistic image of well casing removal during abandonment, professional decommissioning work",
        "Photo-realistic image of well abandonment paperwork and inspection, official documentation process",
        "Photo-realistic image of sealed abandoned well site, properly capped and marked, professional completion",
    ],
    "emergency-well-repair": [
        "Photo-realistic dramatic image of emergency well repair at night, work lights illuminating site, urgent response",
        "Photo-realistic image of water gushing from broken well pipe, technician responding quickly, emergency service",
        "Photo-realistic image of emergency pump replacement, technician working urgently, service truck with lights",
        "Photo-realistic image of flooded pump house emergency, technician assessing water damage, urgent response",
        "Photo-realistic image of no water emergency response, worried homeowner with technician diagnosing problem",
    ],
}

# Content topic prompts
CONTENT_PROMPTS = {
    "water-quality-testing": "Photo-realistic image of water quality testing in laboratory, test tubes with water samples, scientific equipment",
    "iron-bacteria": "Photo-realistic image of orange/rust colored well water in glass, iron bacteria contamination visible",
    "hard-water": "Photo-realistic image of hard water scale buildup on faucet and pipes, mineral deposits",
    "sulfur-smell": "Photo-realistic image of well water with yellow tint, hydrogen sulfide treatment system",
    "arsenic": "Photo-realistic image of water testing for arsenic, lab analysis equipment, scientific testing",
    "bacteria-contamination": "Photo-realistic image of coliform bacteria water test kit, positive test result indication",
    "sediment-filter": "Photo-realistic image of sediment filter cartridge dirty vs clean comparison",
    "low-water-pressure": "Photo-realistic image of weak water stream from shower head, low pressure problem",
    "no-water": "Photo-realistic image of dry faucet with no water, homeowner concerned, emergency situation",
    "pump-cycling": "Photo-realistic image of pressure switch and gauge showing rapid cycling, diagnostic work",
    "pump-noise": "Photo-realistic image of noisy well pump vibrating, technician listening with stethoscope",
    "air-in-lines": "Photo-realistic image of sputtering faucet with air bubbles in water, plumbing problem",
    "frozen-pipes": "Photo-realistic image of frozen well pipes in winter, ice damage to plumbing",
    "well-depth": "Photo-realistic cross-section illustration of deep water well, aquifer layers visible",
    "aquifer": "Photo-realistic illustration of underground aquifer system, water table and well",
    "gpm-flow-rate": "Photo-realistic image of flow rate testing with bucket and timer, measuring gallons per minute",
    "well-permit": "Photo-realistic image of well permit documents and county inspection forms on desk",
    "well-inspection": "Photo-realistic image of well inspector examining wellhead, clipboard and checklist",
    "well-cost": "Photo-realistic image of well drilling estimate paperwork with calculator, cost planning",
    "diy-maintenance": "Photo-realistic image of homeowner checking well pressure tank, DIY maintenance",
    "winterization": "Photo-realistic image of well house being insulated for winter, freeze protection",
    "drought": "Photo-realistic image of dry cracked earth around well, drought conditions in California",
    "submersible-pump": "Photo-realistic close-up of submersible well pump out of well, stainless steel pump",
    "jet-pump": "Photo-realistic image of above-ground jet pump in pump house, professional installation",
    "variable-speed-pump": "Photo-realistic image of modern variable speed pump with controller, advanced technology",
    "solar-pump": "Photo-realistic image of solar-powered well pump system, panels and pump",
    "hand-pump": "Photo-realistic image of manual hand pump on old well, backup water source",
    "well-cap": "Photo-realistic close-up of sanitary well cap properly installed, weatherproof seal",
    "well-casing": "Photo-realistic image of steel well casing being installed, professional drilling",
    "pitless-adapter": "Photo-realistic image of pitless adapter installation below frost line",
    "check-valve": "Photo-realistic image of check valve installation in well line, foot valve",
    "pressure-switch": "Photo-realistic close-up of pressure switch adjustment, 40/60 settings",
    "electrical-panel": "Photo-realistic image of well pump electrical panel and breaker, professional wiring",
    "generator-backup": "Photo-realistic image of backup generator powering well pump during outage",
    "farm-irrigation": "Photo-realistic image of agricultural irrigation from well, sprinklers in field",
    "livestock-water": "Photo-realistic image of cattle drinking from well-supplied water trough",
    "orchard-irrigation": "Photo-realistic image of drip irrigation in orchard from well water",
    "pool-filling": "Photo-realistic image of swimming pool being filled with well water",
    "new-construction": "Photo-realistic image of new home construction with well being drilled on site",
    "real-estate": "Photo-realistic image of home inspection with well evaluation, real estate transaction",
    "shared-well": "Photo-realistic image of shared well system serving multiple homes, rural neighborhood",
    "statistics": "Photo-realistic image of water well data charts and graphs on computer screen",
    "california-map": "Photo-realistic satellite view of Southern California with groundwater basins highlighted",
    "san-diego-county": "Photo-realistic image of San Diego County rural landscape with well drilling rig",
    "riverside-county": "Photo-realistic image of Riverside County desert landscape with well site",
    "cost-comparison": "Photo-realistic image of cost comparison charts for well services on tablet",
    "brands-equipment": "Photo-realistic image of various well pump brands lined up, Franklin Grundfos Goulds",
    "tools": "Photo-realistic image of well service tools and equipment laid out professionally",
}

def generate_image(prompt: str, output_name: str) -> bool:
    """Generate a single image using the OpenAI skill script."""
    output_path = os.path.join(OUTPUT_DIR, f"{output_name}.png")
    
    if os.path.exists(output_path):
        print(f"  Skipping {output_name} (already exists)")
        return True
    
    cmd = [
        "python3", SKILL_SCRIPT,
        "--model", "gpt-image-1",
        "--quality", "high",
        "--size", "1536x1024",
        "--count", "1",
        "--out-dir", "/tmp/img-gen",
        "--prompt", prompt
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode == 0:
            # Move the generated image to our output directory with proper name
            import glob
            tmp_images = glob.glob("/tmp/img-gen/*.png")
            if tmp_images:
                os.rename(tmp_images[0], output_path)
                print(f"  ✓ Generated {output_name}")
                return True
        print(f"  ✗ Failed {output_name}: {result.stderr[:100]}")
        return False
    except subprocess.TimeoutExpired:
        print(f"  ✗ Timeout {output_name}")
        return False
    except Exception as e:
        print(f"  ✗ Error {output_name}: {e}")
        return False

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs("/tmp/img-gen", exist_ok=True)
    
    total = 0
    success = 0
    
    # Generate service type images
    print("\n=== Generating Service Type Images ===\n")
    for service_type, prompts in SERVICE_PROMPTS.items():
        print(f"\n{service_type}:")
        for i, prompt in enumerate(prompts, 1):
            total += 1
            name = f"{service_type}-{i}"
            if generate_image(prompt, name):
                success += 1
            time.sleep(2)  # Rate limiting
    
    # Generate content topic images
    print("\n=== Generating Content Topic Images ===\n")
    for topic, prompt in CONTENT_PROMPTS.items():
        total += 1
        if generate_image(prompt, topic):
            success += 1
        time.sleep(2)  # Rate limiting
    
    print(f"\n=== Complete: {success}/{total} images generated ===\n")
    
    # Save mapping file
    mapping = {
        "service_types": list(SERVICE_PROMPTS.keys()),
        "content_topics": list(CONTENT_PROMPTS.keys()),
        "total_images": total,
        "successful": success
    }
    with open(os.path.join(OUTPUT_DIR, "image-mapping.json"), "w") as f:
        json.dump(mapping, f, indent=2)

if __name__ == "__main__":
    main()
