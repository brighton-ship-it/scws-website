#!/bin/bash
# Fix common "current year" patterns
find ./blog -name "*.html" -exec sed -i '' \
  -e 's/Best Well Pump Brands 2025/Best Well Pump Brands 2026/g' \
  -e 's/2025 Guide/2026 Guide/g' \
  -e 's/Guide 2025/Guide 2026/g' \
  -e 's/2025 Price/2026 Price/g' \
  -e 's/Price 2025/Price 2026/g' \
  -e 's/2025 Cost/2026 Cost/g' \
  -e 's/Cost 2025/Cost 2026/g' \
  -e 's/2020-2025/2021-2026/g' \
  -e 's/Permit Types (2025)/Permit Types (2026)/g' \
  -e 's/2025 Permits/2026 Permits/g' \
  -e 's/permits in 2025/permits in 2026/g' \
  {} \;
echo "Done"
