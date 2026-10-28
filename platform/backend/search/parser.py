import re


def normalize(text):
    text = text.translate(str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩يك", "01234567890123456789یک"))
    text = re.sub(r"[\u064b-\u065f]", "", text).replace("\u200c", " ")
    text = re.sub(r"[×*]|\b[xX]\b|\sدر\s", "X", text)
    text = re.sub(r"(?i)\bm\s*(\d+)", r"M\1", text)
    text = re.sub(
        r"(?i)\b(din|iso|astm)\s*([a-z]?\d+)",
        lambda m: "".join(m.groups()).upper(),
        text,
    )
    return re.sub(r"\s+", " ", text).strip()


def parse(text):
    text = normalize(text)
    result = {"text": text, "standards": []}
    explicit = re.search(r"\b(?:DIN|ISO|ASTM)\s*[A-Z]?\d+|\bA(?:325|490)\b", text, re.I)
    if explicit:
        result["standards"] = [explicit[0].replace(" ", "").upper()]
    if not explicit:
        for word, codes in [
            ("آلن", ["DIN912", "ISO4762"]),
            ("شش گوش", ["DIN933", "DIN931"]),
            ("مهره", ["DIN934", "ISO4032"]),
            ("فنری", ["DIN127"]),
        ]:
            if word in text:
                result["standards"] = codes
                break
    pair = re.search(r"M?(\d+(?:\.\d+)?)\s*[Xx]\s*(\d+(?:\.\d+)?)", text)
    size = re.search(r"M(\d+(?:\.\d+)?)", text)
    if pair:
        result.update(size="M" + pair[1], length=pair[2])
    elif size:
        result["size"] = "M" + size[1]
    else:
        fraction = re.search(r"\b\d+/\d+\b", text)
        if fraction:
            result["size"] = fraction[0]
        elif result["standards"]:
            remaining = text[explicit.end() :] if explicit else text
            number = re.search(r"\b(\d+)\b", remaining)
            if number:
                result["size"] = "M" + number[1]
    grade = re.search(r"\b(?:4\.6|5\.8|8\.8|10\.9|12\.9|A2|A4)\b", text, re.I)
    if grade:
        result["grade"] = grade[0].upper()
    if "گالوانیزه گرم" in text:
        result["finish"] = "HDG"
    elif any(w in text for w in ["گالوانیزه", "زینک", "سفید"]):
        result["finish"] = "ZN"
    return result
