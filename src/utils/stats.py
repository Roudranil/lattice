from typing import Dict, Optional


def accumulate_usage(total: Dict, new: Dict):
    if not new:
        return total

    for key, value in new.items():
        if isinstance(value, dict):
            total.setdefault(key, {})
            accumulate_usage(total[key], value)
        elif isinstance(value, (int, float)):
            total[key] = total.get(key, 0) + value

    return total


def add_usage_metadata(
    left: Optional[Dict],
    right: Optional[Dict],
) -> Dict:
    if not left:
        return right or {
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
            "input_token_details": {},
            "output_token_details": {},
        }
    if not right:
        return left

    return {
        "input_tokens": left["input_tokens"] + right["input_tokens"],
        "output_tokens": left["output_tokens"] + right["output_tokens"],
        "total_tokens": left["total_tokens"] + right["total_tokens"],
        "input_token_details": left["input_token_details"].update(
            right["input_token_details"]
        ),
        "output_token_details": left["output_token_details"].update(
            right["output_token_details"]
        ),
    }
