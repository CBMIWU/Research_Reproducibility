{ pkgs ? import <nixpkgs> { } }:

let
  docx2txt = pkgs.callPackage ./docx2txt.nix { };
in with pkgs.python3Packages; buildPythonPackage rec {
  pname = "textract";
  version = "1.5.0";
  name = "${pname}-${version}";

  src = fetchPypi {
    inherit pname version;
    sha256 = "1mspqi2s2jcib8l11v6n2sqmnw9lgs5rx3nhbncby5zqg4bdswqf";
  };

  propogatedBuildInputs = [
    docx2txt
  ];

  meta = with stdenv.lib; {
    description = "extract text from any document. no muss. no fuss.";
    homepage = "https://pypi.python.org/pypi/textract";
    license = licenses.mit;
  };
}
