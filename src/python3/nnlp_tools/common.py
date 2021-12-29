from typing import Optional


class BNFToken:
    r''' BNF token types '''

    SYMBOL = 1  # "hello"
    I_SYMBOL = 2  # "hello":_
    O_SYMBOL = 3  # _:"hello"
    CLASS = 4  # <rule>
    OR = 5  # |
    LEFT_PARENTHESIS = 6  # (
    RIGHT_PARENTHESIS = 7  # )
    QUESTION = 8  # ?
    ASTERISK = 9  # *
    EPSILON = 10  # _
    END = 10001  # end of experssion (only used in rule parser)
    DEFINE = 10002  # ::=

    def __init__(self, token_type: int, value: Optional[str] = None):
        self.type = token_type
        self.value = value

    def __eq__(self, o: object) -> bool:
        if isinstance(o, BNFToken):
            return self.type == o.type and self.value == o.value
        else:
            return False

    def __str__(self) -> str:
        if self.type == self.SYMBOL:
            return f'"{self.value}"'
        elif self.type == self.I_SYMBOL:
            return f'"{self.value}":_'
        elif self.type == self.O_SYMBOL:
            return f'_:"{self.value}"'
        elif self.type == self.CLASS:
            return f'<{self.value}>'
        else:
            return _REPR[self.type]


_REPR = {
    BNFToken.OR: '|',
    BNFToken.LEFT_PARENTHESIS: '(',
    BNFToken.RIGHT_PARENTHESIS: ')',
    BNFToken.QUESTION: '?',
    BNFToken.ASTERISK: '*',
    BNFToken.EPSILON: '_',
    BNFToken.END: '</s>',
    BNFToken.DEFINE: '::='
}
