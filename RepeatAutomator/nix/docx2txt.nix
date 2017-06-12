{ pkgs ? import <nixpkgs> { } }:

with pkgs.python3Packages; buildPythonPackage rec {
  pname = "docx2txt";
  version = "0.6";
  name = "${pname}-${version}";

  src = fetchPypi {
    inherit pname version;
    sha256 = "0f0kzs5mnphjnv6g21xfsjaj8fs9mgs6s849qnpq7r65fijhqx14";
  };

  meta = with stdenv.lib; {
    description = "A pure python-based utility to extract text and images from docx files.";
    homepage = "https://pypi.python.org/pypi/docx2txt";
    license = licenses.mit;
  };
}
