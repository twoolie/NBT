# Makefile for Sphinx documentation
#

# You can set these variables from the command line.
SPHINXOPTS    =
SPHINXBUILD   = sphinx-build
PAPER         = a4
BUILDDIR      = build

# Internal variables.
ALLSPHINXOPTS   = -d $(BUILDDIR)/doctrees $(SPHINXOPTS) -c . -a .
# the i18n builder cannot share the environment and doctrees with the others
I18NSPHINXOPTS  = $(PAPEROPT_$(PAPER)) $(SPHINXOPTS) .

.PHONY: help clean html dirhtml singlehtml pickle json htmlhelp qthelp devhelp epub latex latexpdf text man changes linkcheck doctest gettext rst

default: wiki

help:
	@echo "Please use \`make <target>' where <target> is one of"
	@echo "  wiki       to make ReST files for the NBT wiki"
	@echo "  rst        to make ReST files"
	@echo "  html       to make standalone HTML files"
	@echo "  epub       to make an epub"
	@echo "  latexpdf   to make LaTeX files and run them through pdflatex"
	@echo "  text       to make text files"

clean:
	-rm -rf $(BUILDDIR)/*

wiki: NBT.wiki
	$(SPHINXBUILD) -b rst $(ALLSPHINXOPTS) NBT.wiki
	@echo
	@echo "Build finished. The message catalogs are in NBT.wiki."

NBT.wiki:
	# Check if there is a symlink "NBT.wiki"
	ls NBT.wiki # Please check out "git clone https://github.com/twoolie/NBT.wiki.git" and make a symlink from here to the checked out directory.

rst:
	$(SPHINXBUILD) -b rst $(ALLSPHINXOPTS) $(BUILDDIR)/rst
	@echo
	@echo "Build finished. The message catalogs are in $(BUILDDIR)/rst."

html:
	$(SPHINXBUILD) -b html $(ALLSPHINXOPTS) $(BUILDDIR)/html
	@echo
	@echo "Build finished. The HTML pages are in $(BUILDDIR)/html."

epub:
	$(SPHINXBUILD) -b epub $(ALLSPHINXOPTS) $(BUILDDIR)/epub
	@echo
	@echo "Build finished. The epub file is in $(BUILDDIR)/epub."

latexpdf:
	$(SPHINXBUILD) -b latex $(ALLSPHINXOPTS) -D latex_paper_size=$(PAPER) $(BUILDDIR)/latex
	@echo "Running LaTeX files through pdflatex..."
	$(MAKE) -C $(BUILDDIR)/latex all-pdf
	@echo "pdflatex finished; the PDF files are in $(BUILDDIR)/latex."

text:
	$(SPHINXBUILD) -b text $(ALLSPHINXOPTS) $(BUILDDIR)/text
	@echo
	@echo "Build finished. The text files are in $(BUILDDIR)/text."

linkcheck:
	$(SPHINXBUILD) -b linkcheck $(ALLSPHINXOPTS) $(BUILDDIR)/linkcheck
	@echo
	@echo "Link check complete; look for any errors in the above output " \
	      "or in $(BUILDDIR)/linkcheck/output.txt."

doctest:
	$(SPHINXBUILD) -b doctest $(ALLSPHINXOPTS) $(BUILDDIR)/doctest
	@echo "Testing of doctests in the sources finished, look at the " \
	      "results in $(BUILDDIR)/doctest/output.txt."
