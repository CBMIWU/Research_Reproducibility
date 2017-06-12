{ pkgs ? import <nixpkgs> { } }:

let
  # Pin a nixpkgs version
  # We need later than 17.03 for nltk
  pinned_pkgs = import (pkgs.fetchFromGitHub {
    owner  = "NixOS";
    repo   = "nixpkgs";
    rev    = "b615c2e9929e840e95408b511db7f03dbdd71143";
    sha256 = "17dvjb5k8mrcp9fv3nhzwpj7x70j7mhdq7yb3k8wll19s8sfhb1x";
  }) {};

  stemming = pinned_pkgs.callPackage ./nix/stemming.nix { };
  # textract = pinned_pkgs.callPackage ./nix/textract.nix { };
in with pinned_pkgs; python3Packages.buildPythonApplication rec {
  name = "repeat-automator";

  src = ./.;

  nativeBuildInputs = [
    python3Packages.setuptools # not currently used, but should be
  ];

  propagatedBuildInputs = with python3Packages; [
    beautifulsoup4
    lxml
    nltk
    pycurl
    stemming
    requests
    tkinter
    xpdf # pdftotext
  ];

  meta = with stdenv.lib; {
    homepage = https://github.com/CBMIWU/Research_Reproducibility;
    description = "A tool for analyzing the reproducibility of EMR studies";
    license = stdenv.lib.licenses.asl20;
    platforms = stdenv.lib.platforms.unix;
    maintainers = [ stdenv.lib.maintainers.siddharthist ];
  };
}
