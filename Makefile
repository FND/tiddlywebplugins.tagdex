.PHONY: release dist coverage test clean

release: clean test
	git diff --exit-code # ensure there are no uncommitted changes
	git tag -a \
			-m v`python -c 'from setup import META; print META["version"]'` \
			v`python -c 'from setup import META; print META["version"]'`
	git push origin master --tags
	# XXX: duplicates dist target
	rm -r dist || true
	python setup.py sdist upload

dist: clean test
	rm -r dist || true
	python setup.py sdist

coverage: clean
	# option #1: figleaf
	find . test -name "*.py" | grep -v venv > coverage.lst
	figleaf `which py.test` -s test
	figleaf2html -f coverage.lst
	# option #2: coverage
	coverage run `which py.test` -s test
	coverage html --omit="venv/*"
	# reports
	coverage report --omit="venv/*"
	@echo "[INFO] additional reports in \`html/index.html\` (figleaf) and" \
			"\`htmlcov/index.html\` (coverage)"

test: clean
	py.test -s --tb=short test

clean:
	find . -name "*.pyc" -print0 | xargs -0 rm || true
	rm -rf tiddlywebplugins.tagdex.egg-info
	rm -rf html .figleaf coverage.lst # figleaf
	rm -rf htmlcov .coverage # coverage
	rm -rf test/__pycache__ # pytest
