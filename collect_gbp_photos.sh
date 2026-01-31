#!/bin/bash
# Collected GBP photo IDs - will add more as we click through
# Format: https://lh3.googleusercontent.com/p/{ID}=s2048 for full size

# Initial photos found
PHOTO_IDS=(
  "AF1QipPT5RPBamGRjmRi0xemL2VOSd2pS4qiej75tCU"
  "AF1QipNyNQ2eiJzutAyJ-kq4hpEI5w4T9-y5HALUUuma"
)

# gps-cs-s photos (different URL pattern)
GPS_PHOTO_IDS=(
  "AHVAweprTTd4zJrxwzBqkKAMv5CREu8z7BZyGxUN5DXpzS9hf01LGuJmE2E1TdsZOKHN2v52GTCvnttCWL0zDAqqz0EA5GQZL6PX_SYUHfP-TQBBhCA3apyxA5ml67L29p6tfvGwB1c"
  "AHVAweoZVB0hy6hd__CTqMvFD1FiREMwT2FzAhx7-KJvsO0bINeNYKCB21x5aVIpcoet_ZKc3ml5dabOV4xB7c1vJjZ3_8pyeZyAA4Wsuy60HoatL8hlB2SWP-Jmaq4GkORxS8ikfxoXdA"
  "AHVAwepPQp13Nm9SR1l6V-W0ZozkTb5F2NyLi_DDqF_fZM3jBd6wGEkk62hVf5H1s4Xhl2NgaFBR-ojndZH4NawwVi9hgiFoGwjNkgAICyrJy5MQ7rPoxLOIa5GcjaxV5NneeyNlKasc"
)

cd /Users/jarvis/clawd/scws-website/images/gbp-photos

# Download regular photos
i=1
for id in "${PHOTO_IDS[@]}"; do
  echo "Downloading photo $i..."
  curl -s "https://lh3.googleusercontent.com/p/${id}=s2048" -o "gbp-photo-${i}.jpg"
  ((i++))
done

# Download gps-cs-s photos
for id in "${GPS_PHOTO_IDS[@]}"; do
  echo "Downloading photo $i..."
  curl -s "https://lh3.googleusercontent.com/gps-cs-s/${id}=s2048" -o "gbp-photo-${i}.jpg"
  ((i++))
done

echo "Done! Downloaded $((i-1)) photos"
