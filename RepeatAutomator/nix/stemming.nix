{ pkgs ? import <nixpkgs> { } }:

with pkgs.python3Packages; buildPythonPackage rec {
  pname = "stemming";
  version = "1.0.1";
  name = "${pname}-${version}";

  src = pkgs.fetchFromGitHub {
    owner = "siddharthist";
    repo = "${pname}";
    rev = "158e38c9db11d3b9754896a847dcb8708431f12a";
    sha256 = "05wifsbc6gbs31myp43s70h99vfnzg4hhgmkydnlfsrnwlgzjj6l";
  };

  meta = with stdenv.lib; {
    description = "Python implementations of various stemming algorithms.";
    homepage = "https://pypi.python.org/pypi/stemming";
    license = licenses.publicDomain;
  };
}
