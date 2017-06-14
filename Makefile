clean:
	rm -fr venv lambda.zip ami-built-lambda.zip

virtualenv:
	virtualenv venv --python=python2.7
	venv/bin/pip install -r lambda/requirements.txt

zip: clean virtualenv
	zip lambda.zip lambda/sign_xpi.py
	cd venv/lib/python2.7/site-packages/; zip -r ../../../../lambda.zip *
