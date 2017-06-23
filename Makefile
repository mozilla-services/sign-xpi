clean:
	rm -fr venv lambda.zip ami-built-lambda.zip

virtualenv:
	virtualenv venv --python=python2.7
	venv/bin/pip install -r aws_lambda/requirements.txt

zip: clean virtualenv
	zip lambda.zip aws_lambda/sign_xpi.py aws_lambda/__init__.py
	pushd venv/lib/python2.7/site-packages/; zip -r ../../../../lambda.zip *; popd
	pushd venv/lib64/python2.7/site-packages/; zip -r ../../../../lambda.zip *; popd

build_image:
	docker build -t sign-xpi .

get_zip: build_image
	docker rm sign-xpi || true
	docker run --name sign-xpi sign-xpi
	docker cp sign-xpi:/app/lambda.zip .
