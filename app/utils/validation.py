import re

ENTRY_CODE_PATTERN = re.compile(r'^[A-Za-z0-9_-]{3,50}$')


def validate_entry_code(code):
    if not code or not ENTRY_CODE_PATTERN.match(code.strip()):
        return False, 'Entry code must be 3-50 alphanumeric characters.'
    return True, None


def validate_quiz_type_form(name, question_count, duration_minutes, entry_code):
    if not name or len(name.strip()) < 2:
        return False, 'Quiz name must be at least 2 characters.'
    try:
        qc = int(question_count)
        dm = int(duration_minutes)
    except (TypeError, ValueError):
        return False, 'Question count and duration must be valid numbers.'
    if qc < 1 or qc > 20:
        return False, 'Question count must be between 1 and 20.'
    if dm < 1 or dm > 30:
        return False, 'Duration must be between 1 and 30 minutes.'
    ok, msg = validate_entry_code(entry_code)
    if not ok:
        return False, msg
    return True, None
