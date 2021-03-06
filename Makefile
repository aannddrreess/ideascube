# -- Development --------------------------------------------------------------
develop:
	pip3 install --no-use-wheel -r requirements-dev.txt

doc:
	mkdocs serve

dummydata: migrate
	python3 manage.py dummydata
	python3 manage.py reindex

migrate:
	python3 manage.py migrate --database=default
	python3 manage.py migrate --database=transient

upgrade-deps:
	pip-compile --rebuild --header --index --annotate --upgrade requirements.in
	pip-compile --rebuild --header --index --annotate --upgrade requirements-dev.in
	# Remove -e in the requirements.txt.
	# See issue : https://github.com/spotify/dh-virtualenv/issues/200
	sed -i 's/^-e //g' requirements.txt

sync-deps:
	pip-sync requirements-dev.txt


# -- Translations -------------------------------------------------------------
collect_translations:
	python3 manage.py makemessages --all --no-obsolete --ignore=debian -d django
	python3 manage.py makemessages --all --no-obsolete --ignore=debian -d djangojs

push_translations:
	tx push -s

pull_translations:
	tx pull --all --force

compile_translations:
	python3 manage.py compilemessages


# -- Testing ------------------------------------------------------------------
test:
	py.test

testcov:
	py.test --cov=ideascube/ --cov-report=term-missing --migrations

test-data-migration:
	set -e ; \
	BRANCH=$$(git rev-parse --abbrev-ref HEAD); \
	LATEST_TAG=$$(git describe --abbrev=0 --tags); \
	\
	echo "# Loading some data at $$LATEST_TAG"; \
	git checkout $$LATEST_TAG; \
	rm -fr storage; \
	make migrate; \
	python3 manage.py loaddata --database=default test-data/data.json; \
	python3 manage.py reindex; \
	\
	echo "# Running migrations on $$BRANCH"; \
	git checkout $$BRANCH; \
	make migrate
