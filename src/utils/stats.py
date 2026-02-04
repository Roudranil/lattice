def accumulate_usage(total: dict, new: dict):
    if not new:
        return total

    for key, value in new.items():
        if isinstance(value, dict):
            total.setdefault(key, {})
            accumulate_usage(total[key], value)
        elif isinstance(value, (int, float)):
            total[key] = total.get(key, 0) + value

    return total
