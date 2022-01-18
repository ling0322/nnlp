import io
import tempfile
import unittest
import json

from os import path

from nnlp.symbol import EPS_SYM, make_disambig_symbol
from nnlp_tools.mutable_fst import MutableFst, SymbolTable

from .util import norm_textfst

class TestMutableFst(unittest.TestCase):
    ''' unit test class for MutableFst '''

    def test_mutable_fst(self):
        ''' test the MutableFst '''

        mutable_fst = MutableFst()
        state_1 = mutable_fst.create_state()
        state_2 = mutable_fst.create_state()
        mutable_fst.add_arc(0, state_1, '\#unk', '\#0')
        mutable_fst.add_arc(state_1, state_2, make_disambig_symbol(1), EPS_SYM)
        mutable_fst.set_final_state(state_2)

        t = '''
            0 1 \#unk \#0
            1 2 #1 <eps>
            2
            '''
        self.assertEqual(norm_textfst(t), norm_textfst(mutable_fst.to_text()))


    def test_readonly_symbol_table(self):
        ''' test the MutableFst with readonly i/o-symbols '''

        isymbols = SymbolTable()
        isymbols.add_symbol('i')
        isymbols.add_symbol('h')

        osymbols = SymbolTable()
        osymbols.add_symbol('hi')

        mutable_fst = MutableFst(isymbols, osymbols)
        state_1 = mutable_fst.create_state()
        state_2 = mutable_fst.create_state()
        mutable_fst.add_arc(0, state_1, 'h', 'hi')
        mutable_fst.add_arc(state_1, state_2, 'i', '<eps>')
        mutable_fst.set_final_state(state_2)

        t = '''
            0 1 2 1
            1 2 1 0
            2
            '''
        self.assertEqual(norm_textfst(t), norm_textfst(mutable_fst.to_text(with_symbols=False)))

        # unknown symbol
        mutable_fst = MutableFst(isymbols, osymbols)
        state_1 = mutable_fst.create_state()
        self.assertRaises(Exception, mutable_fst.add_arc, 0, state_1, 'hi', 'hi')

    def test_to_json(self):
        ''' test to_json method of FST '''
        mutable_fst = MutableFst()
        state_1 = mutable_fst.create_state()
        state_2 = mutable_fst.create_state()
        mutable_fst.add_arc(0, state_1, EPS_SYM, EPS_SYM, 1)
        mutable_fst.add_arc(state_1, state_1, 'A', 'D', 0.5)
        mutable_fst.add_arc(state_1, state_2, 'B', 'C', 0.5)
        mutable_fst.add_arc(state_2, 0, 'B', 'D', 1)
        mutable_fst.set_final_state(0)

        o = json.loads(mutable_fst.to_json())

        self.assertListEqual(o['graph'], [{
            '<eps>': [[1, '<eps>', 1.0]]
        }, {
            'A': [[1, 'D', 0.5]],
            'B': [[2, 'C', 0.5]]
        }, {
            'B': [[0, 'D', 1.0]]
        }])
        self.assertListEqual(o['final_weights'], [[0, 0]])
        self.assertDictEqual(o['isymbol_dict'], {EPS_SYM: 0, 'A': 1, 'B': 2})

    def test_rmdisambig(self):
        ''' test MutableFst.rmdisambig() '''
        mutable_fst = MutableFst()
        state_1 = mutable_fst.create_state()
        state_2 = mutable_fst.create_state()
        mutable_fst.add_arc(0, state_1, '\#2', '#0')
        mutable_fst.add_arc(state_1, state_2, make_disambig_symbol(1), EPS_SYM)
        mutable_fst.add_arc(state_2, state_2, 'hi', 'hi')
        mutable_fst.set_final_state(state_2)
        mutable_fst = mutable_fst.rmdisambig()

        t = '''
            0 1 \#2 #0
            1 2 <eps> <eps>
            2 2 hi hi
            2
            '''
        self.assertEqual(norm_textfst(t), norm_textfst(mutable_fst.to_text()))
        self.assertDictEqual(dict(mutable_fst._isymbols), {
            0: '<eps>',
            1: '\#2',
            3: 'hi'
        })

