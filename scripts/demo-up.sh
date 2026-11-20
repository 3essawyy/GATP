#!/usr/bin/env bash
# GATP demo supervisor (runs INSIDE WSL; normally launched by scripts/demo-up.ps1).
#
# 1. kills anything already on the GATP ports / left over from earlier runs
# 2. starts fixtures, runner, API and web UI, each in its own process group
# 3. waits until every one answers a real health check
# 4. prints READY, then stays in the foreground; Ctrl+C (or closing the window)
#    stops everything cleanly.
#
# Env: GATP_REPO (default ~/GATP), GATP_LLM_PRIMARY (default gemini), GATP_SITE (default v1).
set -u

REPO="${GATP_REPO:-$HOME/GATP}"
export GATP_LLM_PRIMARY="${GATP_LLM_PRIMARY:-gemini}"
SITE="${GATP_SITE:-v1}"
API_PORT=8000
SITE_PORT=8090
WEB_PORT=5173
WAIT_S=120

say() { printf '\033[1;36m[demo]\033[0m %s\n' "$*"; }
die() { printf '\033[1;31m[demo] %s\033[0m\n' "$*" >&2; exit 1; }

[ -d "$REPO" ] || die "repo not found at $REPO (set GATP_REPO)"
cd "$REPO" || die "cannot cd to $REPO"
# A non-interactive shell skips ~/.bashrc, so Node (nvm) is missing and WSL falls back to the
# *Windows* npm via interop (fails with "UNC paths are not supported"). Load nvm, then drop
# every /mnt/* entry from PATH so nothing Windows can be picked up by accident.
export NVM_DIR="${NVM_DIR:-$HOME/.nvm}"
# shellcheck disable=SC1091
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh" >/dev/null 2>&1
export PATH="$HOME/.local/bin:$PATH"
PATH=$(printf '%s' "$PATH" | tr ':' '\n' | grep -v '^/mnt/' | paste -sd:)
export PATH
command -v uv >/dev/null || die "uv not found"
NODE_BIN=$(command -v node || true)
[ -n "$NODE_BIN" ] || die "Linux node not found (install Node 22 with nvm inside WSL)"
case "$NODE_BIN" in /mnt/*) die "node resolves to Windows ($NODE_BIN)";; esac
[ -f .env ] || die ".env missing in $REPO (copy .env.example and add your Gemini key)"
[ -d frontend/node_modules ] || die "frontend deps missing: run 'uv run poe web-install'"

LOGDIR="$REPO/data/logs"
mkdir -p "$LOGDIR"

# ---- 1. clean up -----------------------------------------------------------
kill_port() {  # kill whatever listens on TCP port $1 (SIGTERM, then SIGKILL)
  local pids
  pids=$(ss -ltnpH "sport = :$1" 2>/dev/null | grep -o 'pid=[0-9]*' | cut -d= -f2 | sort -u)
  [ -z "$pids" ] && return 0
  say "port $1 busy (pid $(echo $pids | tr '\n' ' ')): stopping"
  kill $pids 2>/dev/null
  for _ in 1 2 3 4 5 6 7 8 9 10; do
    ss -ltnH "sport = :$1" 2>/dev/null | grep -q . || return 0
    sleep 0.5
  done
  kill -9 $pids 2>/dev/null
  sleep 0.5
}

kill_leftovers() {  # GATP processes that don't hold a port (the runner uses a unix socket)
  # [g] bracket trick + exclude our own pid so the pattern never matches this shell.
  local pids
  pids=$(pgrep -f '[g]atp-runner|[g]atp-api|poe (api|runner|web|fixtures)|fixtures/[s]erve.py' | grep -vx "$$" || true)
  [ -z "$pids" ] && return 0
  say "stopping leftover GATP processes: $(echo $pids | tr '\n' ' ')"
  kill $pids 2>/dev/null
  sleep 1
  kill -9 $pids 2>/dev/null || true
}

# Single instance: a previous supervisor would notice its services dying and tear down the new
# ones, so stop it first (its trap cleans up) and wait until it has really exited.
PIDFILE="$LOGDIR/supervisor.pid"
if [ -f "$PIDFILE" ]; then
  old=$(cat "$PIDFILE" 2>/dev/null || true)
  if [ -n "$old" ] && [ "$old" != "$$" ] && kill -0 "$old" 2>/dev/null; then
    say "stopping previous supervisor (pid $old)"
    kill "$old" 2>/dev/null
    for _ in $(seq 1 20); do kill -0 "$old" 2>/dev/null || break; sleep 0.5; done
    kill -9 "$old" 2>/dev/null || true
  fi
fi
echo "$$" > "$PIDFILE"

say "cleaning up old processes"
kill_leftovers
for p in "$API_PORT" "$SITE_PORT" "$WEB_PORT"; do kill_port "$p"; done
rm -f data/runner/runner.sock
for p in "$API_PORT" "$SITE_PORT" "$WEB_PORT"; do
  ss -ltnH "sport = :$p" 2>/dev/null | grep -q . && die "port $p is still in use; free it by hand (ss -ltnp | grep :$p)"
done

# ---- 2. start --------------------------------------------------------------
PGIDS=()
start() {  # start <name> <command...>: own session so we can kill the whole tree later
  local name="$1"; shift
  : > "$LOGDIR/$name.log"
  setsid "$@" >"$LOGDIR/$name.log" 2>&1 &
  PGIDS+=("$!")
  say "started $name (pid $!, log data/logs/$name.log)"
}

stop_all() {
  trap - EXIT INT TERM
  say "stopping everything"
  for pg in "${PGIDS[@]:-}"; do [ -n "$pg" ] && kill -- "-$pg" 2>/dev/null; done
  sleep 1
  for pg in "${PGIDS[@]:-}"; do [ -n "$pg" ] && kill -9 -- "-$pg" 2>/dev/null; done
  for p in "$API_PORT" "$SITE_PORT" "$WEB_PORT"; do kill_port "$p"; done
  rm -f data/runner/runner.sock
  [ "$(cat "$PIDFILE" 2>/dev/null)" = "$$" ] && rm -f "$PIDFILE"
  exit 0
}
trap stop_all EXIT INT TERM

say "model provider: GATP_LLM_PRIMARY=$GATP_LLM_PRIMARY"
start fixtures uv run poe fixtures "$SITE"
start runner   uv run poe runner
start api      uv run poe api
start web      uv run poe web

# ---- 3. wait for health ----------------------------------------------------
wait_for() {  # wait_for <label> <command...> : poll up to WAIT_S seconds
  local label="$1"; shift
  local waited=0
  until "$@" >/dev/null 2>&1; do
    sleep 1; waited=$((waited + 1))
    if [ "$waited" -ge "$WAIT_S" ]; then
      printf '\033[1;31m[demo] %s did not come up in %ss. Last log lines:\033[0m\n' "$label" "$WAIT_S" >&2
      tail -n 15 "$LOGDIR/${label}.log" >&2
      exit 1
    fi
  done
  say "$label ready"
}

wait_for fixtures curl -fsS "http://127.0.0.1:$SITE_PORT/index.html"
wait_for api      curl -fsS "http://127.0.0.1:$API_PORT/api/health"
wait_for runner   curl -fsS "http://127.0.0.1:$API_PORT/api/runner/health"
wait_for web      curl -fsS "http://127.0.0.1:$WEB_PORT/"

say "READY: UI http://localhost:$WEB_PORT   (Ctrl+C here stops everything; logs in data/logs/)"
# Stay in the foreground; if any child dies, say which one instead of failing silently.
while true; do
  for i in "${!PGIDS[@]}"; do
    if ! kill -0 "${PGIDS[$i]}" 2>/dev/null; then
      die "a service exited (pid ${PGIDS[$i]}); check data/logs/*.log"
    fi
  done
  sleep 3
done
