"""SM-2 spaced repetition algorithm."""

from datetime import datetime, timedelta


def update(card, quality):
    """Update card's SM-2 fields given quality (0-5). Returns updated card.

    Uses camelCase fields to match Reader format:
    easeFactor, interval, repetitions, nextReviewDate, lastReviewed
    """
    ef = card.get('easeFactor', 2.5)
    rep = card.get('repetitions', 0)
    interval = card.get('interval', 0)

    if quality >= 3:
        if rep == 0:
            interval = 1
        elif rep == 1:
            interval = 6
        else:
            interval = round(interval * ef)
        rep += 1
    else:
        rep = 0
        interval = 1

    ef = ef + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    if ef < 1.3:
        ef = 1.3

    card['easeFactor'] = round(ef, 2)
    card['repetitions'] = rep
    card['interval'] = interval
    card['nextReviewDate'] = (datetime.now() + timedelta(days=interval)).strftime('%Y-%m-%d')
    card['lastReviewed'] = datetime.now().strftime('%Y-%m-%d')
    return card
