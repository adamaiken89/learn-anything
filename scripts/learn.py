#!/usr/bin/env python3
"""Learn Anything CLI — study with spaced repetition (SM-2).

Usage:
  learn.py init <topic> [lang] [--depth survey|standard|deep] [--pretest]
  learn.py start <topic>
  learn.py create-module <topic> <module-id> [--name NAME]
  learn.py quiz <topic> <module> [--weak-only] [--adaptive]
  learn.py explain <topic> <module>
  learn.py feynman <topic> <module>
  learn.py review <topic>
  learn.py stats <topic>
  learn.py export <topic>
  learn.py rate <topic> <module> <score> [--comment TEXT]
  learn.py flag <topic> <module> <type> [--detail TEXT]
  learn.py feedback <topic>
  learn.py analytics <topic>
  learn.py forecast <topic>
  learn.py study-plan <topic>
   learn.py epub <topic> [output] [--mermaid api|local|off]
   learn.py epub-regen <topic> [output] [--mermaid api|local|off]
   learn.py epub-verify <topic> [output]
   learn.py pdf <topic> [output] [--engine auto|weasyprint|pandoc|raw]
   learn.py pdf-regen <topic> [output] [--engine auto|weasyprint|pandoc|raw]
"""

import argparse
import csv
import json
import os
import random
import re
import shutil
import subprocess
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

import sm2 as _sm2

# ── Paths ──────────────────────────────────────────────────────

SKILL_DIR = Path(__file__).resolve().parent.parent
SUBJECTS_DIR = Path.cwd()

# ── Colors ─────────────────────────────────────────────────────


class C:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    CYAN = '\033[0;36m'
    BOLD = '\033[1m'
    NC = '\033[0m'


def cval(val):
    """Return ANSI color code, stripping escapes if output not a TTY."""
    return val if sys.stdout.isatty() else ''


RED = cval(C.RED)
GREEN = cval(C.GREEN)
YELLOW = cval(C.YELLOW)
CYAN = cval(C.CYAN)
BOLD = cval(C.BOLD)
NC = cval(C.NC)

# ── SM-2 Algorithm ─────────────────────────────────────────────

sm2_update = _sm2.update


# ── Topic helpers ───────────────────────────────────────────────


def _topic_path(topic):
    return SUBJECTS_DIR / topic


def _check_topic(topic):
    path = _topic_path(topic)
    if not path.exists():
        print(f'{RED}Topic "{topic}" not found. Run: learn.py init {topic}{NC}')
        sys.exit(1)
    return path


def _module_path(topic, module):
    return _topic_path(topic) / 'modules' / module


def _check_module(topic, module):
    path = _module_path(topic, module)
    if not path.exists():
        print(f"{RED}Module '{module}' not found in '{topic}'{NC}")
        sys.exit(1)
    return path


# ── Syllabus Generation ────────────────────────────────────────


# Depth presets: (module_count, time_per_module_range, time_budget)
_DEPTH_PRESETS = {
    'survey': {'modules': 6, 'time_min': 1.5, 'time_max': 2.0, 'budget': 12},
    'standard': {'modules': 18, 'time_min': 1.5, 'time_max': 2.5, 'budget': 40},
    'deep': {'modules': 28, 'time_min': 2.0, 'time_max': 3.0, 'budget': 75},
}


def _generate_syllabus(topic, lang, depth):
    """Generate a skeleton syllabus YAML with the given depth."""
    preset = _DEPTH_PRESETS.get(depth, _DEPTH_PRESETS['standard'])
    n = preset['modules']
    t_min, t_max = preset['time_min'], preset['time_max']
    budget = preset['budget']

    lines = []
    lines.append(f'subject: "{topic}"')
    lines.append(f'language: {lang}')
    lines.append(f'time_budget_hours: {budget}')
    lines.append('target_level: intermediate')
    lines.append(f'domain: "{topic}"')
    lines.append('prerequisites: []')
    lines.append('learning_objectives:')
    for i in range(1, min(4, n // 3 + 1)):
        lines.append(f'  - "[Objective {i}]"')
    lines.append(f'# Depth: {depth} ({n} modules, ~{budget}h)')
    lines.append('')
    lines.append('modules:')

    for i in range(1, n + 1):
        t = round(random.uniform(t_min, t_max), 1)
        # Build prerequisites: depends on earlier modules
        prereqs = []
        if i > 1:
            # First module has no prereqs, rest depend on 1-2 earlier ones
            candidates = list(range(1, i))
            if len(candidates) > 2:
                candidates = candidates[-2:]  # last 1-2 as prereqs
            prereqs = random.sample(candidates, min(len(candidates), 2))
            prereqs.sort()

        name = f'[Module {i}]'
        lines.append(f'  - id: {i}')
        lines.append(f'    name: "{name}"')
        lines.append(f'    time_hours: {t}')
        lines.append(f'    prerequisites: {prereqs}')
        lines.append('    topics: [topic1, topic2]')

    return '\n'.join(lines) + '\n'


def _run_pretest(topic):
    """Quick pre-test: ask 1 question per syllabus module, skip known ones."""
    path = _topic_path(topic)
    syllabus_path = path / 'syllabus.yaml'
    if not syllabus_path.exists():
        return

    # Parse syllabus to get module count
    with open(syllabus_path) as f:
        content = f.read()

    module_names = re.findall(r'name:\s*"(.+?)"', content)
    if not module_names:
        return

    print(f'  {len(module_names)} modules found. Testing 1 question each.\n')

    skip_count = 0
    skip_modules = []
    for i, name in enumerate(module_names, 1):
        # Generate a placeholder question prompt
        print(f'  [{i}/{len(module_names)}] Module: {name}')
        print('    (In a real session, the AI generates a question here.)')
        print('    Type y if you know this, n to keep in your plan, s to skip: ', end='')

        try:
            answer = input().strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if answer in ('y', 'yes', 's', 'skip'):
            skip_count += 1
            skip_modules.append(name)
            print('    -> Marked as known\n')
        else:
            print('    -> Kept in plan\n')

    if skip_modules:
        print(
            f'{GREEN}Pre-test complete: {skip_count}/{len(module_names)} modules marked as known.{NC}'
        )
        print(f'Known modules: {", ".join(skip_modules)}')
        print('\nTip: Edit syllabus.yaml to remove known modules before creating content.')
    else:
        print(f'{YELLOW}Pre-test complete: no modules skipped.{NC}')


def _list_modules(topic):
    path = _topic_path(topic) / 'modules'
    if not path.exists():
        return []
    return sorted(d.name for d in path.iterdir() if d.is_dir() and (d / 'lesson.md').exists())


def _load_deck(topic):
    """Load deck in Reader format: {"cards": {"id": card}}."""
    deck_path = _topic_path(topic) / 'srs' / 'deck.json'
    if deck_path.exists():
        with open(deck_path) as f:
            data = json.load(f)
        # Auto-migrate old array format to new dict format
        if isinstance(data, list):
            return _migrate_deck_array(data, topic)
        if 'cards' in data:
            return data
        return {'cards': {}}
    return {'cards': {}}


def _migrate_deck_array(old_deck, topic):
    """Convert old array-format deck to Reader-compatible dict format."""
    new_cards = {}
    for card in old_deck:
        cid = card.get('id', '')
        if '.' in cid:
            parts = cid.split('.', 1)
            module_id = parts[0]
        else:
            module_id = 'unknown'
        new_card = {
            'id': f'{topic}-{module_id}-{cid}',
            'questionId': cid,
            'moduleId': module_id,
            'courseId': topic,
            'question': card.get('question', ''),
            'answer': f'{card.get("answer", "a")}. {card.get("options", {}).get(card.get("answer", "a"), "")}',
            'explanation': card.get('explanation', ''),
            'easeFactor': card.get('ease_factor', 2.5),
            'interval': card.get('interval', 0),
            'repetitions': card.get('repetitions', 0),
            'nextReviewDate': card.get('next_review', datetime.now().strftime('%Y-%m-%d')),
            'lastReviewed': card.get('last_review'),
            'isStarred': False,
        }
        new_cards[new_card['id']] = new_card
    migrated = {'cards': new_cards}
    _save_deck(topic, migrated)
    return migrated


def _save_deck(topic, deck):
    """Save deck in Reader format: {"cards": {"id": card}}."""
    path = _topic_path(topic) / 'srs' / 'deck.json'
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(deck, f, indent=2)


def _load_stats(topic):
    path = _topic_path(topic) / 'srs' / 'stats.json'
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {'sessions': []}


def _save_stats(topic, stats):
    path = _topic_path(topic) / 'srs' / 'stats.json'
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(stats, f, indent=2)


def _record_session(topic, session_type, module=None, score=None, total=None):
    stats = _load_stats(topic)
    record = {
        'date': datetime.now().strftime('%Y-%m-%d'),
        'type': session_type,
        'topic': topic,
    }
    if module:
        record['module'] = module
    if score is not None:
        record['score'] = score
    if total is not None:
        record['total'] = total
    stats['sessions'].append(record)
    _save_stats(topic, stats)


# ── Feedback helpers ────────────────────────────────────────────


def _load_feedback(topic):
    path = _topic_path(topic) / 'srs' / 'feedback.json'
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {'ratings': [], 'flags': []}


def _save_feedback(topic, feedback):
    path = _topic_path(topic) / 'srs' / 'feedback.json'
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(feedback, f, indent=2)


# ── Adaptive quiz helpers ───────────────────────────────────────


def _find_card(cards, qid, topic, module):
    """Find a card in the dict by question ID, trying various ID formats."""
    # Try direct match on questionId
    for card in cards.values():
        if card.get('questionId') == qid:
            return card
    # Try legacy format: module.num
    legacy_id = f'{topic}-{module}-{qid}'
    if legacy_id in cards:
        return cards[legacy_id]
    return {}


def _adaptive_sort(questions, cards, topic, module):
    """Sort questions by priority: weak cards first, then by difficulty."""

    def priority(q):
        card = _find_card(cards, q.get('id', ''), topic, module)
        if card:
            ef = card.get('easeFactor', 2.5)
            reps = card.get('repetitions', 0)
            return (ef, reps, q.get('difficulty', 1))
        return (2.5, 0, q.get('difficulty', 1))

    return sorted(questions, key=priority)


# ── Commands ────────────────────────────────────────────────────


def cmd_init(args):
    topic = args.topic
    lang = args.lang or 'en'
    depth = getattr(args, 'depth', 'standard')
    path = _topic_path(topic)
    if path.exists():
        print(f'{RED}Topic "{topic}" already exists. Pick a different name.{NC}')
        sys.exit(1)

    (path / 'modules').mkdir(parents=True, exist_ok=True)
    (path / 'srs').mkdir(parents=True, exist_ok=True)

    # Generate syllabus based on depth
    syllabus = _generate_syllabus(topic, lang, depth)
    with open(path / 'syllabus.yaml', 'w') as f:
        f.write(syllabus)

    depth_info = {
        'survey': ('survey', '~8-12 hours', '5-8 modules'),
        'standard': ('standard', '~30-40 hours', '15-20 modules'),
        'deep': ('deep', '~50+ hours', '25+ modules'),
    }
    label, hours, mods = depth_info.get(depth, depth_info['standard'])

    print(f'{GREEN}Created {path} (language: {lang}, depth: {label}){NC}')
    print(f'  {mods}, {hours}')
    print(
        f'Edit syllabus.yaml, then create modules with: learn.py create-module {topic} <module-id>'
    )

    if getattr(args, 'pretest', False):
        print(f'\n{CYAN}Pre-test: answering a few questions to skip what you know...{NC}')
        _run_pretest(topic)


def cmd_start(args):
    topic = args.topic
    spath = _check_topic(topic)

    syllabus = spath / 'syllabus.yaml'
    if syllabus.exists():
        lines = syllabus.read_text().splitlines()
        for line in lines[:20]:
            print(line)
        lang_match = None
        for line in lines:
            m = re.match(r'^language:\s*(\S+)', line)
            if m:
                lang_match = m.group(1)
                break
        if lang_match:
            print(f'{GREEN} Language: {lang_match}{NC}')
        print()

    print(f'{YELLOW}Modules:{NC}')
    mods_dir = spath / 'modules'
    if mods_dir.exists():
        for mod in sorted(mods_dir.iterdir()):
            if mod.is_dir():
                lesson = mod / 'lesson.md'
                if lesson.exists():
                    print(f'  {CYAN}{mod.name}{NC}')
                else:
                    print(f'  {YELLOW}{mod.name}{NC} (no lesson yet)')

    print()
    print(f'Explain:    learn.py explain {topic} <module-id>')
    print(f'Take quiz:  learn.py quiz {topic} <module-id>')
    print(f'Review:     learn.py review {topic}')


def cmd_create_module(args):
    topic = args.topic
    module_id = args.module_id
    name = args.name or module_id
    _check_topic(topic)

    mod_path = _module_path(topic, module_id)
    if mod_path.exists():
        print(f"{RED}Module '{module_id}' already exists in '{topic}'{NC}")
        sys.exit(1)

    mod_path.mkdir(parents=True, exist_ok=True)

    # Copy lesson template
    lesson_tpl = SKILL_DIR / 'templates' / 'module.md'
    if lesson_tpl.exists():
        with open(lesson_tpl) as f:
            content = f.read()
        content = content.replace('[Title]', name)
        content = content.replace('Module N:', f'Module {module_id}:')
        with open(mod_path / 'lesson.md', 'w') as f:
            f.write(content)

    # Copy quiz template
    quiz_tpl = SKILL_DIR / 'templates' / 'quiz.yaml'
    if quiz_tpl.exists():
        shutil.copy2(quiz_tpl, mod_path / 'quiz.yaml')

    print(f'{GREEN}Created module: {mod_path}{NC}')
    print('  lesson.md — edit content')
    print('  quiz.yaml — add 8-10 MCQs')


def cmd_quiz(args):
    topic = args.topic
    module = args.module
    adaptive = getattr(args, 'adaptive', False)
    weak_only = getattr(args, 'weak_only', False)
    _check_topic(topic)
    _check_module(topic, module)

    quiz_path = _module_path(topic, module) / 'quiz.yaml'
    if not quiz_path.exists():
        print(f'{RED}No quiz found at {quiz_path}{NC}')
        sys.exit(1)

    try:
        import yaml
    except ImportError:
        print(f'{RED}Python yaml library required. Install: pip install pyyaml{NC}')
        print(f'{YELLOW}Raw quiz content:{NC}')
        with open(quiz_path) as f:
            print(f.read())
        sys.exit(1)

    with open(quiz_path) as f:
        questions = yaml.safe_load(f)

    if not questions:
        print(f'{YELLOW}No questions in quiz{NC}')
        return

    deck = _load_deck(topic)
    cards = deck.get('cards', {})

    # Filter to weak cards only if requested
    if weak_only:
        questions = [
            q
            for q in questions
            if _find_card(cards, q.get('id', ''), topic, module).get('easeFactor', 2.5) < 2.0
        ]
        if not questions:
            print(f'{GREEN}No weak cards found. All cards have easeFactor >= 2.0{NC}')
            return

    # Sort questions
    if adaptive:
        questions = _adaptive_sort(questions, cards, topic, module)
        print(f'{CYAN}=== {topic} / {module} Adaptive Quiz ==={NC}\n')
    else:
        random.shuffle(questions)
        print(f'{CYAN}=== {topic} / {module} Quiz ==={NC}\n')

    correct = 0
    streak = 0
    current_difficulty = 1
    seen_ids = set()

    shown = 0
    total_to_show = 0
    for q in questions:
        qid = q.get('id', '')
        if qid in seen_ids:
            continue
        if adaptive and q.get('difficulty', 1) > current_difficulty + 1:
            continue
        total_to_show += 1

    for i, q in enumerate(questions, 1):
        qid = q.get('id', f'{module}.{i}')

        # Anti-repeat: skip if already seen this session
        if qid in seen_ids:
            continue
        seen_ids.add(qid)

        # Adaptive: skip if difficulty too high for current streak
        if adaptive:
            q_diff = q.get('difficulty', 1)
            if q_diff > current_difficulty + 1:
                continue

        shown += 1
        print(f'--- Question {shown}/{total_to_show} ---')
        print(q['question'])
        opts = list(q.get('options', {}).items())
        random.shuffle(opts)
        keymap = {}
        for j, (letter, text) in enumerate(opts):
            key = chr(ord('a') + j)
            keymap[key] = letter
            print(f'  {key}) {text}')

        while True:
            try:
                ans = input('\nYour answer: ').strip().lower()
            except (EOFError, KeyboardInterrupt):
                print()
                return
            if ans in keymap:
                break
            valid_range = f'{min(keymap)}-{max(keymap)}'
            print(f'Invalid. Choose {valid_range}.')

        is_correct = keymap[ans] == q.get('answer', '')
        if is_correct:
            print(f'{GREEN}✓ Correct!{NC}')
            quality = 4
            correct += 1
            streak += 1
            # Adaptive: advance difficulty after 3 correct streak
            if adaptive and streak >= 3 and current_difficulty < 3:
                current_difficulty += 1
                streak = 0
                print(f'  {CYAN}难度提升 → Level {current_difficulty}{NC}')
        else:
            print(f'{RED}✗ Wrong. Correct: {q.get("answer", "?")}{NC}')
            quality = 1
            streak = 0
            # Adaptive: drop difficulty on wrong
            if adaptive and current_difficulty > 1:
                current_difficulty -= 1

        explanation = q.get('explanation', '')
        if explanation:
            print(f'  {explanation}')
        print()

        # ── SRS update: create or update card with SM-2 ──
        card_id = f'{topic}-{module}-{qid}'
        existing = cards.get(card_id) or _find_card(cards, qid, topic, module)

        if existing:
            sm2_update(existing, quality)
        else:
            answer_opt = q.get('answer', 'a')
            card = {
                'id': card_id,
                'questionId': qid,
                'moduleId': module,
                'courseId': topic,
                'question': q['question'],
                'answer': f'{answer_opt}. {q.get("options", {}).get(answer_opt, "")}',
                'explanation': q.get('explanation', ''),
                'tags': q.get('tags', []),
                'easeFactor': 2.5,
                'interval': 0,
                'repetitions': 0,
                'nextReviewDate': datetime.now().strftime('%Y-%m-%d'),
                'lastReviewed': None,
                'isStarred': False,
            }
            sm2_update(card, quality)
            cards[card_id] = card

    deck['cards'] = cards
    _save_deck(topic, deck)

    pct = correct * 100 // shown if shown else 0
    print(f'\nScore: {correct}/{shown} ({pct}%)')
    _record_session(topic, 'quiz', module=module, score=correct, total=shown)


def cmd_explain(args):
    topic = args.topic
    module = args.module
    _check_topic(topic)
    _check_module(topic, module)

    lesson_path = _module_path(topic, module) / 'lesson.md'
    if not lesson_path.exists():
        print(f'{RED}No lesson found at {lesson_path}{NC}')
        sys.exit(1)

    print(f'{CYAN}=== Feynman Explain: {topic} / {module} ==={NC}')
    print()
    print('Step 1: Explain the core concept as if teaching a child.')
    print('  - Simplest words. No jargon.')
    print('  - Give concrete example from your daily work.')
    print()
    print('Step 2: Self-check your explanation for:')
    print("  - Vague words: 'stuff', 'things', 'basically', 'kind of'")
    print("  - Circular reasoning: 'it works because that's how it works'")
    print('  - Missing steps: did you skip a causal link?')
    print('  - Unnecessary complexity: can you shorten it?')
    print()
    print('Step 3: Run this command again after refining.')
    print('  For deeper probing, say explanation in opencode chat.')
    print('  AI will find gaps you missed.')
    print()
    print(f'{YELLOW}Concept to explain:{NC}')
    lines = lesson_path.read_text().splitlines()
    found = False
    for i, line in enumerate(lines):
        if re.match(r'^## (Core Concept|The Core|Feynman)', line):
            print(line)
            for extra in lines[i + 1 : i + 4]:
                print(extra)
            found = True
            break
    if not found:
        print('(no core concept heading found)')
    print()
    print(f'Lesson: {lesson_path}')


def cmd_review(args):
    topic = args.topic
    _check_topic(topic)

    deck = _load_deck(topic)
    cards = deck.get('cards', {})
    if not cards:
        print(f'{YELLOW}No SRS deck yet. Take a quiz first: learn.py quiz {topic} <module>{NC}')
        return

    today = datetime.now().strftime('%Y-%m-%d')
    due = [c for c in cards.values() if c.get('nextReviewDate', '2000-01-01') <= today]

    if not due:
        print(f'{GREEN}No cards due for review!{NC}')
        return

    random.shuffle(due)
    correct = 0
    total = len(due)

    print(f'{CYAN}=== Review: {total} card(s) due ==={NC}\n')

    for card in due:
        print(f'Q: {card["question"]}')
        # Parse answer from "a. option text" format
        answer_key = card.get('answer', 'a. ')[0]
        print(f'  Answer key: {answer_key}')
        explanation = card.get('explanation', '')

        while True:
            try:
                ans = input('\nYour answer (a/b/c/d or s=show): ').strip().lower()
            except (EOFError, KeyboardInterrupt):
                print()
                return
            if ans in ('a', 'b', 'c', 'd'):
                break
            if ans == 's':
                print(f'  {GREEN}Answer: {card.get("answer", "?")}{NC}')
                if explanation:
                    print(f'  {explanation}')
                ans = None
                break
            print('Invalid. Choose a, b, c, d, or s to show.')

        if ans is None:
            # Showed answer — mark as review for re-attempt later
            quality = 2
        elif ans == answer_key:
            print(f'{GREEN}✓ Correct!{NC}')
            quality = 4
            correct += 1
        else:
            print(f'{RED}✗ Wrong. Correct: {card.get("answer", "?")}{NC}')
            quality = 1

        if ans is not None and explanation:
            print(f'  {explanation}')
        print()

        sm2_update(card, quality)

    deck['cards'] = cards
    _save_deck(topic, deck)

    if total > 0:
        pct = correct * 100 // total
        print(f'\nScore: {correct}/{total} ({pct}%)')
        _record_session(topic, 'review', score=correct, total=total)


def cmd_stats(args):
    topic = args.topic
    _check_topic(topic)

    deck = _load_deck(topic)
    cards = deck.get('cards', {})
    if not cards:
        print(f'{YELLOW}No stats yet. Take a quiz first.{NC}')
        return

    total = len(cards)
    reviewed = [c for c in cards.values() if c.get('lastReviewed')]
    today = datetime.now().strftime('%Y-%m-%d')
    due_today = [c for c in cards.values() if c.get('nextReviewDate', '2000-01-01') <= today]
    mastered = [c for c in cards.values() if c.get('interval', 0) >= 21]
    avg_ef = sum(c.get('easeFactor', 2.5) for c in cards.values()) / total

    print(f'Cards: {total}')
    print(f'Reviewed: {len(reviewed)}')
    print(f'Due today: {len(due_today)}')
    print(f'Mastered (interval >= 21d): {len(mastered)}')
    print(f'Avg ease factor: {avg_ef:.2f}')
    print()

    # Module breakdown
    module_counts = Counter()
    for c in cards.values():
        mod = c.get('moduleId', '?')
        module_counts[mod] += 1
    print('By module:')
    for mod in sorted(module_counts):
        print(f'  Module {mod}: {module_counts[mod]} cards')

    # Session history
    stats = _load_stats(topic)
    if stats.get('sessions'):
        print()
        print('Recent sessions:')
        for s in stats['sessions'][-5:]:
            parts = [s['date'], s['type']]
            if s.get('module'):
                parts.append(s['module'])
            if s.get('score') is not None and s.get('total') is not None:
                parts.append(f'{s["score"]}/{s["total"]}')
            print(f'  {" | ".join(parts)}')


def cmd_export(args):
    topic = args.topic
    _check_topic(topic)

    deck = _load_deck(topic)
    cards = deck.get('cards', {})
    if not cards:
        print(f'{YELLOW}No deck to export.{NC}')
        return

    out_path = _topic_path(topic) / 'srs' / 'deck.csv'
    with open(out_path, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['Question', 'Answer', 'Explanation', 'Tags'])
        for card in cards.values():
            w.writerow(
                [
                    card.get('question', ''),
                    card.get('answer', ''),
                    card.get('explanation', ''),
                    ' '.join(card.get('tags', [])),
                ]
            )

    print(f'{GREEN}Exported {len(cards)} cards to {out_path}{NC}')
    print('Import into Anki via: File > Import')


def cmd_rate(args):
    topic = args.topic
    module = args.module
    score = args.score
    comment = getattr(args, 'comment', '') or ''
    _check_topic(topic)
    _check_module(topic, module)

    if not 1 <= score <= 5:
        print(f'{RED}Score must be 1-5{NC}')
        sys.exit(1)

    feedback = _load_feedback(topic)
    feedback['ratings'].append(
        {
            'module': module,
            'score': score,
            'date': datetime.now().isoformat(),
            'comment': comment,
        }
    )
    _save_feedback(topic, feedback)
    print(f'{GREEN}Rated {module}: {score}/5{NC}')


def cmd_flag(args):
    topic = args.topic
    module = args.module
    flag_type = args.type
    detail = getattr(args, 'detail', '') or ''
    _check_topic(topic)
    _check_module(topic, module)

    valid_types = ['wrong', 'outdated', 'confusing']
    if flag_type not in valid_types:
        print(f'{RED}Flag type must be one of: {", ".join(valid_types)}{NC}')
        sys.exit(1)

    feedback = _load_feedback(topic)
    feedback['flags'].append(
        {
            'module': module,
            'type': flag_type,
            'detail': detail,
            'date': datetime.now().isoformat(),
        }
    )
    _save_feedback(topic, feedback)
    print(f'{GREEN}Flagged {module}: {flag_type}{NC}')


def cmd_feedback(args):
    topic = args.topic
    _check_topic(topic)

    feedback = _load_feedback(topic)
    ratings = feedback.get('ratings', [])
    flags = feedback.get('flags', [])

    if not ratings and not flags:
        print(f'{YELLOW}No feedback yet.{NC}')
        return

    print(f'{CYAN}=== Feedback: {topic} ==={NC}\n')

    mod_ratings = {}
    mod_flags = {}

    if ratings:
        print(f'{YELLOW}Ratings:{NC}')
        for r in ratings:
            mod = r['module']
            mod_ratings.setdefault(mod, []).append(r['score'])
        for mod in sorted(mod_ratings):
            scores = mod_ratings[mod]
            avg = sum(scores) / len(scores)
            bar = '★' * int(round(avg)) + '☆' * (5 - int(round(avg)))
            print(f'  {mod}: {bar} {avg:.1f}/5 ({len(scores)} ratings)')
        print()

    if flags:
        print(f'{YELLOW}Flags:{NC}')
        for f in flags:
            mod = f['module']
            mod_flags.setdefault(mod, []).append(f['type'])
        for mod in sorted(mod_flags):
            types = mod_flags[mod]
            counts = Counter(types)
            parts = [f'{t}: {c}' for t, c in counts.most_common()]
            print(f'  {mod}: {", ".join(parts)}')
        print()

    # Suggest modules to revisit
    low_rated = [mod for mod, scores in mod_ratings.items() if sum(scores) / len(scores) < 3.0]
    flagged = list(mod_flags.keys())
    revisit = sorted(set(low_rated + flagged))
    if revisit:
        print(f'{YELLOW}Suggest revisiting:{NC}')
        for mod in revisit:
            print(f'  - {mod}')


def cmd_analytics(args):
    topic = args.topic
    _check_topic(topic)

    deck = _load_deck(topic)
    cards = deck.get('cards', {})
    stats = _load_stats(topic)

    if not cards:
        print(f'{YELLOW}No data yet. Take a quiz first.{NC}')
        return

    total_cards = len(cards)
    mastered = [c for c in cards.values() if c.get('interval', 0) >= 21]
    learning = [c for c in cards.values() if 0 < c.get('interval', 0) < 21]
    new_cards = [c for c in cards.values() if not c.get('lastReviewed')]

    print(f'{CYAN}=== Analytics: {topic} ==={NC}\n')

    print(f'Total cards: {total_cards}')
    print(f'  New (never reviewed): {len(new_cards)}')
    print(f'  Learning (interval < 21d): {len(learning)}')
    print(f'  Mastered (interval >= 21d): {len(mastered)}')
    if total_cards > 0:
        mastery_pct = len(mastered) * 100 // total_cards
        bar_len = 30
        filled = mastery_pct * bar_len // 100
        bar = '█' * filled + '░' * (bar_len - filled)
        print(f'  Mastery: [{bar}] {mastery_pct}%')
    print()

    # Session retention over time
    sessions = stats.get('sessions', [])
    if sessions:
        print(f'{YELLOW}Session history:{NC}')
        daily = {}
        for s in sessions:
            date = s['date']
            daily.setdefault(date, {'quiz': [], 'review': []})
            if s['type'] == 'quiz' and s.get('score') is not None and s.get('total') is not None:
                daily[date]['quiz'].append((s['score'], s['total']))
            elif (
                s['type'] == 'review' and s.get('score') is not None and s.get('total') is not None
            ):
                daily[date]['review'].append((s['score'], s['total']))

        for date in sorted(daily.keys())[-10:]:
            parts = [date]
            if daily[date]['quiz']:
                q_correct = sum(s[0] for s in daily[date]['quiz'])
                q_total = sum(s[1] for s in daily[date]['quiz'])
                parts.append(f'quiz {q_correct}/{q_total}')
            if daily[date]['review']:
                r_correct = sum(s[0] for s in daily[date]['review'])
                r_total = sum(s[1] for s in daily[date]['review'])
                parts.append(f'review {r_correct}/{r_total}')
            print(f'  {" | ".join(parts)}')
    print()

    # Weak modules (by ease factor)
    mod_ef = {}
    for c in cards.values():
        mod = c.get('moduleId', '?')
        mod_ef.setdefault(mod, []).append(c.get('easeFactor', 2.5))

    if mod_ef:
        print(f'{YELLOW}Module difficulty (avg ease factor):{NC}')
        mod_avg = [(mod, sum(efs) / len(efs)) for mod, efs in mod_ef.items()]
        mod_avg.sort(key=lambda x: x[1])
        for mod, avg in mod_avg:
            indicator = f'{RED}⚠{NC}' if avg < 2.0 else ''
            print(f'  {mod}: {avg:.2f} {indicator}')


def cmd_forecast(args):
    topic = args.topic
    _check_topic(topic)

    deck = _load_deck(topic)
    cards = deck.get('cards', {})
    if not cards:
        print(f'{YELLOW}No deck yet.{NC}')
        return

    today = datetime.now()
    today_str = today.strftime('%Y-%m-%d')

    due_now = []
    due_week = []
    due_month = []
    later = []

    for card in cards.values():
        nr = card.get('nextReviewDate', '2000-01-01')
        if nr <= today_str:
            due_now.append(card)
        else:
            try:
                due_date = datetime.strptime(nr, '%Y-%m-%d')
                days = (due_date - today).days
                if days <= 7:
                    due_week.append((days, card))
                elif days <= 30:
                    due_month.append((days, card))
                else:
                    later.append((days, card))
            except ValueError:
                later.append((999, card))

    print(f'{CYAN}=== Forgetting Forecast: {topic} ==={NC}\n')

    print(f'{RED}Due now: {len(due_now)} cards{NC}')
    if due_now:
        mods = Counter(c.get('moduleId', '?') for c in due_now)
        for mod, count in mods.most_common():
            print(f'  {mod}: {count} cards')

    print(f'\nDue this week: {len(due_week)} cards')
    due_week.sort()
    for days, card in due_week[:5]:
        mod = card.get('moduleId', '?')
        print(f'  In {days}d: {mod} — {card["question"][:50]}...')
    if len(due_week) > 5:
        print(f'  ... and {len(due_week) - 5} more')

    print(f'\nDue this month: {len(due_month)} cards')
    print(f'  Later: {len(later)} cards')


def cmd_study_plan(args):
    topic = args.topic
    _check_topic(topic)

    deck = _load_deck(topic)
    cards = deck.get('cards', {})
    if not cards:
        print(f'{YELLOW}No deck yet. Take a quiz first.{NC}')
        return

    today_str = datetime.now().strftime('%Y-%m-%d')

    due_now = [c for c in cards.values() if c.get('nextReviewDate', '2000-01-01') <= today_str]
    weak = [
        c
        for c in cards.values()
        if c.get('easeFactor', 2.5) < 2.0 and c.get('nextReviewDate', '2000-01-01') > today_str
    ]
    mastered = [c for c in cards.values() if c.get('interval', 0) >= 21]

    print(f'{CYAN}=== Study Plan: {topic} ==={NC}\n')

    total_suggested = 0

    if due_now:
        print(f'{RED}Priority: {len(due_now)} cards due now{NC}')
        mods = Counter(c.get('moduleId', '?') for c in due_now)
        for mod, count in mods.most_common(5):
            print(f'  {mod}: {count} cards')
        total_suggested += len(due_now)

    if weak:
        print(f'\n{YELLOW}Weak cards (easeFactor < 2.0): {len(weak)}{NC}')
        mods = Counter(c.get('moduleId', '?') for c in weak)
        for mod, count in mods.most_common(5):
            print(f'  {mod}: {count} cards')
        total_suggested += len(weak)

    if mastered:
        print(f'\n{GREEN}Mastered: {len(mastered)} cards (review less frequently){NC}')

    target = 20
    print(f'\n{CYAN}Suggested session: {min(total_suggested, target)} cards{NC}')
    if total_suggested > target:
        print('  (Focus on due + weak. Skip mastered.)')
    elif total_suggested == 0:
        print('  All caught up! Next review based on SM-2 schedule.')


def cmd_epub(args):
    topic = args.topic
    output = args.output
    mermaid = args.mermaid
    description = args.description
    theme = args.theme

    _check_topic(topic)
    spath = _topic_path(topic)

    if not output:
        output = str(spath / f'{topic}.epub')

    epub_script = SKILL_DIR / 'scripts' / 'epub.py'
    if not epub_script.exists():
        print(f'{RED}epub.py not found at {epub_script}{NC}')
        sys.exit(1)

    cmd = [
        sys.executable,
        str(epub_script),
        'build',
        str(spath),
        output,
        '--mermaid',
        mermaid,
        '--theme',
        theme,
    ]
    if description:
        cmd.extend(['--description', description])

    print(f'{CYAN}Building EPUB: {topic}{NC}')
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(result.stdout, end='')
    if result.stderr:
        print(result.stderr, file=sys.stderr, end='')

    if os.path.exists(output):
        size_kb = os.path.getsize(output) / 1024
        print(f'{GREEN}EPUB: {output} ({size_kb:.1f} KB){NC}')
    else:
        print(f'{RED}Failed{NC}')
        sys.exit(1)


def _pdf_extra_args(args):
    cmd = []
    if args.title:
        cmd.extend(['--title', args.title])
    if args.author:
        cmd.extend(['--author', args.author])
    cmd.extend(['--engine', args.engine])
    return cmd


def cmd_pdf(args):
    topic = args.topic
    output = args.output

    _check_topic(topic)
    spath = _topic_path(topic)

    if not output:
        output = str(spath / f'{topic}.pdf')

    pdf_script = SKILL_DIR / 'scripts' / 'pdf.py'
    if not pdf_script.exists():
        print(f'{RED}pdf.py not found at {pdf_script}{NC}')
        sys.exit(1)

    print(f'{CYAN}Building PDF: {topic}{NC}')
    cmd = [sys.executable, str(pdf_script), 'build', str(spath), output] + _pdf_extra_args(args)
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
    )
    print(result.stdout, end='')
    if result.stderr:
        print(result.stderr, file=sys.stderr, end='')

    if os.path.exists(output):
        size_kb = os.path.getsize(output) / 1024
        print(f'{GREEN}PDF: {output} ({size_kb:.1f} KB){NC}')
    else:
        print(f'{RED}Failed{NC}')
        sys.exit(1)


def cmd_pdf_regen(args):
    topic = args.topic
    output = args.output

    _check_topic(topic)
    spath = _topic_path(topic)
    book_md = spath / 'book.md'

    if not book_md.exists():
        print(f"{YELLOW}No book.md. Run 'pdf' first.{NC}")
        return

    if not output:
        output = str(spath / f'{topic}.pdf')

    pdf_script = SKILL_DIR / 'scripts' / 'pdf.py'
    if not pdf_script.exists():
        print(f'{RED}pdf.py not found at {pdf_script}{NC}')
        sys.exit(1)

    print(f'{CYAN}Regenerating PDF from cached markdown: {topic}{NC}')
    cmd = [sys.executable, str(pdf_script), 'from-md', str(book_md), output] + _pdf_extra_args(args)
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
    )
    print(result.stdout, end='')
    if result.stderr:
        print(result.stderr, file=sys.stderr, end='')

    if os.path.exists(output):
        size_kb = os.path.getsize(output) / 1024
        print(f'{GREEN}PDF: {output} ({size_kb:.1f} KB){NC}')
    else:
        print(f'{RED}Failed{NC}')
        sys.exit(1)


def cmd_epub_regen(args):
    topic = args.topic
    output = args.output
    mermaid = args.mermaid
    description = args.description
    theme = args.theme

    _check_topic(topic)
    spath = _topic_path(topic)
    book_md = spath / 'book.md'

    if not book_md.exists():
        print(f"{YELLOW}No book.md. Run 'epub' first.{NC}")
        return

    if not output:
        output = str(spath / f'{topic}.epub')

    epub_script = SKILL_DIR / 'scripts' / 'epub.py'
    if not epub_script.exists():
        print(f'{RED}epub.py not found at {epub_script}{NC}')
        sys.exit(1)

    cmd = [
        sys.executable,
        str(epub_script),
        'from-md',
        str(book_md),
        output,
        '--mermaid',
        mermaid,
        '--theme',
        theme,
    ]
    if description:
        cmd.extend(['--description', description])

    print(f'{CYAN}Regenerating EPUB from cached markdown: {topic}{NC}')
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(result.stdout, end='')
    if result.stderr:
        print(result.stderr, file=sys.stderr, end='')

    if os.path.exists(output):
        size_kb = os.path.getsize(output) / 1024
        print(f'{GREEN}EPUB: {output} ({size_kb:.1f} KB){NC}')
    else:
        print(f'{RED}Failed{NC}')
        sys.exit(1)


def cmd_epub_list_themes(args):
    epub_script = SKILL_DIR / 'scripts' / 'epub.py'
    if not epub_script.exists():
        print(f'{RED}epub.py not found at {epub_script}{NC}')
        sys.exit(1)
    result = subprocess.run(
        [sys.executable, str(epub_script), 'list-themes'], capture_output=True, text=True
    )
    if result.stdout:
        print(result.stdout, end='')
    if result.stderr:
        print(result.stderr, file=sys.stderr, end='')
    sys.exit(result.returncode)


def cmd_epub_verify(args):
    topic = args.topic
    output = args.output

    _check_topic(topic)
    spath = _topic_path(topic)

    if not output:
        epub_path = spath / f'{topic}.epub'
    else:
        epub_path = Path(output)

    if not epub_path.exists():
        print(f'{RED}EPUB not found: {epub_path}{NC}')
        return

    epub_script = SKILL_DIR / 'scripts' / 'epub.py'
    if not epub_script.exists():
        print(f'{RED}epub.py not found at {epub_script}{NC}')
        sys.exit(1)

    print(f'{CYAN}Verifying EPUB: {topic}{NC}')
    result = subprocess.run(
        [sys.executable, str(epub_script), 'verify', str(epub_path)],
        capture_output=True,
        text=True,
    )
    print(result.stdout, end='')
    if result.stderr:
        print(result.stderr, file=sys.stderr, end='')


# ── CLI Parser ──────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description='Learn Anything — study with spaced repetition (SM-2)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
  init <topic> [lang]           Create topic dir (optional, auto-created on first use)
  start <topic>                 Show topic overview and modules
  create-module <topic> <mod>   Create new module from template
  quiz <topic> <mod>            Take MCQ quiz (--adaptive, --weak-only)
  explain <topic> <mod>         Feynman Technique prompt
  feynman <topic> <mod>         Alias for explain
  review <topic>                Spaced repetition review
  stats <topic>                 Study statistics
  export <topic>                Export to Anki CSV
  rate <topic> <mod> <1-5>      Rate module clarity
  flag <topic> <mod> <type>     Report content error (wrong/outdated/confusing)
  feedback <topic>              Show aggregated feedback and suggestions
  analytics <topic>             Retention analytics and mastery breakdown
  forecast <topic>              Forgetting forecast (what's due when)
  study-plan <topic>            Optimal study session composition
  epub <topic> [file]           Export course to EPUB book
  epub-regen <topic> [file]     Regenerate EPUB from cached markdown
  epub-verify <topic> [file]    Validate EPUB structure
  pdf <topic> [file]            Export course to PDF
  pdf-regen <topic> [file]      Regenerate PDF from cached book.md
        """,
    )
    sub = parser.add_subparsers(dest='command')
    sub.required = True

    p = sub.add_parser('init', help='Create topic directory with syllabus template')
    p.add_argument('topic')
    p.add_argument('lang', nargs='?', default='en')
    p.add_argument(
        '--depth',
        default='standard',
        choices=['survey', 'standard', 'deep'],
        help='Module depth: survey (~6), standard (~18), deep (~28)',
    )
    p.add_argument(
        '--pretest', action='store_true', help='Take a quick pre-test to skip known content'
    )

    p = sub.add_parser('start', help='Show topic overview')
    p.add_argument('topic')

    p = sub.add_parser('create-module', help='Create new module from template')
    p.add_argument('topic')
    p.add_argument('module_id')
    p.add_argument('--name', default=None, help='Human-readable module name')

    p = sub.add_parser('quiz', help='Take MCQ quiz')
    p.add_argument('topic')
    p.add_argument('module')
    p.add_argument('--adaptive', action='store_true', help='Adaptive difficulty mode')
    p.add_argument('--weak-only', action='store_true', help='Only quiz on weak cards (ease < 2.0)')

    p = sub.add_parser('explain', help='Feynman Technique prompt')
    p.add_argument('topic')
    p.add_argument('module')

    p = sub.add_parser('feynman', help='Feynman Technique prompt (alias)')
    p.add_argument('topic')
    p.add_argument('module')

    p = sub.add_parser('review', help='Spaced repetition review')
    p.add_argument('topic')

    p = sub.add_parser('stats', help='Study statistics')
    p.add_argument('topic')

    p = sub.add_parser('export', help='Export to Anki CSV')
    p.add_argument('topic')

    p = sub.add_parser('rate', help='Rate a module (1-5 stars)')
    p.add_argument('topic')
    p.add_argument('module')
    p.add_argument('score', type=int)
    p.add_argument('--comment', default='', help='Optional comment')

    p = sub.add_parser('flag', help='Report content error')
    p.add_argument('topic')
    p.add_argument('module')
    p.add_argument('type', choices=['wrong', 'outdated', 'confusing'])
    p.add_argument('--detail', default='', help='Details about the issue')

    p = sub.add_parser('feedback', help='Show aggregated feedback')
    p.add_argument('topic')

    p = sub.add_parser('analytics', help='Retention analytics')
    p.add_argument('topic')

    p = sub.add_parser('forecast', help='Forgetting forecast')
    p.add_argument('topic')

    p = sub.add_parser('study-plan', help='Optimal study plan')
    p.add_argument('topic')

    p = sub.add_parser('epub-list-themes', help='List available EPUB themes')

    p = sub.add_parser('epub', help='Export course to EPUB')
    p.add_argument('topic')
    p.add_argument('output', nargs='?', default=None)
    p.add_argument('--description', default='', help='Cover page description')
    p.add_argument(
        '--theme',
        default='notebook',
        help='Theme name (default: notebook). Use epub-list-themes to see all themes.',
    )
    p.add_argument(
        '--mermaid',
        default='api',
        choices=['api', 'local', 'off'],
        help='Mermaid rendering mode: api (default), local (mmdc CLI), off (skip)',
    )

    p = sub.add_parser('epub-regen', help='Regenerate EPUB from cached book.md')
    p.add_argument('topic')
    p.add_argument('output', nargs='?', default=None)
    p.add_argument('--description', default='', help='Cover page description')
    p.add_argument(
        '--theme',
        default='notebook',
        help='Theme name (default: notebook). Use epub-list-themes to see all themes.',
    )
    p.add_argument(
        '--mermaid',
        default='api',
        choices=['api', 'local', 'off'],
        help='Mermaid rendering mode: api (default), local (mmdc CLI), off (skip)',
    )

    p = sub.add_parser('epub-verify', help='Validate EPUB structure')
    p.add_argument('topic')
    p.add_argument('output', nargs='?', default=None)

    p = sub.add_parser('pdf', help='Export course to PDF')
    p.add_argument('topic')
    p.add_argument('output', nargs='?', default=None)
    p.add_argument('--title', default=None, help='PDF title (default: topic dir name)')
    p.add_argument('--author', default='Learn Anything', help='PDF author')
    p.add_argument(
        '--engine',
        default='auto',
        choices=['auto', 'weasyprint', 'pandoc', 'raw'],
        help='PDF engine: auto (default), weasyprint, pandoc, raw (stdlib)',
    )

    p = sub.add_parser('pdf-regen', help='Regenerate PDF from cached book.md')
    p.add_argument('topic')
    p.add_argument('output', nargs='?', default=None)
    p.add_argument('--title', default=None, help='PDF title (default: topic dir name)')
    p.add_argument('--author', default='Learn Anything', help='PDF author')
    p.add_argument(
        '--engine',
        default='auto',
        choices=['auto', 'weasyprint', 'pandoc', 'raw'],
        help='PDF engine: auto (default), weasyprint, pandoc, raw (stdlib)',
    )

    p = sub.add_parser('sync', help='Export deck to Reader directory')
    p.add_argument('topic')
    p.add_argument(
        '--reader-path',
        default=None,
        help='Reader subjects dir (default: ~/.coursereader/subjects)',
    )

    p = sub.add_parser('sync-pull', help='Import deck from Reader directory')
    p.add_argument('topic')
    p.add_argument(
        '--reader-path',
        default=None,
        help='Reader subjects dir (default: ~/.coursereader/subjects)',
    )

    sub.add_parser('help', help='Show this help message')

    args = parser.parse_args()

    if args.command == 'help':
        parser.print_help()
        return

    dispatch = {
        'init': cmd_init,
        'start': cmd_start,
        'create-module': cmd_create_module,
        'quiz': cmd_quiz,
        'explain': cmd_explain,
        'feynman': cmd_explain,
        'review': cmd_review,
        'stats': cmd_stats,
        'export': cmd_export,
        'rate': cmd_rate,
        'flag': cmd_flag,
        'feedback': cmd_feedback,
        'analytics': cmd_analytics,
        'forecast': cmd_forecast,
        'study-plan': cmd_study_plan,
        'epub': cmd_epub,
        'epub-regen': cmd_epub_regen,
        'epub-verify': cmd_epub_verify,
        'epub-list-themes': cmd_epub_list_themes,
        'pdf': cmd_pdf,
        'pdf-regen': cmd_pdf_regen,
        'sync': cmd_sync,
        'sync-pull': cmd_sync_pull,
    }

    fn = dispatch.get(args.command)
    if fn:
        fn(args)
    else:
        parser.print_help()
        sys.exit(1)


def _reader_subjects_path(reader_path=None):
    """Return the Reader's subjects directory."""
    if reader_path:
        return Path(reader_path)
    return Path.home() / '.coursereader' / 'subjects'


def cmd_sync(args):
    """Export CLI deck to Reader-compatible directory."""
    topic = args.topic
    _check_topic(topic)

    reader_subjects = _reader_subjects_path(getattr(args, 'reader_path', None))
    reader_topic = reader_subjects / topic

    # Create Reader directory structure
    reader_srs = reader_topic / 'srs'
    reader_srs.mkdir(parents=True, exist_ok=True)

    # Load and save deck (already in Reader format)
    deck = _load_deck(topic)
    cards = deck.get('cards', {})
    if not cards:
        print(f'{YELLOW}No cards to sync.{NC}')
        return

    # Save deck
    with open(reader_srs / 'deck.json', 'w') as f:
        json.dump(deck, f, indent=2)

    # Copy modules (lesson.md + quiz.yaml)
    reader_modules = reader_topic / 'modules'
    reader_modules.mkdir(parents=True, exist_ok=True)

    cli_modules = _topic_path(topic) / 'modules'
    copied = 0
    for mod_dir in sorted(cli_modules.iterdir()):
        if not mod_dir.is_dir():
            continue
        reader_mod = reader_modules / mod_dir.name
        reader_mod.mkdir(exist_ok=True)
        for fname in ['lesson.md', 'quiz.yaml']:
            src = mod_dir / fname
            if src.exists():
                import shutil

                shutil.copy2(src, reader_mod / fname)
                copied += 1

    # Copy syllabus
    syllabus_src = _topic_path(topic) / 'syllabus.yaml'
    if syllabus_src.exists():
        import shutil

        shutil.copy2(syllabus_src, reader_topic / 'syllabus.yaml')

    print(f'{GREEN}Synced to Reader: {reader_topic}{NC}')
    print(f'  Deck: {len(cards)} cards')
    print(f'  Modules: {copied} files copied')


def cmd_sync_pull(args):
    """Import deck from Reader directory to CLI."""
    topic = args.topic
    reader_subjects = _reader_subjects_path(getattr(args, 'reader_path', None))
    reader_topic = reader_subjects / topic

    if not reader_topic.exists():
        print(f'{RED}Reader topic not found: {reader_topic}{NC}')
        sys.exit(1)

    reader_deck = reader_topic / 'srs' / 'deck.json'
    if not reader_deck.exists():
        print(f'{RED}No deck found at {reader_deck}{NC}')
        sys.exit(1)

    # Ensure CLI topic exists
    cli_topic = _topic_path(topic)
    cli_topic.mkdir(parents=True, exist_ok=True)
    cli_srs = cli_topic / 'srs'
    cli_srs.mkdir(exist_ok=True)

    # Load Reader deck and save to CLI
    with open(reader_deck) as f:
        deck = json.load(f)

    # Ensure it's in dict format
    if isinstance(deck, list):
        deck = _migrate_deck_array(deck, topic)

    with open(cli_srs / 'deck.json', 'w') as f:
        json.dump(deck, f, indent=2)

    cards = deck.get('cards', {})
    print(f'{GREEN}Imported from Reader: {reader_topic}{NC}')
    print(f'  Deck: {len(cards)} cards')


if __name__ == '__main__':
    main()
