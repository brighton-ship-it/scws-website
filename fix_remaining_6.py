#!/usr/bin/env python3
"""Fix the remaining 6 files that had no insertion point."""

import re
from pathlib import Path

files_to_fix = [
    'blog/well-drilling-cost-calculator.html',
    'blog/well-drilling-financing-options.html',
    'blog/well-drilling-forest-falls.html',
    'blog/well-drilling-french-valley.html',
    'blog/well-service-loma-linda.html',
    'blog/well-service-mount-woodson.html',
]

def get_related_section(filename: str) -> str:
    """Generate appropriate related articles section based on filename."""
    
    # All these are either drilling or service pages
    if 'cost-calculator' in filename:
        return '''
<!-- Related Articles -->
<section class="py-16 bg-gray-50">
    <div class="max-w-4xl mx-auto px-4">
        <div class="text-center mb-10">
            <h2 id="related-articles" class="text-3xl font-bold text-primary mb-2">Related Articles</h2>
            <p class="text-gray-600">Continue learning about well maintenance and troubleshooting</p>
        </div>
        <div class="grid md:grid-cols-3 gap-6">
            <a href="well-drilling-cost-per-foot.html" class="group bg-white rounded-xl shadow-md hover:shadow-xl transition overflow-hidden">
                <div class="h-40 overflow-hidden">
                    <img width="800" height="600" loading="lazy" src="/assets/images/article-categories/cost-guide.png" alt="Well Drilling Cost Per Foot: Regional Price Guide" class="w-full h-full object-cover group-hover:scale-105 transition duration-300">
                </div>
                <div class="p-5">
                    <span class="text-xs font-semibold text-amber-600 uppercase tracking-wide">Cost Guide</span>
                    <h3 class="font-bold text-lg text-primary mt-1 mb-2 group-hover:text-accent transition">Well Drilling Cost Per Foot: Regional Price Guide</h3>
                    <p class="text-gray-600 text-sm">What to expect for drilling costs</p>
                </div>
            </a>
            <a href="water-well-cost.html" class="group bg-white rounded-xl shadow-md hover:shadow-xl transition overflow-hidden">
                <div class="h-40 overflow-hidden">
                    <img width="800" height="600" loading="lazy" src="/assets/images/article-categories/cost-guide.png" alt="Water Well Cost: Complete Installation Price Guide" class="w-full h-full object-cover group-hover:scale-105 transition duration-300">
                </div>
                <div class="p-5">
                    <span class="text-xs font-semibold text-amber-600 uppercase tracking-wide">Cost Guide</span>
                    <h3 class="font-bold text-lg text-primary mt-1 mb-2 group-hover:text-accent transition">Water Well Cost: Complete Installation Price Guide</h3>
                    <p class="text-gray-600 text-sm">Total cost of new well installation</p>
                </div>
            </a>
            <a href="san-diego-county-well-permit-process.html" class="group bg-white rounded-xl shadow-md hover:shadow-xl transition overflow-hidden">
                <div class="h-40 overflow-hidden">
                    <img width="800" height="600" loading="lazy" src="/assets/images/article-categories/drilling.png" alt="San Diego County Well Permit Process Guide" class="w-full h-full object-cover group-hover:scale-105 transition duration-300">
                </div>
                <div class="p-5">
                    <span class="text-xs font-semibold text-accent uppercase tracking-wide">Drilling</span>
                    <h3 class="font-bold text-lg text-primary mt-1 mb-2 group-hover:text-accent transition">San Diego County Well Permit Process Guide</h3>
                    <p class="text-gray-600 text-sm">Navigate the permit process successfully</p>
                </div>
            </a>
        </div>
    </div>
</section>
'''
    elif 'financing' in filename:
        return '''
<!-- Related Articles -->
<section class="py-16 bg-gray-50">
    <div class="max-w-4xl mx-auto px-4">
        <div class="text-center mb-10">
            <h2 id="related-articles" class="text-3xl font-bold text-primary mb-2">Related Articles</h2>
            <p class="text-gray-600">Continue learning about well maintenance and troubleshooting</p>
        </div>
        <div class="grid md:grid-cols-3 gap-6">
            <a href="well-drilling-cost-calculator.html" class="group bg-white rounded-xl shadow-md hover:shadow-xl transition overflow-hidden">
                <div class="h-40 overflow-hidden">
                    <img width="800" height="600" loading="lazy" src="/assets/images/article-categories/cost-guide.png" alt="Well Drilling Cost Calculator: Get Accurate Estimates" class="w-full h-full object-cover group-hover:scale-105 transition duration-300">
                </div>
                <div class="p-5">
                    <span class="text-xs font-semibold text-amber-600 uppercase tracking-wide">Cost Guide</span>
                    <h3 class="font-bold text-lg text-primary mt-1 mb-2 group-hover:text-accent transition">Well Drilling Cost Calculator: Get Accurate Estimates</h3>
                    <p class="text-gray-600 text-sm">Calculate your well drilling costs</p>
                </div>
            </a>
            <a href="water-well-cost.html" class="group bg-white rounded-xl shadow-md hover:shadow-xl transition overflow-hidden">
                <div class="h-40 overflow-hidden">
                    <img width="800" height="600" loading="lazy" src="/assets/images/article-categories/cost-guide.png" alt="Water Well Cost: Complete Installation Price Guide" class="w-full h-full object-cover group-hover:scale-105 transition duration-300">
                </div>
                <div class="p-5">
                    <span class="text-xs font-semibold text-amber-600 uppercase tracking-wide">Cost Guide</span>
                    <h3 class="font-bold text-lg text-primary mt-1 mb-2 group-hover:text-accent transition">Water Well Cost: Complete Installation Price Guide</h3>
                    <p class="text-gray-600 text-sm">Total cost of new well installation</p>
                </div>
            </a>
            <a href="well-drilling-timeline.html" class="group bg-white rounded-xl shadow-md hover:shadow-xl transition overflow-hidden">
                <div class="h-40 overflow-hidden">
                    <img width="800" height="600" loading="lazy" src="/assets/images/article-categories/drilling.png" alt="Well Drilling Timeline: What to Expect" class="w-full h-full object-cover group-hover:scale-105 transition duration-300">
                </div>
                <div class="p-5">
                    <span class="text-xs font-semibold text-accent uppercase tracking-wide">Drilling</span>
                    <h3 class="font-bold text-lg text-primary mt-1 mb-2 group-hover:text-accent transition">Well Drilling Timeline: What to Expect</h3>
                    <p class="text-gray-600 text-sm">Understand the drilling process and timeframe</p>
                </div>
            </a>
        </div>
    </div>
</section>
'''
    elif 'drilling' in filename:
        # City-specific drilling pages
        return '''
<!-- Related Articles -->
<section class="py-16 bg-gray-50">
    <div class="max-w-4xl mx-auto px-4">
        <div class="text-center mb-10">
            <h2 id="related-articles" class="text-3xl font-bold text-primary mb-2">Related Articles</h2>
            <p class="text-gray-600">Continue learning about well maintenance and troubleshooting</p>
        </div>
        <div class="grid md:grid-cols-3 gap-6">
            <a href="well-drilling-cost-calculator.html" class="group bg-white rounded-xl shadow-md hover:shadow-xl transition overflow-hidden">
                <div class="h-40 overflow-hidden">
                    <img width="800" height="600" loading="lazy" src="/assets/images/article-categories/cost-guide.png" alt="Well Drilling Cost Calculator: Get Accurate Estimates" class="w-full h-full object-cover group-hover:scale-105 transition duration-300">
                </div>
                <div class="p-5">
                    <span class="text-xs font-semibold text-amber-600 uppercase tracking-wide">Cost Guide</span>
                    <h3 class="font-bold text-lg text-primary mt-1 mb-2 group-hover:text-accent transition">Well Drilling Cost Calculator: Get Accurate Estimates</h3>
                    <p class="text-gray-600 text-sm">Calculate your well drilling costs</p>
                </div>
            </a>
            <a href="san-diego-county-well-permit-process.html" class="group bg-white rounded-xl shadow-md hover:shadow-xl transition overflow-hidden">
                <div class="h-40 overflow-hidden">
                    <img width="800" height="600" loading="lazy" src="/assets/images/article-categories/drilling.png" alt="San Diego County Well Permit Process Guide" class="w-full h-full object-cover group-hover:scale-105 transition duration-300">
                </div>
                <div class="p-5">
                    <span class="text-xs font-semibold text-accent uppercase tracking-wide">Drilling</span>
                    <h3 class="font-bold text-lg text-primary mt-1 mb-2 group-hover:text-accent transition">San Diego County Well Permit Process Guide</h3>
                    <p class="text-gray-600 text-sm">Navigate the permit process successfully</p>
                </div>
            </a>
            <a href="well-maintenance-schedule.html" class="group bg-white rounded-xl shadow-md hover:shadow-xl transition overflow-hidden">
                <div class="h-40 overflow-hidden">
                    <img width="800" height="600" loading="lazy" src="/assets/images/article-categories/maintenance.png" alt="Well Maintenance Schedule: Year-Round Guide" class="w-full h-full object-cover group-hover:scale-105 transition duration-300">
                </div>
                <div class="p-5">
                    <span class="text-xs font-semibold text-accent uppercase tracking-wide">Maintenance</span>
                    <h3 class="font-bold text-lg text-primary mt-1 mb-2 group-hover:text-accent transition">Well Maintenance Schedule: Year-Round Guide</h3>
                    <p class="text-gray-600 text-sm">Complete maintenance calendar for well owners</p>
                </div>
            </a>
        </div>
    </div>
</section>
'''
    else:
        # Service pages
        return '''
<!-- Related Articles -->
<section class="py-16 bg-gray-50">
    <div class="max-w-4xl mx-auto px-4">
        <div class="text-center mb-10">
            <h2 id="related-articles" class="text-3xl font-bold text-primary mb-2">Related Articles</h2>
            <p class="text-gray-600">Continue learning about well maintenance and troubleshooting</p>
        </div>
        <div class="grid md:grid-cols-3 gap-6">
            <a href="well-pump-troubleshooting.html" class="group bg-white rounded-xl shadow-md hover:shadow-xl transition overflow-hidden">
                <div class="h-40 overflow-hidden">
                    <img width="800" height="600" loading="lazy" src="/assets/images/article-categories/troubleshooting.png" alt="Well Pump Troubleshooting: Complete Diagnostic Guide" class="w-full h-full object-cover group-hover:scale-105 transition duration-300">
                </div>
                <div class="p-5">
                    <span class="text-xs font-semibold text-accent uppercase tracking-wide">Troubleshooting</span>
                    <h3 class="font-bold text-lg text-primary mt-1 mb-2 group-hover:text-accent transition">Well Pump Troubleshooting: Complete Diagnostic Guide</h3>
                    <p class="text-gray-600 text-sm">Systematic approach to identifying pump problems</p>
                </div>
            </a>
            <a href="well-pump-repair.html" class="group bg-white rounded-xl shadow-md hover:shadow-xl transition overflow-hidden">
                <div class="h-40 overflow-hidden">
                    <img width="800" height="600" loading="lazy" src="/assets/images/article-categories/troubleshooting.png" alt="Well Pump Repair Guide: Common Issues &amp; Solutions" class="w-full h-full object-cover group-hover:scale-105 transition duration-300">
                </div>
                <div class="p-5">
                    <span class="text-xs font-semibold text-accent uppercase tracking-wide">Troubleshooting</span>
                    <h3 class="font-bold text-lg text-primary mt-1 mb-2 group-hover:text-accent transition">Well Pump Repair Guide: Common Issues & Solutions</h3>
                    <p class="text-gray-600 text-sm">Complete guide to diagnosing and repairing well pumps</p>
                </div>
            </a>
            <a href="well-maintenance-schedule.html" class="group bg-white rounded-xl shadow-md hover:shadow-xl transition overflow-hidden">
                <div class="h-40 overflow-hidden">
                    <img width="800" height="600" loading="lazy" src="/assets/images/article-categories/maintenance.png" alt="Well Maintenance Schedule: Year-Round Guide" class="w-full h-full object-cover group-hover:scale-105 transition duration-300">
                </div>
                <div class="p-5">
                    <span class="text-xs font-semibold text-accent uppercase tracking-wide">Maintenance</span>
                    <h3 class="font-bold text-lg text-primary mt-1 mb-2 group-hover:text-accent transition">Well Maintenance Schedule: Year-Round Guide</h3>
                    <p class="text-gray-600 text-sm">Complete maintenance calendar for well owners</p>
                </div>
            </a>
        </div>
    </div>
</section>
'''

for filepath in files_to_fix:
    path = Path(filepath)
    print(f"Processing {path.name}...")
    
    content = path.read_text(encoding='utf-8')
    
    # Find the chat widget script tag
    match = re.search(r'<script>setTimeout.*?chat-widget\.js.*?</script>', content, re.DOTALL)
    
    if match:
        insert_pos = match.start()
        section = get_related_section(path.name)
        new_content = content[:insert_pos] + section + '\n' + content[insert_pos:]
        path.write_text(new_content, encoding='utf-8')
        print(f"  ✅ Added Related Articles section")
    else:
        print(f"  ⚠️  Could not find insertion point")

print("\n🎉 Done! Committing changes...")
