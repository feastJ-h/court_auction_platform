import re


RRN_PATTERN = re.compile(r"(\d{6})-[1-4]\d{6}")
PHONE_PATTERN = re.compile(r"((?:010|02|0[3-6][1-4]?))-\d{3,4}-\d{4}")


def mask_pii(text: str) -> tuple[str, int]:
    masked, rrn_count = RRN_PATTERN.subn(r"\1-*******", text)
    masked, phone_count = PHONE_PATTERN.subn(r"\1-****-****", masked)
    return masked, rrn_count + phone_count
