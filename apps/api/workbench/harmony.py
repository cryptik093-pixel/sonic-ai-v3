"""One harmonic timeline shared by every pitched part; no model-derived notes."""
from .midi import ROOTS, SCALES


def harmonic_plan(command):
    s = command.settings
    progression = s.progression or ([1, 6, 4, 5] if command.scale == 'major' else
                                   ([1, 4, 6, 5] if command.style == 'soul' else [1, 6, 3, 7]))
    degrees = [progression[(bar // s.progression_rate) % len(progression)] - 1
               for bar in range(command.bars)]
    # A closed phrase lands every part on I/i. Loop mode preserves user progression.
    if s.cadence == 'resolve':
        degrees[-1] = 0
    return degrees


def degree_pitch(command, degree):
    scale = SCALES[command.scale]
    return ROOTS[command.key] + scale[degree % 7] + 12 * (degree // 7)


def chord_classes(command, degree):
    # Stable melodic anchors use the triad, even when the pad has extensions.
    return {degree_pitch(command, degree + offset) % 12 for offset in (0, 2, 4)}


def choose_pitch(command, degree, register, previous=None, anchor=False, contour=0):
    pc = degree_pitch(command, degree) % 12
    pcs = chord_classes(command, anchor) if anchor is not False else {pc}
    candidates = [n for n in range(register.low, register.high + 1) if n % 12 in pcs]
    if previous is not None:
        candidates = [n for n in candidates if abs(n - previous) <= command.settings.max_melodic_leap]
    if not candidates:
        raise ValueError('No feasible melodic path within the range and maximum leap; widen the range or leap limit.')
    target = (register.low + register.high) / 2 + contour
    if previous is not None:
        target = .65 * previous + .35 * target
    return min(candidates, key=lambda n: (abs(n - target) + (0 if n % 12 == pc else 2), n))


def melodic_path(command, targets):
    """Dynamic programming prevents a locally attractive note blocking a later cadence."""
    register = command.settings.melody_range
    scale_pcs = {(ROOTS[command.key] + n) % 12 for n in SCALES[command.scale]}
    layers = []
    for degree, anchor, contour, tonic in targets:
        preferred = degree_pitch(command, degree) % 12
        pcs = {ROOTS[command.key]} if tonic else (chord_classes(command, anchor) if anchor is not False else scale_pcs)
        options = [n for n in range(register.low, register.high + 1) if n % 12 in pcs]
        center = (register.low + register.high) / 2 + contour
        layer = {}
        for pitch in options:
            local_cost = abs(pitch - center) * .15 + (0 if pitch % 12 == preferred else 3)
            if not layers:
                layer[pitch] = (local_cost, None)
            else:
                links = [(cost + abs(pitch - prior) * .35 + max(0, abs(pitch-prior)-4), prior)
                         for prior, (cost, _) in layers[-1].items()
                         if abs(pitch-prior) <= command.settings.max_melodic_leap]
                if links:
                    cost, prior = min(links)
                    layer[pitch] = (cost + local_cost, prior)
        if not layer:
            raise ValueError('No feasible melodic path within the range and maximum leap; widen the range or leap limit.')
        layers.append(layer)
    pitch = min(layers[-1], key=lambda n: (layers[-1][n][0], n))
    path = []
    for layer in reversed(layers):
        path.append(pitch)
        pitch = layer[pitch][1]
    return path[::-1]
