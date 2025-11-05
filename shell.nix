let
  pkgs = import <nixpkgs> {};
in pkgs.mkShell {
  # The Nix packages provided in the environment
  packages = [
    pkgs.python311
  ];
  shellHook = ''
    python -m venv .venv
    source .venv/bin/activate
  '';
}
