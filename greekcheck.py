#!/usr/bin/env python3

# The structure of this block is heavily based on https://github.com/udapi/udapi-python/blob/master/udapi/block/ud/markbugs.py

import collections
import logging
import re
import unicodedata

from udapi.core.block import Block

REQUIRED_FEATURE_FOR_UPOS = {
    'NOUN': ['Gender', 'Number', 'Case'],
    'PROPN': ['Gender', 'Number', 'Case'],
    'PRON': ['PronType', 'Case', 'Number'],
    'DET': ['PronType', 'Case', 'Number'],
    'ADJ': ['Case', 'Number', 'Gender'],
    'NUM': ['NumType'],
    'VERB': ['VerbForm', 'Aspect'],
}


class GreekCheck(Block):
    """Block for checking suspicious/wrong constructions in Ancient Greek (grc) UD v2."""

    def __init__(self, save_stats=True, tests=None, skip=None, **kwargs):
        """Create the MarkBugs block object.

        Args:
        save_stats: store the bug statistics overview into `document.misc["bugs"]`?
        tests: a regex of tests to include.
            If `not re.search(tests, short_msg)` the node is not reported.
            You can use e.g. `tests=aux-chain|cop-upos` to apply only those two tests.
            Default = None (or empty string or '.*') which all tests.
        skip: a regex of tests to exclude.
            If `re.search(skip, short_msg)` the node is not reported.
            You can use e.g. `skip=no-(VerbForm|NumType|PronType)`.
            This has higher priority than the `tests` regex.
            Default = None (or empty string) which means no skipping.
        """
        super().__init__(**kwargs)
        self.save_stats = save_stats
        self.stats = collections.Counter()
        self.tests_re = re.compile(tests) if (tests is not None and tests != '') else None
        self.skip_re = re.compile(skip) if (skip is not None and skip != '') else None

    def log(self, node, short_msg, long_msg):
        """Log node.address() + long_msg and add ToDo=short_msg to node.misc."""
        if self.tests_re is not None and not self.tests_re.search(short_msg):
            return
        if self.skip_re is not None and self.skip_re.search(short_msg):
            return
        logging.debug('node %s %s: %s', node.address(), short_msg, long_msg)
        if node.misc['Bug']:
            if short_msg not in node.misc['Bug']:
                node.misc['Bug'] += ',' + short_msg
        else:
            node.misc['Bug'] = short_msg
        self.stats[short_msg] += 1

    def has_crasis_mark(self, s):
        crasis_char = chr(0x0313) # Combining comma above
        lower_consonants = 'βγδζθκλμνξπρσςτφχψ'
        norm = unicodedata.normalize('NFD', s.lower())
        if crasis_char in norm:
            for c in norm[:norm.index(crasis_char)]:
                if c in lower_consonants:
                    return True
        return False

    def process_node(self, node):
        form, udeprel, upos, feats = node.form, node.udeprel, node.upos, node.feats
        parent = node.parent

        if self.has_crasis_mark(form):
            self.log(node, 'unsplit-crasis', 'Crasis should be split into a multiword token.')

        mwt = node.multiword_token
        if mwt and not self.has_crasis_mark(mwt.form):
            self.log(node, 'non-crasis-mwt', 'Only crasis should be split into multiword tokens.')

        for i_upos, i_feat_list in REQUIRED_FEATURE_FOR_UPOS.items():
            if upos == i_upos:
                for i_feat in i_feat_list:
                    if not feats[i_feat]:
                        self.log(node, upos+'-no-' + i_feat, 'upos=%s but %s feature is missing' % (upos, i_feat))

        if feats['VerbForm'] == 'Fin':
            if upos not in ('VERB', 'AUX'):
                self.log(node, 'finverb-upos', 'VerbForm=Fin upos!=VERB|AUX (but %s)' % upos)
            if not feats['Mood']:
                self.log(node, 'finverb-mood', 'VerbForm=Fin but Mood feature is missing.')
            if not feats['Tense']:
                self.log(node, 'finverb-tense', 'VerbForm=Fin but Tense feature is missing.')

    def after_process_document(self, document):
        total = 0
        message = 'GreekCheck Error Overview:'
        for bug, count in sorted(self.stats.items(), key=lambda pair: (pair[1], pair[0])):
            total += count
            message += '\n%20s %10d' % (bug, count)
        message += '\n%20s %10d\n' % ('TOTAL', total)
        logging.warning(message)
        if self.save_stats:
            document.meta["bugs"] = message
        self.stats.clear()
