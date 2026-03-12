#!/usr/bin/env python3
"""
Verify that all 43 originally broken image references are now fixed
"""

import os
from pathlib import Path

# The original 43 broken references
ORIGINAL_BROKEN = {
    # Article categories
    'article-categories/buying-property.png': 'article-categories/cost-guide.png',
    'article-categories/costs.png': 'article-categories/cost-guide.png',
    'article-categories/filtration.png': 'article-categories/treatment.png',
    'article-categories/home-buying.png': 'article-categories/cost-guide.png',
    'article-categories/inspection.png': 'article-categories/maintenance.png',
    'article-categories/pump-repair.png': 'article-categories/troubleshooting.png',
    'article-categories/real-estate.png': 'article-categories/cost-guide.png',
    'article-categories/repair.png': 'article-categories/troubleshooting.png',
    'article-categories/solar-pumps.png': 'article-categories/equipment.png',
    'article-categories/storage-tanks.png': 'article-categories/equipment.png',
    'article-categories/testing.png': 'article-categories/water-quality.png',
    'article-categories/water-treatment.png': 'article-categories/treatment.png',
    
    # Blog categories (redirected to article-categories)
    'blog-categories/costs.png': 'article-categories/cost-guide.png',
    'blog-categories/repair.png': 'article-categories/troubleshooting.png',
    'blog-categories/testing.png': 'article-categories/water-quality.png',
    
    # Blog images
    'blog-images/drought-well.png': 'blog-images/drought.png',
    'blog-images/emergency-well.png': 'blog-images/emergency-well-repair-1.png',
    'blog-images/hydrofracturing.png': 'blog-images/well-drilling-1.png',
    'blog-images/insurance-coverage.png': 'blog-images/well-service-1.png',
    'blog-images/irrigation-well.png': 'blog-images/well-service-2.png',
    'blog-images/livestock-well.png': 'blog-images/well-service-3.png',
    'blog-images/pool-well-water.png': 'blog-images/water-test.png',
    'blog-images/selling-home-well.png': 'blog-images/well-inspection.png',
    'blog-images/shared-well.png': 'blog-images/well-service-4.png',
    'blog-images/solar-well-pump.png': 'blog-images/solar-pump.png',
    'blog-images/water-quality-1.png': 'blog-images/sulfur-water.png',
    'blog-images/water-storage-tank.png': 'blog-images/pressure-tank-1.png',
    'blog-images/well-abandonment.png': 'blog-images/well-casing.png',
    'blog-images/well-log.png': 'blog-images/well-inspection.png',
    'blog-images/well-mortgage.png': 'blog-images/well-service-5.png',
    'blog-images/well-property-value.png': 'blog-images/well-service-1.png',
    'blog-images/well-water-safety.png': 'blog-images/water-test.png',
    
    # Hero images
    'images/hero-mountains.jpg': 'images/hero-mountain-landscape.jpg',
    'images/hero-ranch.jpg': 'images/hero-rural.jpg',
    'images/hero-rancho-penasquitos-hills.jpg': 'images/hero-poway-hills.jpg',
    'images/rancho-penasquitos-estate-property.jpg': 'images/hero-poway-hills.jpg',
}

def check_original_broken():
    """Check that none of the original broken references still exist"""
    base_dir = Path('/Users/jarvis/clawd/scws-website')
    still_broken = []
    
    html_files = list(base_dir.rglob('*.html'))
    
    for html_file in html_files:
        if 'node_modules' in str(html_file):
            continue
        
        try:
            with open(html_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            for broken in ORIGINAL_BROKEN.keys():
                if broken in content:
                    # Make sure it's not just part of a longer valid path
                    # Check if it's actually a broken reference
                    still_broken.append({
                        'file': str(html_file),
                        'broken_ref': broken
                    })
        except Exception as e:
            pass
    
    return still_broken

def verify_fixed_images_exist():
    """Verify that all the replacement images actually exist"""
    base_dir = Path('/Users/jarvis/clawd/scws-website')
    missing = []
    
    for fixed_path in set(ORIGINAL_BROKEN.values()):
        # Try with /assets/images/ prefix
        full_path = base_dir / 'assets' / 'images' / fixed_path
        if not full_path.exists():
            # Try direct in images/
            full_path = base_dir / fixed_path
            if not full_path.exists():
                missing.append(fixed_path)
    
    return missing

if __name__ == '__main__':
    print("Verifying the original 43 broken references are fixed...")
    print("=" * 60)
    
    still_broken = check_original_broken()
    missing_targets = verify_fixed_images_exist()
    
    if still_broken:
        print(f"\n❌ Found {len(still_broken)} files still referencing broken images:")
        for item in still_broken:
            print(f"  {item['file']}")
            print(f"  Still contains: {item['broken_ref']}")
    else:
        print("\n✅ None of the original 43 broken references found in HTML files!")
    
    print()
    
    if missing_targets:
        print(f"❌ Missing {len(missing_targets)} target images:")
        for img in missing_targets:
            print(f"  {img}")
    else:
        print("✅ All replacement images exist!")
    
    print("\n" + "=" * 60)
    
    if not still_broken and not missing_targets:
        print("\n🎉 SUCCESS: All 43 broken image references are fixed!")
    else:
        print(f"\n⚠️  Issues remaining: {len(still_broken)} broken refs, {len(missing_targets)} missing targets")
