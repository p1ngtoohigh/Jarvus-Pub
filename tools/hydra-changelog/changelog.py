#!/usr/bin/env python3
"""Generate a categorized Markdown changelog from commits since the latest tag."""
import argparse
from collections import defaultdict
from datetime import date
from pathlib import Path
import re
import subprocess

CATEGORIES = ('Added', 'Fixed', 'Changed', 'Removed')
TYPE_MAP = {'feat': 'Added', 'fix': 'Fixed', 'perf': 'Changed', 'refactor': 'Changed', 'docs': 'Changed', 'style': 'Changed', 'build': 'Changed', 'ci': 'Changed', 'test': 'Changed', 'chore': 'Changed', 'revert': 'Removed'}
CONVENTIONAL = re.compile(r'^(?P<type>[a-zA-Z]+)(?:\([^)]+\))?(?:!)?:\s*(?P<description>.+)$')

def git(*args, cwd=None):
    return subprocess.run(['git', *args], cwd=cwd, text=True, capture_output=True, check=True).stdout.strip()

def latest_tag(cwd=None):
    try:
        return git('describe', '--tags', '--abbrev=0', cwd=cwd)
    except subprocess.CalledProcessError:
        return None

def classify(subject):
    match = CONVENTIONAL.match(subject)
    if match:
        typ, desc = match.group('type').lower(), match.group('description')
        return TYPE_MAP.get(typ, 'Changed'), desc
    lower = subject.lower()
    if re.search(r'\b(remove|delete|drop|deprecat)\w*\b', lower):
        return 'Removed', subject
    if re.search(r'\b(fix|bug|repair|resolve|correct)\w*\b', lower):
        return 'Fixed', subject
    if re.search(r'\b(add|introduce|implement|create)\w*\b', lower):
        return 'Added', subject
    return 'Changed', subject

def generate(cwd=None, today=None):
    tag = latest_tag(cwd)
    revision = f'{tag}..HEAD' if tag else 'HEAD'
    raw = git('log', revision, '--pretty=format:%h%x1f%s%x1e', cwd=cwd)
    sections = defaultdict(list)
    for record in raw.split('\x1e'):
        if '\x1f' not in record:
            continue
        sha, subject = record.strip().split('\x1f', 1)
        if subject.startswith('Merge '):
            continue
        category, description = classify(subject.strip())
        sections[category].append(f'- {description} (`{sha}`)')
    heading = f'## {today or date.today().isoformat()}' + (f' (since {tag})' if tag else ' (all commits; no tags found)')
    lines = ['# Changelog', '', heading, '']
    if not sections:
        lines.extend(['No commits found since the latest tag.', ''])
    else:
        for category in CATEGORIES:
            if sections[category]:
                lines.extend([f'### {category}', *sections[category], ''])
    return '\n'.join(lines).rstrip() + '\n'

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', default='.', help='Git repository directory')
    parser.add_argument('--output', default='CHANGELOG.md', help='Output path')
    args = parser.parse_args()
    try:
        output = generate(args.repo)
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        parser.exit(1, f'Cannot read git history: {exc}\n')
    target = Path(args.output)
    target.write_text(output, encoding='utf-8')
    print(f'Wrote {target} ({len(output.splitlines())} lines)')

if __name__ == '__main__':
    main()
