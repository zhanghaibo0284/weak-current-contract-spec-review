#!/usr/bin/env bash
# weak-current-contract-spec-review installer (macOS / Linux)
# Usage:
#   ./install.sh
#   ./install.sh --target trae
#   ./install.sh --target claude --force

set -euo pipefail

SKILL_NAME="weak-current-contract-spec-review"
TARGET="auto"
FORCE=0

while [ $# -gt 0 ]; do
    case "$1" in
        --target)
            TARGET="${2:-}"
            shift 2
            ;;
        --force)
            FORCE=1
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [--target auto|claude|trae] [--force]"
            exit 0
            ;;
        *)
            echo "Unknown option: $1" >&2
            exit 2
            ;;
    esac
done

SOURCE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EXPECTED_CHECKSUM=""
if [ -f "$SOURCE/CHECKSUM.txt" ]; then
    EXPECTED_CHECKSUM="$(head -n 1 "$SOURCE/CHECKSUM.txt" | tr -d '\r')"
fi

if [ ! -f "$SOURCE/SKILL.md" ]; then
    echo "SKILL.md not found in $SOURCE. Run this script from the repository root." >&2
    exit 1
fi

if [ "$TARGET" = "auto" ]; then
    if [ -d "$HOME/.claude" ]; then
        TARGET="claude"
    elif [ -d "$HOME/.trae-cn" ]; then
        TARGET="trae"
    else
        echo "No platform detected. Specify --target claude or --target trae." >&2
        exit 1
    fi
fi

case "$TARGET" in
    claude) SKILLS_ROOT="$HOME/.claude/skills" ;;
    trae)   SKILLS_ROOT="$HOME/.trae-cn/skills" ;;
    *)
        echo "Invalid target: $TARGET" >&2
        exit 2
        ;;
esac

DEST="$SKILLS_ROOT/$SKILL_NAME"
mkdir -p "$SKILLS_ROOT"

if [ -e "$DEST" ]; then
    if [ "$FORCE" -eq 1 ]; then
        rm -rf "$DEST"
        echo "Removed existing: $DEST"
    else
        BACKUP="$DEST.bak-$(date +%Y%m%d-%H%M%S)"
        mv "$DEST" "$BACKUP"
        echo "Backup created: $BACKUP"
    fi
fi

mkdir -p "$DEST"

if command -v rsync >/dev/null 2>&1; then
    rsync -a --exclude '.git' --exclude '.screenshots' --exclude '__pycache__' "$SOURCE/" "$DEST/"
else
    (cd "$SOURCE" && tar --exclude='.git' --exclude='.screenshots' --exclude='__pycache__' -cf - .) | (cd "$DEST" && tar -xf -)
fi

COUNT="$(find "$DEST" -type f | wc -l | tr -d ' ')"
echo "Installed to: $DEST"
echo "Files copied: $COUNT"

PYTHON=""
if command -v python3 >/dev/null 2>&1; then
    PYTHON="python3"
elif command -v python >/dev/null 2>&1; then
    PYTHON="python"
fi

if [ -n "$PYTHON" ]; then
    (cd "$DEST" && "$PYTHON" verify_skill.py) || echo "WARNING: verify_skill.py reported issues" >&2
    CHECKSUM="$(cd "$DEST" && "$PYTHON" verify_skill.py --checksum | tr -d '\r')"
    echo "Checksum: $CHECKSUM"
    if [ -z "$EXPECTED_CHECKSUM" ]; then
        echo "No CHECKSUM.txt found. Skipped checksum comparison."
    else
        case "$CHECKSUM" in
            *"$EXPECTED_CHECKSUM"*) echo "Checksum OK" ;;
            *) echo "WARNING: checksum mismatch, the rules may have been modified." >&2 ;;
        esac
    fi
else
    echo "Python not found. Skipped structure verification."
fi

echo "Done. Restart Claude Code / Trae to load the skill."
