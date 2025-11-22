{ pkgs ? import <nixpkgs> {} }:

let
  # the command used to generate the python-packages.nix file
  # nix run github:nix-community/pip2nix -- generate innertube
  packageOverrides = pkgs.callPackage ./python-packages.nix {};
  python = pkgs.python3.override { inherit packageOverrides; };
in
  pkgs.mkShell {
    packages = with pkgs; [
      (python.withPackages(p: with p; [
        innertube
      ]))
    ];
  }
