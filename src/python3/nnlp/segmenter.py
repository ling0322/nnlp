from .decoder import FstDecoder
from .fst import Fst
from .symbol import BRK_SYM

class Segmenter:
    ''' segment a string into small pieces 
    Args:
        fst (Fst): the FST model for segmentation
        beam_size (int): beam_size for decoder
    Usage:
        segmenter = Segmenter(fst_model)
        outputs = segmenter.segment_string(input_str)
    '''

    def __init__(self, fst: Fst, beam_size: int = 8) -> None:
        self._fst = fst
        self._beam_size = beam_size

    def segment_string(self, input: str) -> list[str]:
        ''' segment a string into list of strings
        Args:
            input (str): the input string
        Returns:
            (list[str]): the output segments 
        '''

        input_symbols = list(input)
        decoder = FstDecoder(self._fst, self._beam_size)
        output_symbols = decoder.decode_sequence(input_symbols)
        
        segments = ['']
        for symbol in output_symbols:
            if symbol != BRK_SYM:
                segments[-1] += symbol
            else:
                segments.append('')
        segments = list(filter(lambda tok: tok != '', segments))

        return segments
