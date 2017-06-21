clean:
	rm -fr venv lambda.zip ami-built-lambda.zip

virtualenv:
	virtualenv venv --python=python2.7
	venv/bin/pip install -r aws_lambda/requirements.txt

zip: clean virtualenv
	zip lambda.zip aws_lambda/sign_xpi.py aws_lambda/__init__.py
	pushd venv/lib/python2.7/site-packages/; zip -r ../../../../lambda.zip *; popd
	pushd venv/lib64/python2.7/site-packages/; zip -r ../../../../lambda.zip *; popd
