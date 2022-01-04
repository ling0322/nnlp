from .decoder import FstDecoder
from .fst import Fst

class Converter:
    ''' converts a string to another with FST 
    Args:
        fst (Fst): the FST model for convertion
        beam_size (int): beam_size for decoder
    Usage:
        converter = Converter(fst_model)
        output_str = converter.convert_string(input_str)
    '''

    def __init__(self, fst: Fst, beam_size: int = 8) -> None:
        self._fst = fst
        self._beam_size = beam_size

    def convert_string(self, input: str) -> str:
        ''' convert one string to another using FST
        Args:
            input (str): the input string
        Returns:
            (str): the output string 
        '''

        input_symbols = list(input)
        decoder = FstDecoder(self._fst, self._beam_size)
        output_symbols = decoder.decode_sequence(input_symbols)
        return ''.join(output_symbols)
