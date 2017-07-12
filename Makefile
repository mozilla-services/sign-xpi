VENV=.venv
VENV_DEV=.venv-dev

clean:
	rm -fr venv $(VENV) lambda.zip ami-built-lambda.zip

virtualenv:
	virtualenv $(VENV) --python=python3.6
	$(VENV)/bin/pip install -r aws_lambda/requirements.txt

virtualenv-dev:
	virtualenv $(VENV_DEV) --python=python3.6
	$(VENV_DEV)/bin/pip install -r aws_lambda/requirements.txt
	$(VENV_DEV)/bin/pip install -r requirements_dev.txt

zip: clean virtualenv
	zip lambda.zip aws_lambda/sign_xpi.py aws_lambda/__init__.py
	pushd $(VENV)/lib/python2.7/site-packages/; zip -r ../../../../lambda.zip *; popd
	pushd $(VENV)/lib64/python2.7/site-packages/; zip -r ../../../../lambda.zip *; popd

build_image:
	docker build -t sign-xpi .

get_zip: build_image
	docker rm sign-xpi || true
	docker run --name sign-xpi sign-xpi
	docker cp sign-xpi:/app/lambda.zip .

install-autograph: $(VENV_DEV)/bin/autograph

$(VENV_DEV)/bin/autograph:
	env GOPATH=$(VENV_DEV) go get -u github.com/mozilla-services/autograph

run-autograph: install-autograph
	$(VENV_DEV)/bin/autograph -c $(VENV_DEV)/src/go.mozilla.org/autograph/autograph.yaml
