# -*- coding: utf-8 -*-
# Copyright (c) 2012, Freek Dijkstra <software@macfreek.nl>
# Some rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:

# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.


"""
    sphinxcontrib.restbuilder
    =========================

    Sphinx extension to output reST files.

    .. moduleauthor:: Freek Dijkstra <software@macfreek.nl>
    
    Please refer to the documentation_ for further information.
    
    .. _`Sphinx`: http://sphinx.pocoo.org/latest
    .. _`sphinx-contrib`: http://bitbucket.org/birkenfeld/sphinx-contrib
    .. _documentation: http://packages.python.org/sphinxcontrib-restbuilder
"""

# from __future__ import (print_function, division, unicode_literals,
#                         absolute_import)

import codecs
import os
import re
import textwrap

from sphinx.builders import Builder
#from sphinx.writers.context import ConTeXtWriter

from docutils import nodes, writers

from sphinx import addnodes
from sphinx.locale import admonitionlabels, versionlabels, _
from sphinx.writers.text import TextTranslator


from docutils.io import StringOutput

from sphinx.builders import Builder
from sphinx.builders.text import TextBuilder
from sphinx.util.osutil import ensuredir


SEP = "/"

# Clone of relative_uri() sphinx.util.osutil, with bug-fixes
# since the original code had a few errors.
def relative_uri(base, to):
    """Return a relative URL from ``base`` to ``to``."""
    if to.startswith(SEP):
        return to
    b2 = base.split(SEP)
    t2 = to.split(SEP)
    # remove common segments (except the last segment)
    for x, y in zip(b2[:-1], t2[:-1]):
        if x != y:
            break
        b2.pop(0)
        t2.pop(0)
    if b2 == t2:
        # Special case: relative_uri('f/index.html','f/index.html')
        # returns '', not 'index.html'
        return ''
    if len(b2) == 1 and t2 == ['']:
        # Special case: relative_uri('f/index.html','f/') should 
        # return './', not ''
        return '.' +  SEP
    return ('..' + SEP) * (len(b2)-1) + SEP.join(t2)



import textwrap

from docutils import nodes, writers

from sphinx import addnodes
from sphinx.locale import admonitionlabels, versionlabels, _

# 
# class TextWrapper(textwrap.TextWrapper):
#     """Custom subclass that uses a different word separator regex."""
# 
#     wordsep_re = re.compile(
#         r'(\s+|'                                  # any whitespace
#         r'(?<=\s)(?::[a-z-]+:)?`\S+|'             # interpreted text start
#         r'[^\s\w]*\w+[a-zA-Z]-(?=\w+[a-zA-Z])|'   # hyphenated words
#         r'(?<=[\w\!\"\'\&\.\,\?])-{2,}(?=\w))')   # em-dash
# 

class RstBuilder(Builder):
    name = 'rst'
    format = 'rst'
    file_suffix = '.rst'
    link_suffix = None  # defaults to file_suffix
    file_transform = None
    link_transform = None

    def init(self):
        """Load necessary templates and perform initialization."""
        if self.config.rst_file_suffix is not None:
            self.file_suffix = self.config.rst_file_suffix
        if self.config.rst_link_suffix is not None:
            self.link_suffix = self.config.rst_link_suffix
        elif self.link_suffix == None:
            self.link_suffix = self.file_suffix

        # Closure (function) to convert the docname to a reST file name.
        def file_transform(docname):
            return docname + self.file_suffix
        
        # Closure (function) to convert the docname to a relative URI.
        def link_transform(docname):
            return docname + self.link_suffix
        
        if self.config.rst_file_transform != None:
            self.file_transform = self.config.rst_file_transform
        else:
            self.file_transform = file_transform
        if self.config.rst_link_transform != None:
            self.link_transform = self.config.rst_link_transform
        else:
            self.link_transform = link_transform

    def get_outdated_docs(self):
        """
        Return an iterable of output files that are outdated, or a string
        describing what an update build will build.

        If the builder does not output individual files corresponding to
        source files, return a string here. If it does, return an iterable of
        those files that need to be written.
        """
        for docname in self.env.found_docs:
            if docname not in self.env.all_docs:
                yield docname
                continue
            targetname = os.path.join(self.outdir, self.file_transform(docname))
            sourcename = os.path.join(self.env.srcdir, docname + 
                        self.env.source_suffix)

            try:
                targetmtime = path.getmtime(targetname)
            except Exception:
                targetmtime = 0
            try:
                srcmtime = path.getmtime(sourcename)
                if srcmtime > targetmtime:
                    yield docname
            except EnvironmentError:
                # source doesn't exist anymore
                pass

    def get_target_uri(self, docname, typ=None):
        return self.link_transform(docname)

    def get_relative_uri(self, from_, to, typ=None):
        """Return a relative URI between two source filenames.

        May raise environment.NoUri if there's no way to return a sensible URI.
        """
        return relative_uri(self.get_target_uri(from_),
                            self.get_target_uri(to, typ))
        # Builder.get_relative_uri(self, from_, to, typ)

    def prepare_writing(self, docnames):
        self.writer = RstWriter(self)

    def write_doc(self, docname, doctree):
        destination = StringOutput(encoding='utf-8')
        # print "write(%s,%s)" % (type(doctree), type(destination))

        self.writer.write(doctree, destination)
        outfilename = os.path.join(self.outdir, self.file_transform(docname))
        # print "write(%s,%s) -> %s" % (type(doctree), type(destination), outfilename)
        ensuredir(os.path.dirname(outfilename))
        try:
            f = codecs.open(outfilename, 'w', 'utf-8')
            try:
                f.write(self.writer.output)
            finally:
                f.close()
        except (IOError, OSError), err:
            self.warn("error writing file %s: %s" % (outfilename, err))

    def finish(self):
        self.writer = None




class RstWriter(writers.Writer):
    supported = ('text',)
    settings_spec = ('No options here.', '', ())
    settings_defaults = {}

    output = None

    def __init__(self, builder):
        writers.Writer.__init__(self)
        self.builder = builder

    def translate(self):
        visitor = RstTranslator(self.document, self.builder)
        self.document.walkabout(visitor)
        self.output = visitor.body

MAXWIDTH = 78
STDINDENT = 4

class RstTranslator(TextTranslator):
    sectionchars = '*=-~"+`'

    def __init__(self, document, builder):
        TextTranslator.__init__(self, document, builder)

        newlines = builder.config.text_newlines
        if newlines == 'windows':
            self.nl = '\r\n'
        elif newlines == 'native':
            self.nl = os.linesep
        else:
            self.nl = '\n'
        self.sectionchars = builder.config.text_sectionchars
        self.states = [[]]
        self.stateindent = [0]
        self.list_counter = []
        self.sectionlevel = 0
        self.table = None
        self.wrapper = textwrap.TextWrapper(width=STDINDENT, break_long_words=False, break_on_hyphens=False)

    def wrap(self, text, width=STDINDENT):
        self.wrapper.width = width
        return self.wrapper.wrap(text)

    def add_text(self, text):
        self.states[-1].append((-1, text))
    def new_state(self, indent=STDINDENT):
        self.states.append([])
        self.stateindent.append(indent)
    def end_state(self, wrap=True, end=[''], first=None):
        content = self.states.pop()
        maxindent = sum(self.stateindent)
        indent = self.stateindent.pop()
        result = []
        toformat = []
        def do_format():
            if not toformat:
                return
            if wrap:
                res = self.wrap(''.join(toformat), width=MAXWIDTH-maxindent)
            else:
                res = ''.join(toformat).splitlines()
            if end:
                res += end
            result.append((indent, res))
        for itemindent, item in content:
            if itemindent == -1:
                toformat.append(item)
            else:
                do_format()
                result.append((indent + itemindent, item))
                toformat = []
        do_format()
        if first is not None and result:
            itemindent, item = result[0]
            if item:
                result.insert(0, (itemindent - indent, [first + item[0]]))
                result[1] = (itemindent, item[1:])
        self.states[-1].extend(result)

    def visit_document(self, node):
        # print node
        self.new_state(0)
    def depart_document(self, node):
        self.end_state()
        self.body = self.nl.join(line and (' '*indent + line)
                                 for indent, lines in self.states[0]
                                 for line in lines)
        # XXX header/footer?

    def visit_highlightlang(self, node):
        raise nodes.SkipNode

    def visit_section(self, node):
        self._title_char = self.sectionchars[self.sectionlevel]
        self.sectionlevel += 1
    def depart_section(self, node):
        self.sectionlevel -= 1

    def visit_topic(self, node):
        self.new_state(0)
    def depart_topic(self, node):
        self.end_state()

    visit_sidebar = visit_topic
    depart_sidebar = depart_topic

    def visit_rubric(self, node):
        self.new_state(0)
        self.add_text('-[ ')
    def depart_rubric(self, node):
        self.add_text(' ]-')
        self.end_state()

    def visit_compound(self, node):
        # print "visit_compound(%s)" % (node)
        pass
    def depart_compound(self, node):
        pass

    def visit_glossary(self, node):
        # print "visit_glossary(%s)" % (node)
        pass
    def depart_glossary(self, node):
        pass

    def visit_title(self, node):
        if isinstance(node.parent, nodes.Admonition):
            self.add_text(node.astext()+': ')
            raise nodes.SkipNode
        self.new_state(0)
    def depart_title(self, node):
        if isinstance(node.parent, nodes.section):
            char = self._title_char
        else:
            char = '^'
        text = ''.join(x[1] for x in self.states.pop() if x[0] == -1)
        self.stateindent.pop()
        self.states[-1].append((0, ['', text, '%s' % (char * len(text)), '']))

    def visit_subtitle(self, node):
        # print "visit_subtitle(%s)" % (node)
        pass
    def depart_subtitle(self, node):
        pass

    def visit_attribution(self, node):
        self.add_text('-- ')
    def depart_attribution(self, node):
        pass

    def visit_desc(self, node):
        self.new_state(0)
    def depart_desc(self, node):
        self.end_state()

    def visit_desc_signature(self, node):
        if node.parent['objtype'] in ('class', 'exception', 'method', 'function'):
            self.add_text('**')
        else:
            self.add_text('``')
    def depart_desc_signature(self, node):
        if node.parent['objtype'] in ('class', 'exception', 'method', 'function'):
            self.add_text('**')
        else:
            self.add_text('``')

    def visit_desc_name(self, node):
        # print "visit_desc_name(%s)" % (node)
        pass
    def depart_desc_name(self, node):
        pass

    def visit_desc_addname(self, node):
        # print "visit_desc_addname(%s)" % (node)
        pass
    def depart_desc_addname(self, node):
        pass

    def visit_desc_type(self, node):
        # print "visit_desc_type(%s)" % (node)
        pass
    def depart_desc_type(self, node):
        pass

    def visit_desc_returns(self, node):
        self.add_text(' -> ')
    def depart_desc_returns(self, node):
        pass

    def visit_desc_parameterlist(self, node):
        self.add_text('(')
        self.first_param = 1
    def depart_desc_parameterlist(self, node):
        self.add_text(')')

    def visit_desc_parameter(self, node):
        if not self.first_param:
            self.add_text(', ')
        else:
            self.first_param = 0
        self.add_text(node.astext())
        raise nodes.SkipNode

    def visit_desc_optional(self, node):
        self.add_text('[')
    def depart_desc_optional(self, node):
        self.add_text(']')

    def visit_desc_annotation(self, node):
        content = node.astext()
        if len(content) > MAXWIDTH:
            h = int(MAXWIDTH/3)
            content = content[:h] + " ... " + content[-h:]
            self.add_text(content)
            raise nodes.SkipNode
    def depart_desc_annotation(self, node):
        pass

    def visit_refcount(self, node):
        pass
    def depart_refcount(self, node):
        pass

    def visit_desc_content(self, node):
        self.new_state()
    def depart_desc_content(self, node):
        self.end_state()

    def visit_figure(self, node):
        self.new_state()
    def depart_figure(self, node):
        self.end_state()

    def visit_caption(self, node):
        # print "visit_caption(%s)" % (node)
        pass
    def depart_caption(self, node):
        pass

    def visit_productionlist(self, node):
        self.new_state()
        names = []
        for production in node:
            names.append(production['tokenname'])
        maxlen = max(len(name) for name in names)
        for production in node:
            if production['tokenname']:
                self.add_text(production['tokenname'].ljust(maxlen) + ' ::=')
                lastname = production['tokenname']
            else:
                self.add_text('%s    ' % (' '*len(lastname)))
            self.add_text(production.astext() + self.nl)
        self.end_state(wrap=False)
        raise nodes.SkipNode

    def visit_seealso(self, node):
        self.new_state()
    def depart_seealso(self, node):
        self.end_state(first='')

    def visit_footnote(self, node):
        self._footnote = node.children[0].astext().strip()
        self.new_state(len(self._footnote) + 3)
    def depart_footnote(self, node):
        self.end_state(first='[%s] ' % self._footnote)

    def visit_citation(self, node):
        if len(node) and isinstance(node[0], nodes.label):
            self._citlabel = node[0].astext()
        else:
            self._citlabel = ''
        self.new_state(len(self._citlabel) + 3)
    def depart_citation(self, node):
        self.end_state(first='[%s] ' % self._citlabel)

    def visit_label(self, node):
        raise nodes.SkipNode

    # XXX: option list could use some better styling

    def visit_option_list(self, node):
        # print "visit_option_list(%s)" % (node)
        pass
    def depart_option_list(self, node):
        pass

    def visit_option_list_item(self, node):
        self.new_state(0)
    def depart_option_list_item(self, node):
        self.end_state()

    def visit_option_group(self, node):
        self._firstoption = True
    def depart_option_group(self, node):
        self.add_text('     ')

    def visit_option(self, node):
        if self._firstoption:
            self._firstoption = False
        else:
            self.add_text(', ')
    def depart_option(self, node):
        pass

    def visit_option_string(self, node):
        # print "visit_option_string(%s)" % (node)
        pass
    def depart_option_string(self, node):
        pass

    def visit_option_argument(self, node):
        self.add_text(node['delimiter'])
    def depart_option_argument(self, node):
        pass

    def visit_description(self, node):
        # print "visit_description(%s)" % (node)
        pass
    def depart_description(self, node):
        pass

    def visit_tabular_col_spec(self, node):
        raise nodes.SkipNode

    def visit_colspec(self, node):
        self.table[0].append(node['colwidth'])
        raise nodes.SkipNode

    def visit_tgroup(self, node):
        # print "visit_tgroup(%s)" % (node)
        pass
    def depart_tgroup(self, node):
        pass

    def visit_thead(self, node):
        # print "visit_thead(%s)" % (node)
        pass
    def depart_thead(self, node):
        pass

    def visit_tbody(self, node):
        self.table.append('sep')
    def depart_tbody(self, node):
        pass

    def visit_row(self, node):
        self.table.append([])
    def depart_row(self, node):
        pass

    def visit_entry(self, node):
        if node.has_key('morerows') or node.has_key('morecols'):
            raise NotImplementedError('Column or row spanning cells are '
                                      'not implemented.')
        self.new_state(0)
    def depart_entry(self, node):
        text = self.nl.join(self.nl.join(x[1]) for x in self.states.pop())
        self.stateindent.pop()
        self.table[-1].append(text)

    def visit_table(self, node):
        if self.table:
            raise NotImplementedError('Nested tables are not supported.')
        self.new_state(0)
        self.table = [[]]
    def depart_table(self, node):
        lines = self.table[1:]
        fmted_rows = []
        colwidths = self.table[0]
        realwidths = colwidths[:]
        separator = 0
        # don't allow paragraphs in table cells for now
        for line in lines:
            if line == 'sep':
                separator = len(fmted_rows)
            else:
                cells = []
                for i, cell in enumerate(line):
                    par = self.wrap(cell, width=colwidths[i])
                    if par:
                        maxwidth = max(map(len, par))
                    else:
                        maxwidth = 0
                    realwidths[i] = max(realwidths[i], maxwidth)
                    cells.append(par)
                fmted_rows.append(cells)

        def writesep(char='-'):
            out = ['+']
            for width in realwidths:
                out.append(char * (width+2))
                out.append('+')
            self.add_text(''.join(out) + self.nl)

        def writerow(row):
            lines = zip(*row)
            for line in lines:
                out = ['|']
                for i, cell in enumerate(line):
                    if cell:
                        out.append(' ' + cell.ljust(realwidths[i]+1))
                    else:
                        out.append(' ' * (realwidths[i] + 2))
                    out.append('|')
                self.add_text(''.join(out) + self.nl)

        for i, row in enumerate(fmted_rows):
            if separator and i == separator:
                writesep('=')
            else:
                writesep('-')
            writerow(row)
        writesep('-')
        self.table = None
        self.end_state(wrap=False)

    def visit_acks(self, node):
        self.new_state(0)
        self.add_text(', '.join(n.astext() for n in node.children[0].children)
                      + '.')
        self.end_state()
        raise nodes.SkipNode

    def visit_image(self, node):
        if 'alt' in node.attributes:
            self.add_text(_('[image: %s]') % node['alt'])
        self.add_text(_('[image]'))
        raise nodes.SkipNode

    def visit_transition(self, node):
        indent = sum(self.stateindent)
        self.new_state(0)
        self.add_text('=' * (MAXWIDTH - indent))
        self.end_state()
        raise nodes.SkipNode

    def visit_bullet_list(self, node):
        self.list_counter.append(-1)
    def depart_bullet_list(self, node):
        self.list_counter.pop()

    def visit_enumerated_list(self, node):
        self.list_counter.append(0)
    def depart_enumerated_list(self, node):
        self.list_counter.pop()

    def visit_definition_list(self, node):
        self.list_counter.append(-2)
    def depart_definition_list(self, node):
        self.list_counter.pop()

    def visit_list_item(self, node):
        if self.list_counter[-1] == -1:
            # bullet list
            self.new_state(2)
        elif self.list_counter[-1] == -2:
            # definition list
            pass
        else:
            # enumerated list
            self.list_counter[-1] += 1
            self.new_state(len(str(self.list_counter[-1])) + 2)
    def depart_list_item(self, node):
        if self.list_counter[-1] == -1:
            self.end_state(first='* ', end=None)
        elif self.list_counter[-1] == -2:
            pass
        else:
            self.end_state(first='%s. ' % self.list_counter[-1], end=None)

    def visit_definition_list_item(self, node):
        self._li_has_classifier = len(node) >= 2 and \
                                  isinstance(node[1], nodes.classifier)
    def depart_definition_list_item(self, node):
        pass

    def visit_term(self, node):
        self.new_state(0)
    def depart_term(self, node):
        if not self._li_has_classifier:
            self.end_state(end=None)

    def visit_termsep(self, node):
        self.add_text(', ')
        raise nodes.SkipNode

    def visit_classifier(self, node):
        self.add_text(' : ')
    def depart_classifier(self, node):
        self.end_state(end=None)

    def visit_definition(self, node):
        self.new_state()
    def depart_definition(self, node):
        self.end_state()

    def visit_field_list(self, node):
        # print "visit_field_list(%s)" % (node)
        pass
    def depart_field_list(self, node):
        pass

    def visit_field(self, node):
        # print "visit_field(%s)" % (node)
        self.new_state(0)
    def depart_field(self, node):
        self.end_state(end=None)

    def visit_field_name(self, node):
        self.add_text(':')
    def depart_field_name(self, node):
        self.add_text(':')
        content = node.astext()
        self.add_text((16-len(content))*' ')

    def visit_field_body(self, node):
        self.new_state()
    def depart_field_body(self, node):
        self.end_state()

    def visit_centered(self, node):
        pass
    def depart_centered(self, node):
        pass

    def visit_hlist(self, node):
        # print "visit_hlist(%s)" % (node)
        pass
    def depart_hlist(self, node):
        pass

    def visit_hlistcol(self, node):
        # print "visit_hlistcol(%s)" % (node)
        pass
    def depart_hlistcol(self, node):
        pass

    def visit_admonition(self, node):
        self.new_state(0)
    def depart_admonition(self, node):
        self.end_state()

    def _visit_admonition(self, node):
        self.new_state(2)
    def _make_depart_admonition(name):
        def depart_admonition(self, node):
            self.end_state(first=admonitionlabels[name] + ': ')
        return depart_admonition

    visit_attention = _visit_admonition
    depart_attention = _make_depart_admonition('attention')
    visit_caution = _visit_admonition
    depart_caution = _make_depart_admonition('caution')
    visit_danger = _visit_admonition
    depart_danger = _make_depart_admonition('danger')
    visit_error = _visit_admonition
    depart_error = _make_depart_admonition('error')
    visit_hint = _visit_admonition
    depart_hint = _make_depart_admonition('hint')
    visit_important = _visit_admonition
    depart_important = _make_depart_admonition('important')
    visit_note = _visit_admonition
    depart_note = _make_depart_admonition('note')
    visit_tip = _visit_admonition
    depart_tip = _make_depart_admonition('tip')
    visit_warning = _visit_admonition
    depart_warning = _make_depart_admonition('warning')

    def visit_versionmodified(self, node):
        self.new_state(0)
        if node.children:
            self.add_text(versionlabels[node['type']] % node['version'] + ': ')
        else:
            self.add_text(versionlabels[node['type']] % node['version'] + '.')
    def depart_versionmodified(self, node):
        self.end_state()

    def visit_literal_block(self, node):
        self.add_text("::")
        self.new_state()
    def depart_literal_block(self, node):
        self.end_state(wrap=False)

    def visit_doctest_block(self, node):
        self.new_state(0)
    def depart_doctest_block(self, node):
        self.end_state(wrap=False)

    def visit_line_block(self, node):
        self.new_state(0)
    def depart_line_block(self, node):
        self.end_state(wrap=False)

    def visit_line(self, node):
        # print "visit_line(%s)" % (node)
        pass
    def depart_line(self, node):
        pass

    def visit_block_quote(self, node):
        self.add_text('..')
        self.new_state()
    def depart_block_quote(self, node):
        self.end_state()

    def visit_compact_paragraph(self, node):
        pass
    def depart_compact_paragraph(self, node):
        pass

    def visit_paragraph(self, node):
        if not isinstance(node.parent, nodes.Admonition) or \
               isinstance(node.parent, addnodes.seealso):
            self.new_state(0)
    def depart_paragraph(self, node):
        if not isinstance(node.parent, nodes.Admonition) or \
               isinstance(node.parent, addnodes.seealso):
            self.end_state()

    def visit_target(self, node):
        if 'refid' in node:
            self.new_state(0)
            self.add_text('.. _'+node['refid']+':'+self.nl)
    def depart_target(self, node):
        if 'refid' in node:
            self.end_state(wrap=False)

    def visit_index(self, node):
        raise nodes.SkipNode

    def visit_substitution_definition(self, node):
        raise nodes.SkipNode

    def visit_pending_xref(self, node):
        pass
    def depart_pending_xref(self, node):
        pass

    def visit_reference(self, node):
        if 'refuri' not in node:
            pass # Don't add these anchors
        elif 'internal' not in node:
            pass # Don't add external links (they are automatically added by the reST spec)
        elif 'reftitle' in node:
            # Include node as text, rather than with markup.
            # reST seems unable to parse a construct like ` ``literal`` <url>`_
            # Hence we revert to the more simple `literal <url>`_
            self.add_text('`%s <%s>`_' % (node.astext(), node['refuri']))
            # self.end_state(wrap=False)
            raise nodes.SkipNode
        else:
            self.add_text('`%s <%s>`_' % (node.astext(), node['refuri']))
            raise nodes.SkipNode
            
    def depart_reference(self, node):
        if 'refuri' not in node:
            pass # Don't add these anchors
        elif 'internal' not in node:
            pass # Don't add external links (they are automatically added by the reST spec)
        elif 'reftitle' in node:
            pass

    def visit_download_reference(self, node):
        print "visit_download_reference(%s)" % (node)
        pass
    def depart_download_reference(self, node):
        pass

    def visit_emphasis(self, node):
        self.add_text('*')
    def depart_emphasis(self, node):
        self.add_text('*')

    def visit_literal_emphasis(self, node):
        self.add_text('*')
    def depart_literal_emphasis(self, node):
        self.add_text('*')

    def visit_strong(self, node):
        self.add_text('**')
    def depart_strong(self, node):
        self.add_text('**')

    def visit_abbreviation(self, node):
        self.add_text('')
    def depart_abbreviation(self, node):
        if node.hasattr('explanation'):
            self.add_text(' (%s)' % node['explanation'])

    def visit_title_reference(self, node):
        print "visit_title_reference(%s)" % (node)
        self.add_text('*')
    def depart_title_reference(self, node):
        self.add_text('*')

    def visit_literal(self, node):
        self.add_text('``')
    def depart_literal(self, node):
        self.add_text('``')

    def visit_subscript(self, node):
        self.add_text('_')
    def depart_subscript(self, node):
        pass

    def visit_superscript(self, node):
        self.add_text('^')
    def depart_superscript(self, node):
        pass

    def visit_footnote_reference(self, node):
        self.add_text('[%s]' % node.astext())
        raise nodes.SkipNode

    def visit_citation_reference(self, node):
        self.add_text('[%s]' % node.astext())
        raise nodes.SkipNode

    def visit_Text(self, node):
        self.add_text(node.astext())
    def depart_Text(self, node):
        pass

    def visit_generated(self, node):
        # print "visit_generated(%s)" % (node)
        pass
    def depart_generated(self, node):
        pass

    def visit_inline(self, node):
        # print "visit_inline(%s)" % (node)
        pass
    def depart_inline(self, node):
        pass

    def visit_problematic(self, node):
        self.add_text('>>')
    def depart_problematic(self, node):
        self.add_text('<<')

    def visit_system_message(self, node):
        self.new_state(0)
        self.add_text('<SYSTEM MESSAGE: %s>' % node.astext())
        self.end_state()
        raise nodes.SkipNode

    def visit_comment(self, node):
        raise nodes.SkipNode

    def visit_meta(self, node):
        # only valid for HTML
        raise nodes.SkipNode

    def visit_raw(self, node):
        if 'text' in node.get('format', '').split():
            self.body.append(node.astext())
        raise nodes.SkipNode

    def unknown_visit(self, node):
        raise NotImplementedError('Unknown node: ' + node.__class__.__name__)



def setup(app):
    app.require_sphinx('1.0')
    app.add_builder(RstBuilder)
    app.add_config_value('rst_file_suffix', ".rst", False)
    """This is the file name suffix for reST files"""
    app.add_config_value('rst_link_suffix', None, False)
    """The is the suffix used in internal links. By default, takes the same value as rst_file_suffix"""
    app.add_config_value('rst_file_transform', None, False)
    """Function to translate a docname to a filename. By default, returns docname + rst_file_suffix."""
    app.add_config_value('rst_link_transform', None, False)
    """Function to translate a docname to a (partial) URI. By default, returns docname + rst_link_suffix."""

