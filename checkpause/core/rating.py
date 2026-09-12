RATINGS = (
    (85.0, "optimal"),
    (75.0, "precise"),
    (65.0, "competent"),
    (50.0, "steady"),
    (0.0, "volatile"),
)


def rating_key(accuracy):
    if accuracy is None:
        return None
    for threshold, key in RATINGS:
        if accuracy >= threshold:
            return key
    return "volatile"
