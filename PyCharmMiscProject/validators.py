import re
import logging
from typing import Optional, List

logger = logging.getLogger(__name__)

EMAIL_PATTERN = re.compile(
    r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$",
    re.IGNORECASE
)

PHONE_KZ_PATTERN = re.compile(
    r"^(\+7|8)[\s\-]?\(?(\d{3})\)?[\s\-]?(\d{3})[\s\-]?(\d{2})[\s\-]?(\d{2})$"
)

PHONE_INTL_PATTERN = re.compile(
    r"^\+?[1-9]\d{6,14}$"
)

URL_PATTERN = re.compile(
    r"https?://[^\s/$.?#].[^\s]*|www\.[a-zA-Z0-9\-]+\.[a-zA-Z]{2,}[^\s]*",
    re.IGNORECASE
)

COMMAND_PATTERN = re.compile(
    r"^/([a-zA-Z0-9_]+)(?:@[a-zA-Z0-9_]+)?$"
)

UNSAFE_PATTERN = re.compile(
    r"[<>&\"\'`\\;{}()\[\]]"
)

WHITESPACE_PATTERN = re.compile(r"\s{2,}")

DIGITS_PATTERN = re.compile(r"\d+")

TIME_PATTERN = re.compile(r"^([01]?\d|2[0-3]):([0-5]\d)$")

def validate_email(email: str) -> bool:
    if not email or not isinstance(email, str):
        return False
    email = email.strip()
    result = bool(EMAIL_PATTERN.match(email))
    logger.debug(f"Email validation: '{email}' → {result}")
    return result

def validate_phone(phone: str) -> bool:
    if not phone or not isinstance(phone, str):
        return False
    cleaned = re.sub(r"[\s\-()]", "", phone.strip())
    result = bool(PHONE_KZ_PATTERN.match(cleaned) or PHONE_INTL_PATTERN.match(cleaned))
    logger.debug(f"Phone validation: '{phone}' → {result}")
    return result

def validate_time(time_str: str) -> bool:
    if not time_str:
        return False
    return bool(TIME_PATTERN.match(time_str.strip()))

def is_valid_command(text: str) -> Optional[str]:
    if not text:
        return None
    match = COMMAND_PATTERN.match(text.strip())
    return match.group(1).lower() if match else None

def extract_urls(text: str) -> List[str]:
    if not text:
        return []
    urls = URL_PATTERN.findall(text)
    logger.debug(f"Extracted {len(urls)} URLs from text")
    return urls

def extract_digits(text: str) -> List[str]:
    if not text:
        return []
    return DIGITS_PATTERN.findall(text)

def extract_emails(text: str) -> List[str]:
    if not text:
        return []
    email_pattern = re.compile(
        r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}",
        re.IGNORECASE
    )
    return email_pattern.findall(text)

def sanitize_input(text: str, max_length: int = 500) -> str:
    if not text:
        return ""

    cleaned = UNSAFE_PATTERN.sub("", text)

    cleaned = WHITESPACE_PATTERN.sub(" ", cleaned)

    cleaned = cleaned.strip()[:max_length]

    if cleaned != text.strip():
        logger.debug(f"Input sanitized: '{text[:50]}' → '{cleaned[:50]}'")

    return cleaned

def clean_text(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", "", text)
    text = WHITESPACE_PATTERN.sub(" ", text)
    return text.strip()

def normalize_phone(phone: str) -> str:
    if not phone:
        return ""
    digits = re.sub(r"[^\d+]", "", phone.strip())
    if digits.startswith("8") and len(digits) == 11:
        digits = "+7" + digits[1:]
    elif digits.startswith("7") and len(digits) == 11:
        digits = "+" + digits
    return digits

def escape_markdown(text: str) -> str:
    if not text:
        return ""
    special_chars = r"\_*[]()~`>#+-=|{}.!"
    return re.sub(r"([" + re.escape(special_chars) + r"])", r"\\\1", text)

def truncate_text(text: str, max_length: int = 200, suffix: str = "...") -> str:
    if not text or len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)].rstrip() + suffix

def is_empty_input(text: str) -> bool:
    return not text or not text.strip()

def normalize_day_name(text: str) -> Optional[str]:
    if not text:
        return None

    text_lower = text.lower().strip()
    day_patterns = {
        "Понедельник": [r"понед", r"пн", r"monday", r"mon"],
        "Вторник": [r"вторн", r"вт", r"tuesday", r"tue"],
        "Среда": [r"сред", r"ср", r"wednesday", r"wed"],
        "Четверг": [r"четв", r"чт", r"thursday", r"thu"],
        "Пятница": [r"пятн", r"пт", r"friday", r"fri"],
        "Суббота": [r"суббот", r"сб", r"saturday", r"sat"],
        "Воскресенье": [r"воскрес", r"вс", r"sunday", r"sun"],
    }
    for day, patterns in day_patterns.items():
        for pattern in patterns:
            if re.search(pattern, text_lower):
                return day
    return None

if __name__ == "__main__":
    print("=== Validators Demo ===\n")
    emails = ["student@iitu.edu.kz", "bad-email", "test@mail.ru", "no@domain"]
    for e in emails:
        print(f"Email '{e}': {validate_email(e)}")

    print()
    phones = ["+77761054008", "87761054008", "+7 (776) 105-40-08", "12345", "87761054008"]
    for p in phones:
        print(f"Phone '{p}': {validate_phone(p)} → normalized: {normalize_phone(p)}")

    print()
    text = "Расписание на сайте https://iitu.edu.kz/schedule и www.example.com"
    print(f"URLs in text: {extract_urls(text)}")

    print()
    dirty = "Hello <script>alert('xss')</script> & 'World'"
    print(f"Sanitized: '{sanitize_input(dirty)}'")

    print()
    for d in ["пн", "вторник", "wed", "ср", "пятница", "unknown"]:
        print(f"Day '{d}' → {normalize_day_name(d)}")