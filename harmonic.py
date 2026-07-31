# Camelot Wheel Rules for Harmonic Mixing
# The Camelot wheel ranges from 1-12, and A (minor) or B (major).

def parse_key(key):
    # E.g. "8A" -> 8, "A"
    number = int(key[:-1])
    letter = key[-1].upper()
    return number, letter

def get_compatible_keys(key):
    """
    Returns a list of compatible keys based on the Camelot wheel rules:
    - Same key
    - Relative major/minor (change letter, keep number)
    - +1 / -1 movement (keep letter, change number by 1)
    - Energy boost (+2 movement)
    - Dominant/Subdominant shifts
    """
    if not key or len(key) < 2:
        return []

    try:
        num, letter = parse_key(key)
    except ValueError:
        return []

    compatible = []

    # 1. Same key
    compatible.append(f"{num}{letter}")

    # 2. Relative major/minor (Same number, opposite letter)
    opp_letter = 'B' if letter == 'A' else 'A'
    compatible.append(f"{num}{opp_letter}")

    # 3. +1 movement (subdominant/dominant)
    num_plus = num + 1 if num < 12 else 1
    compatible.append(f"{num_plus}{letter}")

    # 4. -1 movement
    num_minus = num - 1 if num > 1 else 12
    compatible.append(f"{num_minus}{letter}")

    # 5. Energy boost (+2 movement)
    num_boost = (num + 2) if (num + 2) <= 12 else (num + 2 - 12)
    compatible.append(f"{num_boost}{letter}")

    # 6. Emotional transition / Diagonal shift (e.g. 8A -> 9B, 8B -> 7A)
    # Minor (A) +1 number to Major (B)
    if letter == 'A':
        emo_num = num + 1 if num < 12 else 1
        compatible.append(f"{emo_num}B")

        # Subdominant minor to relative major (e.g., 8A -> 7B)
        sub_num = num - 1 if num > 1 else 12
        compatible.append(f"{sub_num}B")
    else:
        # Major (B) -1 number to Minor (A)
        emo_num = num - 1 if num > 1 else 12
        compatible.append(f"{emo_num}A")

        # Dominant major to relative minor (e.g., 8B -> 9A)
        dom_num = num + 1 if num < 12 else 1
        compatible.append(f"{dom_num}A")

    # Clean duplicates while preserving order
    result = []
    for k in compatible:
        if k not in result:
            result.append(k)

    return result

# Mapping Open Key, Musical Key, and Camelot
# For this example, we keep it simple, primarily focusing on Camelot.

CAMELOT_TO_MUSICAL = {
    "1A": "Abm", "1B": "B",
    "2A": "Ebm", "2B": "F#",
    "3A": "Bbm", "3B": "Db",
    "4A": "Fm",  "4B": "Ab",
    "5A": "Cm",  "5B": "Eb",
    "6A": "Gm",  "6B": "Bb",
    "7A": "Dm",  "7B": "F",
    "8A": "Am",  "8B": "C",
    "9A": "Em",  "9B": "G",
    "10A": "Bm", "10B": "D",
    "11A": "F#m", "11B": "A",
    "12A": "Dbm", "12B": "E"
}

MUSICAL_TO_CAMELOT = {v: k for k, v in CAMELOT_TO_MUSICAL.items()}

def musical_to_camelot(musical_key):
    # Simple mapping
    return MUSICAL_TO_CAMELOT.get(musical_key, "")

def camelot_to_musical(camelot_key):
    return CAMELOT_TO_MUSICAL.get(camelot_key, "")
