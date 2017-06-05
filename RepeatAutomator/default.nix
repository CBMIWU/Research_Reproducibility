{ pkgs ? import <nixpkgs> { } }:

let
  # Pin a nixpkgs version
  pinned_pkgs = import (pkgs.fetchFromGitHub {
    owner  = "NixOS";
    repo   = "nixpkgs";
    rev    = "17.03";
    sha256 = "1fw9ryrz1qzbaxnjqqf91yxk1pb9hgci0z0pzw53f675almmv9q2";
  }) {};
in with pinned_pkgs; python2Packages.buildPythonApplication rec {
  name = "repeat-automator";

  src = "./.";

  nativeBuildInputs = [
    python2Packages.setuptools # not currently used, but should be
  ];

  propagatedBuildInputs = with python2Packages; [
    beautifulsoup
    pycurl
  ];

  meta = with stdenv.lib; {
    homepage = https://github.com/CBMIWU/Research_Reproducibility;
    description = "A tool for analyzing the reproducibility of EMR studies";
    license = stdenv.lib.licenses.asl20;
    platforms = stdenv.lib.platforms.unix;
    maintainers = [ stdenv.lib.maintainers.siddharthist ];
  };
}
