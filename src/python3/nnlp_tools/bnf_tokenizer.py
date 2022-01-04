from typing import List, Optional, Tuple
import re

from .util import BNFSyntaxError
from .common import BNFToken


class BNFTokenizer:
    r''' convert BNF experession string to tokens, also it will handle some grammer sugars
    for example,
        <hello> ::= "hello" -> <hello> ::= "hello":"hello"
        <hi> ::= @"hi" -> <hello> ::= "h":"h" "i":"i"
        <hi> ::= @"hi":_ -> <hello> ::= "h":_ "i":_    # _ is the epsilon symbol
    '''

    def __init__(self):
        self._re_special_char = re.compile(r'[ \t:]')
        self._offset = 0
        self._expression = ''

    def _discard_space(self) -> None:
        r''' read and discard spaces '''
        while self._offset < len(self._expression) and self._expression[self._offset].isspace():
            self._offset += 1

    def _is_end(self) -> bool:
        r''' returns true if end of expression reached '''
        if self._offset >= len(self._expression):
            return True
        return False

    def _read_symbol(self) -> Optional[BNFToken]:
        r''' read a symbol token from self._expression[self._offset: ], the symbol token contains
        following types:
            _                ->  BNFToken(EPSILON, value="_")
            "hello"          ->  BNFToken(SYMBOL, value="hello")
            "hello":_        ->  BNFToken(I_SYMBOL, value="hello")
            _:"hello"        ->  BNFToken(O_SYMBOL, value="hello")
        On success, returns BNFToken else returns None'''

        def _read_one_symbol():
            r''' read one single symbol from self._expression[self._offset] '''
            if self._expression[self._offset] == '_':
                self._offset += 1
                return None
            if self._expression[self._offset] != '"':
                raise BNFSyntaxError(f'symbol expected in position {self._offset}')

            end_pos = self._expression.find('"', self._offset + 1)
            if end_pos == -1:
                raise BNFSyntaxError(f'quote mismatch')
            value = self._expression[self._offset + 1:end_pos]
            if value == '':
                raise BNFSyntaxError(f'symbol is empty')
            self._offset = end_pos + 1

            return value

        if self._expression[self._offset] in {'"', '_'}:
            i_symbol = None
            o_symbol = None
            symbol = _read_one_symbol()
            if self._offset < len(self._expression) and self._expression[self._offset] == ':':
                self._offset += 1
                i_symbol = symbol
                o_symbol = _read_one_symbol()
                symbol = None

            if symbol:
                return BNFToken(BNFToken.SYMBOL, symbol)
            elif not i_symbol and not o_symbol:
                return BNFToken(BNFToken.EPSILON)
            elif not i_symbol and o_symbol:
                return BNFToken(BNFToken.O_SYMBOL, o_symbol)
            elif i_symbol and not o_symbol:
                return BNFToken(BNFToken.I_SYMBOL, i_symbol)
            else:
                # both i_symbol and o_symbol have values
                raise BNFSyntaxError(f'either input or output symbols should be _')
        else:
            return None

    def _read_class(self) -> Optional[BNFToken]:
        r''' read a class token like <hello> from self._expression[self._offset: ]
        On success, returns (CLASS, None) else returns None'''

        if self._expression[self._offset] == '<':
            end_pos = self._expression.find('>', self._offset + 1)
            if end_pos == -1:
                raise BNFSyntaxError(f'invalid rule name')
            value = self._expression[self._offset + 1:end_pos]
            value = value.strip()
            if value == "" or self._re_special_char.search(value):
                raise BNFSyntaxError(f'invalid class name')

            # update _offset
            self._offset = end_pos + 1

            return BNFToken(BNFToken.CLASS, value)
        else:
            return None

    def _read_macro(self) -> Optional[BNFToken]:
        ''' read a macro from self._expression[self._offset: ], returns (MACRO_*, paramater) if
        success, otherwise returns None'''

        if self._expression[self._offset] == '!':
            lp_pos = self._expression.find('("', self._offset + 1)
            if lp_pos == -1:
                raise BNFSyntaxError(f'invalid macro')
            macro_name = self._expression[self._offset + 1: lp_pos].strip()
            rp_pos = self._expression.find('")', lp_pos + 2)
            if rp_pos == -1:
                raise BNFSyntaxError(f'invalid macro')
            macro_param = self._expression[lp_pos + 2: rp_pos]
            self._offset = rp_pos + 2

            if macro_name == 'read_lexicon':
                return BNFToken(BNFToken.MACRO_READ_LEXICON, macro_param)
            else:
                raise BNFSyntaxError(f'invalid macro name: {macro_name}')
        else:
            return None

    def _read_define(self) -> Optional[BNFToken]:
        r''' read a define token ::= from self._expression[self._offset: ]
        On success, returns (DEFINE, '') else returns None'''

        if self._expression[self._offset:self._offset + 3] == '::=':
            self._offset += 3

            return BNFToken(BNFToken.DEFINE)
        else:
            return None

    def __call__(self, bnf_expression: str) -> Tuple[str, List[BNFToken]]:
        r''' apply tokenizer on bnf experssion, returns tuple (rule name, list of tokens) '''

        self._expression = bnf_expression
        self._offset = 0

        self._discard_space()
        if self._is_end():
            raise BNFSyntaxError(f'unexpected end of expression')

        token = self._read_class()
        if not token:
            raise BNFSyntaxError(f'<class-name> expected at {self._offset}')
        class_name = token.value
        assert class_name

        self._discard_space()
        if self._is_end():
            raise BNFSyntaxError(f'unexpected end of expression')
        token = self._read_define()
        if token == None:
            raise BNFSyntaxError(f'token ::= expected at {self._offset}')

        tokens: List[BNFToken] = []
        while True:
            self._discard_space()
            if self._is_end():
                break

            ch = self._expression[self._offset]
            if ch == '"' or ch == '_':
                token = self._read_symbol()
            elif ch == '!':
                token = self._read_macro()
            elif ch == '|':
                token = BNFToken(BNFToken.OR)
                self._offset += 1
            elif ch == '(':
                token = BNFToken(BNFToken.LEFT_PARENTHESIS)
                self._offset += 1
            elif ch == ')':
                token = BNFToken(BNFToken.RIGHT_PARENTHESIS)
                self._offset += 1
            elif ch == '?':
                token = BNFToken(BNFToken.QUESTION)
                self._offset += 1
            elif ch == '*':
                token = BNFToken(BNFToken.ASTERISK)
                self._offset += 1
            elif ch == '<':
                token = self._read_class()
            else:
                raise BNFSyntaxError(f'invalid character "{ch}" at {self._offset}')

            if not token:
                raise BNFSyntaxError(f'invalid character at {self._offset}')

            tokens.append(token)

        if tokens == []:
            raise BNFSyntaxError(f'unexpected end of expression')

        return class_name, tokens
