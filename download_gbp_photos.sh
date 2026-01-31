#!/bin/bash
cd /Users/jarvis/clawd/scws-website/images/gbp-photos

# AF1Qip format photos (17 total)
AF1_IDS=(
  "AF1QipPT5RPBamGRjmRi0xemL2VOSd2pS4qiej75tCU"
  "AF1QipNyNQ2eiJzutAyJ-kq4hpEI5w4T9-y5HALUUuma"
  "AF1QipPBoBaJ9OlZ8S-Ldk6vC-VG8Fj_0Jeez2_eHgM"
  "AF1QipO6GaZ8lOgvVeVxqSBG-mm8nE_SGIhlZT7SP9E"
  "AF1QipMcYSTyQWBns2fp4xnN5kt2Qq3rs6mQ9t21PXM"
  "AF1QipNIHPq4G1YGnrtj9WXBMoQegS8i66dWvqigh2M"
  "AF1QipM645u8u15odWfeGLL3DHq56dBFhClr_TMoraA"
  "AF1QipP1jPH9v5PSAKgSZqnrK07ANg-mvPvrWQVHcv8"
  "AF1QipMYipX0VeQg6REv7b8Q5TaTiU22llIUSBfRzp8"
  "AF1QipOXksBIHkQ9lG2iZ5xoZRCjpBnHBk7cRQuMwC4"
  "AF1QipMNI3yukYDedbszRBwjuBqSM03X1ChVJpcrcxI"
  "AF1QipN0BnxspbCoJCJA3v4PEWll4yCemEX-T1TH1pU"
  "AF1QipORsZQ319fBi7dZwKpiiNrHJuo8JRuGyWzezv4"
  "AF1QipNZU45mnWpAjJl5JfAI-dxLYvpbr14xjtQk3DU"
  "AF1QipPAILvslicUqSxe8GmczIuarUkd2gSZSXyuS54"
  "AF1QipPmvm7UYAXzbd8O6-JEgVbwUQnJSnzmRbEaudQ"
  "AF1QipNNhmeUNbFR_Ln5HN8EWD7OVhljFoBjTywpWdM"
)

# AHVAwe format photos (gps-cs-s) (3 total)
GPS_IDS=(
  "AHVAweprTTd4zJrxwzBqkKAMv5CREu8z7BZyGxUN5DXpzS9hf01LGuJmE2E1TdsZOKHN2v52GTCvnttCWL0zDAqqz0EA5GQZL6PX_SYUHfP-TQBBhCA3apyxA5ml67L29p6tfvGwB1c"
  "AHVAweoZVB0hy6hd__CTqMvFD1FiREMwT2FzAhx7-KJvsO0bINeNYKCB21x5aVIpcoet_ZKc3ml5dabOV4xB7c1vJjZ3_8pyeZyAA4Wsuy60HoatL8hlB2SWP-Jmaq4GkORxS8ikfxoXdA"
  "AHVAwepPQp13Nm9SR1l6V-W0ZozkTb5F2NyLi_DDqF_fZM3jBd6wGEkk62hVf5H1s4Xhl2NgaFBR-ojndZH4NawwVi9hgiFoGwjNkgAICyrJy5MQ7rPoxLOIa5GcjaxV5NneeyNlKasc"
)

echo "Downloading 20 GBP photos..."

# Download AF1Qip photos
i=1
for id in "${AF1_IDS[@]}"; do
  printf "Downloading photo %02d (AF1Qip)..." "$i"
  curl -s "https://lh3.googleusercontent.com/p/${id}=s2048" -o "gbp-$(printf '%02d' $i).jpg"
  size=$(stat -f%z "gbp-$(printf '%02d' $i).jpg" 2>/dev/null || stat --printf="%s" "gbp-$(printf '%02d' $i).jpg")
  echo " ${size} bytes"
  ((i++))
done

# Download GPS-CS-S photos
for id in "${GPS_IDS[@]}"; do
  printf "Downloading photo %02d (gps-cs-s)..." "$i"
  curl -s "https://lh3.googleusercontent.com/gps-cs-s/${id}=s2048" -o "gbp-$(printf '%02d' $i).jpg"
  size=$(stat -f%z "gbp-$(printf '%02d' $i).jpg" 2>/dev/null || stat --printf="%s" "gbp-$(printf '%02d' $i).jpg")
  echo " ${size} bytes"
  ((i++))
done

echo ""
echo "Done! Downloaded $((i-1)) photos to:"
pwd
ls -la *.jpg 2>/dev/null | head -25
