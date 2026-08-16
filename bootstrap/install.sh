#!/bin/sh
# contextkeel installer — macOS and Linux.
#
#   curl -LsSf https://raw.githubusercontent.com/yasirnabil534/contextkeel/main/bootstrap/install.sh | sh
#
# Requires nothing pre-installed. Non-interactive, idempotent, and quiet:
# at most six lines of output, and never a prompt.
#
# POSIX sh on purpose — /bin/sh is dash on Debian/Ubuntu and bash-isms break
# there. No arrays, no [[ ]], no `local` beyond one word, no process
# substitution.

set -eu

# Install sources, tried in order unless CONTEXTKEEL_REF overrides them.
# PyPI comes first so that publishing the package makes this work with no edit
# here; until then the repository tarball serves. A tarball rather than
# git+https on purpose: git+ would quietly make git a requirement of a tool
# that otherwise installs everything it needs.
PYPI_NAME="contextkeel"
REPO_TARBALL="https://github.com/yasirnabil534/contextkeel/archive/refs/heads/main.tar.gz"
PACKAGE="${CONTEXTKEEL_REF:-}"
PYTHON_MIN="3.11"
BIN_DIR="${HOME}/.local/bin"

say()  { printf '%s\n' "$1"; }
die()  { printf '\n%s\n' "$1" >&2; exit 1; }

have() { command -v "$1" >/dev/null 2>&1; }

# ---------------------------------------------------------------------------
# 1. uv — a standalone binary that needs no Python of its own, and can supply
#    a managed interpreter. Installing it first means we never have to touch
#    the system package manager (no sudo, no locked-down-machine failures).
# ---------------------------------------------------------------------------
ensure_uv() {
  if have uv; then return 0; fi
  say "Setting up (1/3): installing the package manager…"
  if have curl; then
    curl -LsSf https://astral.sh/uv/install.sh | sh >/dev/null 2>&1 || return 1
  elif have wget; then
    wget -qO- https://astral.sh/uv/install.sh | sh >/dev/null 2>&1 || return 1
  else
    die "Need curl or wget to install. Install one, then re-run this command."
  fi
  # The installer drops the shim here; the running shell has not picked it up.
  PATH="${HOME}/.local/bin:${HOME}/.cargo/bin:${PATH}"
  export PATH
  have uv
}

# ---------------------------------------------------------------------------
# 2. Fallback only: if uv could not be installed, try a system Python so the
#    user still ends up with a working tool.
# ---------------------------------------------------------------------------
ensure_system_python() {
  if have python3; then return 0; fi
  say "Setting up: installing Python…"
  if have brew;    then brew install python                       >/dev/null 2>&1 && return 0; fi
  if have apt-get; then sudo apt-get update >/dev/null 2>&1 && sudo apt-get install -y python3 python3-venv python3-pip >/dev/null 2>&1 && return 0; fi
  if have dnf;     then sudo dnf install -y python3 python3-pip    >/dev/null 2>&1 && return 0; fi
  if have pacman;  then sudo pacman -Sy --noconfirm python python-pip >/dev/null 2>&1 && return 0; fi
  if have zypper;  then sudo zypper install -y python3 python3-pip >/dev/null 2>&1 && return 0; fi
  return 1
}

# ---------------------------------------------------------------------------
# 3. Install contextkeel itself.
# ---------------------------------------------------------------------------
try_install() {
  # uv downloads a managed CPython when the host has none new enough, so this
  # works on a machine with no Python at all.
  uv tool install --python "$PYTHON_MIN" --force "$1" >/dev/null 2>&1 && return 0
  uv tool install --force "$1" >/dev/null 2>&1
}

install_tool() {
  if have uv; then
    if [ -n "$PACKAGE" ]; then
      try_install "$PACKAGE"          # explicit override wins outright
      return $?
    fi
    try_install "$PYPI_NAME" && return 0
    try_install "$REPO_TARBALL" && return 0
    return 1
  fi
  ensure_system_python || return 1
  python3 -m pip install --user --upgrade "${PACKAGE:-$REPO_TARBALL}" >/dev/null 2>&1
}

add_to_path() {
  case ":${PATH}:" in
    *":${BIN_DIR}:"*) return 0 ;;
  esac
  PATH="${BIN_DIR}:${PATH}"
  export PATH

  # Persist for future shells; harmless if the line is already there.
  for rc in "${HOME}/.zshrc" "${HOME}/.bashrc" "${HOME}/.profile"; do
    [ -f "$rc" ] || continue
    if ! grep -q '\.local/bin' "$rc" 2>/dev/null; then
      # shellcheck disable=SC2016  # $PATH must stay literal: it is expanded by
      # the user's future shell when the rc file is sourced, not by us now.
      printf '\nexport PATH="%s:$PATH"\n' "$BIN_DIR" >> "$rc"
    fi
  done
}

# ---------------------------------------------------------------------------

main() {
  if have ckeel && [ "${CONTEXTKEEL_FORCE:-0}" != "1" ]; then
    say "Already installed. Updating…"
  else
    ensure_uv || say "Setting up: falling back to a system Python…"
    say "Setting up (2/3): installing contextkeel…"
    install_tool || die "Install failed. See https://github.com/yasirnabil534/contextkeel#what-you-need for the manual steps."
  fi

  add_to_path
  have ckeel || die "Installed, but 'ckeel' is not on PATH yet. Open a new terminal and run: ckeel init"

  say "Setting up (3/3): preparing this project…"
  ckeel init --auto || die "Installed successfully, but setup did not finish. Run: ckeel doctor --fix"

  say ""
  say "Done. Your project is set up — run 'ckeel status' any time."
}

main "$@"
