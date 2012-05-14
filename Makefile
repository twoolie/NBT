PYLINT_FILES= nbt/ examples/ tests/

check:
	pep8 -r --ignore=E501,W191,E101 $(PYLINT_FILES)
	pyflakes $(PYLINT_FILES)
	pylint --output-format=parseable -rn -iy --disable=W0312 --max-line-length=120 --good-names=x,y,z $(PYLINT_FILES)

test:
	python tests/alltests.py
    