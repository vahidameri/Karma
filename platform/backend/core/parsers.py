"""Keep decimal JSON literals exact until the typed serializer interprets them."""

import json

from rest_framework.exceptions import ParseError
from rest_framework.parsers import JSONParser


class ExactJSONParser(JSONParser):
    def parse(self, stream, media_type=None, parser_context=None):
        raw = stream.read(2_500_001)
        if len(raw) > 2_500_000:
            raise ParseError("JSON body exceeds 2.5 MB")

        def invalid_constant(value):
            raise ValueError("Non-finite JSON number")

        try:
            # Monetary/quantity serializers consume strings as Decimal. Unknown JSON values
            # also retain exact decimal text instead of introducing an IEEE-754 float.
            return json.loads(raw.decode("utf-8"), parse_float=str, parse_constant=invalid_constant)
        except (ValueError, UnicodeError, RecursionError) as error:
            raise ParseError("Invalid JSON") from error
