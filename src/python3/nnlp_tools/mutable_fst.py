from __future__ import annotations

import pywrapfst
import pyfstext
import math
import json
from typing import Iterator, Union, Optional
from nnlp.symbol import EPS_SYM, is_disambig_symbol
from nnlp.fst import Fst
from .symbol_table import SymbolTable

NAN = float('nan')


class MutableFst:
    ''' mutable FST that support add arcs dynamically '''

    # symbol table for input and output symbols
    _isymbols: SymbolTable
    _osymbols: SymbolTable
    _fst: pywrapfst.VectorFst

    def __init__(self,
                 isymbols: Optional[SymbolTable] = None,
                 osymbols: Optional[SymbolTable] = None,
                 name: str = 'FST') -> None:
        if isymbols:
            self._isymbols = isymbols
            self._isymbols_readonly = True
        else:
            self._isymbols = SymbolTable()
            self._isymbols_readonly = False

        if osymbols:
            self._osymbols = osymbols
            self._osymbols_readonly = True
        else:
            self._osymbols = SymbolTable()
            self._osymbols_readonly = False

        self._fst = pywrapfst.VectorFst()
        state_zero = self._fst.add_state()
        self._fst.set_start(state_zero)

        self.name = name

    def create_state(self) -> int:
        ''' add a new state '''
        return self._fst.add_state()

    def set_final_state(self, state: int, weight: float = 0.0) -> None:
        ''' set final state with weight '''
        self._fst.set_final(state, weight)

    def print_info(self) -> None:
        ''' print information of FST to stdout '''
        num_iepsilons = 0
        num_oepsilons = 0
        num_epsilons = 0
        num_arcs = 0
        for _, _, isym, osym, _ in self.arcs():
            num_arcs += 1
            if isym == EPS_SYM:
                num_iepsilons += 1
            if osym == EPS_SYM:
                num_oepsilons += 1
            if isym == EPS_SYM and osym == EPS_SYM:
                num_epsilons += 1

        print(f'fstinfo: {self.name}')
        print(f'# of states: {self._fst.num_states()}')
        print(f'# of final states: {len(self.final_states())}')
        print(f'# of arcs: {num_arcs}')
        print(f'# of epsilons: {num_epsilons}')
        print(f'# of input epsilons: {num_iepsilons}')
        print(f'# of output epsilons: {num_oepsilons}')
        print()

    def add_arc(self,
                src_state: int,
                dest_state: int,
                isymbol: str,
                osymbol: str,
                weight: float = 0.0) -> None:
        ''' add arc to FST '''

        isymbol_id = self._get_symbol_id(isymbol, self._isymbols,
                                         self._isymbols_readonly)
        osymbol_id = self._get_symbol_id(osymbol, self._osymbols,
                                         self._osymbols_readonly)

        arc = pywrapfst.Arc(isymbol_id, osymbol_id, weight, dest_state)
        self._fst.add_arc(src_state, arc)

    def write(self, prefix: str) -> None:
        '''
        Write FST, isymbols, osymbols to <prefix>.{fst, isyms.txt, osyms.txt}
        '''
        self._fst.write(f'{prefix}.fst')
        self._isymbols.write_text(f'{prefix}.isyms.txt')
        self._osymbols.write_text(f'{prefix}.osyms.txt')

    def to_text(self, with_symbols: bool = True) -> str:
        '''
        serialize the FST to AT&T format string
        Args:
            with_symbols: true if print symbols instead of label-id
        '''
        if with_symbols:
            return self._fst.print(isymbols=self._isymbols._symbol_table,
                                   osymbols=self._osymbols._symbol_table)
        else:
            return self._fst.print()

    def states(self) -> Iterator[int]:
        ''' returns an iterator of all states in FST '''
        return self._fst.states()

    def final_states(self) -> dict[int, float]:
        ''' returns dict of (final states, final weight) in FST. This method
        will go through all states in FST, so it will take long time if FST is
        large
        '''
        # final weights
        final: dict[int, float] = {}
        for state in self.states():
            weight = float(self._fst.final(state))
            if math.isfinite(weight):
                final[state] = weight
        
        return final

    def arcs(self) -> Iterator[tuple[int, int, str, str, float]]:
        ''' returns an iterator of all arcs in FST '''
        for state in self._fst.states():
            for arc in self._fst.arcs(state):
                yield (
                    state,
                    arc.nextstate,
                    self._isymbols.get_symbol(arc.ilabel),
                    self._osymbols.get_symbol(arc.olabel),
                    float(arc.weight),
                )

    def rmdisambig(self) -> MutableFst:
        ''' returns a new FST the same as current one excepts that all
        disambiguation symbols have be converted to <eps> '''
        fst = MutableFst(name=f'rds({self.name})')
        fst._isymbols = self._isymbols.copy()
        fst._osymbols = self._osymbols.copy()
        fst._fst = self._fst.copy()

        # get set of disambig symbols
        idisambig_labels = set()
        rds_isymbols = pywrapfst.SymbolTable()
        for label, symbol in fst._isymbols._symbol_table:
            if is_disambig_symbol(symbol):
                idisambig_labels.add(label)
            else:
                rds_isymbols.add_symbol(symbol, label)

        for state in self._fst.states():
            mutable_arc_iter = fst._fst.mutable_arcs(state)
            for arc in mutable_arc_iter:
                if arc.ilabel in idisambig_labels:
                    arc = pywrapfst.Arc(0, arc.olabel, arc.weight,
                                        arc.nextstate)
                    mutable_arc_iter.set_value(arc)

        # replace isymbols with the new symbol table without disambig symbols
        fst._isymbols._symbol_table = rds_isymbols
        return fst

    def determinize(self) -> MutableFst:
        ''' returns equivalent deterministic FST '''
        fst = MutableFst(name=f'det({self.name})')
        fst._isymbols = self._isymbols.copy()
        fst._osymbols = self._osymbols.copy()
        fst._fst = pywrapfst.determinize(self._fst)

        return fst

    def rmepslocal(self) -> MutableFst:
        ''' returns equivalent FST after removing epsilon arcs as much as
        possible
        '''
        fst = MutableFst(name=f'rel({self.name})')
        fst._isymbols = self._isymbols.copy()
        fst._osymbols = self._osymbols.copy()
        fst._fst = self._fst.copy()

        pyfstext.RemoveEpsilonLocal(fst._fst)

        return fst

    def minimize(self, allow_nondet: bool = False) -> MutableFst:
        ''' performs the minimization of FST '''
        fst = MutableFst(name=f'min({self.name})')
        fst._isymbols = self._isymbols.copy()
        fst._osymbols = self._osymbols.copy()
        fst._fst = self._fst.minimize(allow_nondet=allow_nondet)

        return fst

    def compose(self, fst: MutableFst) -> MutableFst:
        ''' composes two FSTs, returns (self o fst) '''
        if not self._osymbols is fst._isymbols:
            raise Exception('FST compose: in-/output symbols table mismatch')
        composed_fst = MutableFst(name=f'{self.name} o {fst.name}')
        composed_fst._isymbols = self._isymbols.copy()
        composed_fst._osymbols = fst._osymbols.copy()
        composed_fst._fst = pywrapfst.compose(self._fst, fst._fst)

        return composed_fst

    def to_json(self) -> str:
        '''
        convert the FST to json string, this FST could be read by nnlp.Fst
        '''
        isymbol_dict: dict[str, int] = {}
        for isym_id, isymbol in self._isymbols:
            isymbol_dict[isymbol] = isym_id

        # arcs
        graph: list[dict[str, list[tuple[int, str, float]]]] = []
        for src_state, dest_state, isymbol, osymbol, weight in self.arcs():
            # add arc to graph
            while len(graph) <= src_state:
                graph.append(dict())
            if isymbol not in graph[src_state]:
                graph[src_state][isymbol] = []
            graph[src_state][isymbol].append((dest_state, osymbol, weight))

        # final weights
        final = self.final_states()

        o = dict(version=1,
                 graph=graph,
                 isymbol_dict=isymbol_dict,
                 final_weights=list(final.items()))
        return json.dumps(o, separators=(',', ':'))

    def _get_symbol_id(self, symbol: str, symbol_table: SymbolTable,
                       readonly: bool) -> int:
        '''
        get id of a input symbol from symbol_table. When readonly == False,
        create a newsymbol id for nonexisting symbols, otherwise, raise an
        Exception
        '''
        if symbol == '':
            raise Exception(
                f'empty symbol is not supported, use EPS_SYM instead?')

        if symbol not in symbol_table:
            if readonly:
                raise Exception(f'symbol not exist: {symbol}')
            return symbol_table.add_symbol(symbol)
        else:
            symbol_id = symbol_table.get_id(symbol)
            return symbol_id
