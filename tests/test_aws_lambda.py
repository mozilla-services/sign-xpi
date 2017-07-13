import io
from aws_lambda import sign_xpi


def test_get_extension_id_rdf_sanity_check():
    simple_rdf = io.StringIO("""<?xml version="1.0" encoding="UTF-8"?>

<RDF xmlns="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
     xmlns:em="http://www.mozilla.org/2004/em-rdf#">
  <Description about="urn:mozilla:install-manifest">
    <em:id>hypothetical-addon@mozilla.org</em:id>
  </Description>
</RDF>""")
    extension_id = sign_xpi.get_extension_id_rdf(simple_rdf)

    assert extension_id == 'hypothetical-addon@mozilla.org'
