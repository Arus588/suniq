"""Short-term predictions from recorded INA219 power readings."""


def predict_next_power(values, window=3):
    """Predict one reading ahead from recent readings in one test condition."""
    if len(values) < window:
        return None

    predicted_history = [None] * len(values)
    errors = []
    for index in range(window, len(values)):
        prediction = sum(values[index - window:index]) / window
        predicted_history[index] = prediction
        errors.append(abs(prediction - values[index]))

    return {
        "next_mw": sum(values[-window:]) / window,
        "mae_mw": sum(errors) / len(errors) if errors else None,
        "evaluated_count": len(errors),
        "history_mw": predicted_history,
    }
