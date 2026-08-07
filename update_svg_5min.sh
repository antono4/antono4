#!/bin/bash
# Script untuk memperbarui contrib-3d.svg setiap 5 menit
#============================================

REPO="antono4/antono4"
BRANCH="main"
SVG_PATH="assets/contrib-3d.svg"
WORK_DIR="/workspace/project"
INTERVAL=300  # 5 menit

# Setup git
cd "$WORK_DIR"
git config --local user.name "GitHub Actions Bot"
git config --local user.email "github-actions[bot]@users.noreply.github.com"

echo "🔄 Memperbarui contrib-3d.svg setiap 5 menit..."
echo "📍 Repo: $REPO"
echo "📍 Branch: $BRANCH"
echo "============================================"

# Loop forever
count=0
while true; do
    count=$((count + 1))
    TIMESTAMP=$(date -u +"%Y-%m-%d %H:%M:%S UTC")
    
    echo "[$count] $TIMESTAMP - Mengunduh SVG terbaru..."
    
    # Download SVG terbaru dari GitHub raw
    curl -sL "https://raw.githubusercontent.com/$REPO/$BRANCH/$SVG_PATH" -o "$WORK_DIR/$SVG_PATH"
    
    if [ $? -eq 0 ]; then
        echo "[$count] ✓ Download berhasil, ukuran: $(wc -c < "$WORK_DIR/$SVG_PATH") bytes"
        
        # Commit dan push perubahan
        git add "$SVG_PATH"
        if git diff --staged --quiet; then
            echo "[$count] Tidak ada perubahan"
        else
            git commit -m "chore: update contrib-3d.svg [$TIMESTAMP] [skip ci]" --allow-empty
            git push
            echo "[$count] ✓ Berhasil di-push!"
        fi
    else
        echo "[$count] ✗ Gagal mengunduh"
    fi
    
    echo "---"
    sleep "$INTERVAL"
done
