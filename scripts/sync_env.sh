#!/bin/bash
# Sync local .env files with their templates.
#
# For each template/target pair, finds KEY=value lines present in the template
# whose key is missing from the target, and (after explicit confirmation) appends
# only those missing keys. Existing values are never overwritten or removed.
#
# Usage:
#   scripts/sync_env.sh <template> <target> [<template> <target> ...]
#
# Behaviour:
#   - By default it shows the missing keys and prompts before writing; nothing is
#     changed unless you answer "y".
#   - Set SKIP_ENV_SYNC=1 (or run without an interactive terminal, e.g. CI) to
#     only report the missing keys without touching any file.
#   - If a target file does not exist it is created from its template (no prompt);
#     the confirmation only applies to syncing keys into a file that exists.

set -euo pipefail

# Colour the diff green when writing to a terminal and NO_COLOR is unset.
if [ -t 1 ] && [ -z "${NO_COLOR:-}" ]; then
    GREEN=$'\033[32m'
    RESET=$'\033[0m'
else
    GREEN=""
    RESET=""
fi

if [ "$#" -lt 2 ] || [ $(($# % 2)) -ne 0 ]; then
    echo "Usage: $0 <template> <target> [<template> <target> ...]" >&2
    exit 1
fi

missing_keys_lines() {
    local template="$1" target="$2"
    while IFS= read -r line || [ -n "$line" ]; do
        case "$line" in
            ''|\#*) continue ;;
            *=*) ;;
            *) continue ;;
        esac
        local key="${line%%=*}"
        key="${key#export }"
        # Escape regex metacharacters so keys like MY.KEY or KEY[1] match literally.
        local key_re
        key_re=$(printf '%s' "$key" | sed 's/[][\\.^$*+?(){}|]/\\&/g')
        if ! grep -qE "^(export )?${key_re}=" "$target"; then
            printf '%s\n' "$line"
        fi
    done < "$template"
}

append_lines() {
    local target="$1" line
    # Insert a newline first if the target doesn't end in one, to avoid gluing.
    if [ -s "$target" ] && [ -n "$(tail -c 1 "$target")" ]; then
        echo "" >> "$target"
    fi
    while IFS= read -r line; do
        printf '%s\n' "$line" >> "$target"
    done
}

while [ "$#" -gt 0 ]; do
    template="$1"
    target="$2"
    shift 2

    if [ ! -f "$template" ]; then
        echo "  ! template $template not found, skipping"
        continue
    fi
    if [ ! -f "$target" ]; then
        cp "$template" "$target"
        echo "  created $target from $template"
        continue
    fi

    missing="$(missing_keys_lines "$template" "$target")"

    if [ -z "$missing" ]; then
        echo "  $target already up to date with $template"
        continue
    fi

    echo "  $target is missing the following from $template:"
    while IFS= read -r line; do
        echo "    ${GREEN}+ ${line}${RESET}"
    done <<< "$missing"

    if [ "${SKIP_ENV_SYNC:-0}" = "1" ] || [ ! -t 0 ]; then
        echo "    (reporting only — run interactively without SKIP_ENV_SYNC to apply)"
        continue
    fi

    printf "  Add these to %s? [y/N] " "$target"
    read -r reply
    case "$reply" in
        y|Y)
            append_lines "$target" <<< "$missing"
            echo "    updated $target"
            ;;
        *)
            echo "    skipped $target (no changes made)"
            ;;
    esac
done

exit 0
