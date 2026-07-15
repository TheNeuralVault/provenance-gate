#!/data/data/com.termux/files/usr/bin/sh
# Termux:Boot script — auto-start the provenance-gate signing service.
# Runs in NATIVE Termux at device boot; must enter the Ubuntu PRoot (where the
# signer + Python 3.12 live) to launch the service.
#
# Requires the Termux:Boot app installed + granted autostart (F-Droid).

# Keep device awake long enough to start the service.
termux-wake-lock 2>/dev/null

LOG=/data/data/com.termux/files/home/.signer/boot.log
mkdir -p /data/data/com.termux/files/home/.signer
echo "[boot $(date)] starting signer via proot-distro ubuntu" >> "$LOG"

# Launch the signing service inside the PRoot. run_signer.py loops forever
# (holds the Ed25519 private key, serves on ~/.signer/sign.sock).
proot-distro login ubuntu -- bash -lc '
  export HOME=/data/data/com.termux/files/home
  cd "$HOME"
  # Guard: do not start a second instance if the socket is already served.
  if [ -S "$HOME/.signer/sign.sock" ] && \
     python "$HOME/.signer/healthcheck.py" >/dev/null 2>&1; then
    echo "[boot] signer already healthy, skipping"
    exit 0
  fi
  rm -f "$HOME/.signer/sign.sock"
  nohup python "$HOME/.signer/run_signer.py" \
    > "$HOME/.signer/service.log" 2>&1 &
  echo "[boot] launched signer pid $!"
  # Also verify provenance-gate at device boot (T1 baseline), so the
  # gate is governed on reboot -- not only when a Hermes session starts.
  if [ -x "$HOME/provenance-gate/hooks/session_verify.sh" ]; then
    bash "$HOME/provenance-gate/hooks/session_verify.sh" \
      >> "$HOME/.signer/boot.log" 2>&1
    echo "[boot] gate verify exit=$?"
  else
    echo "[boot] gate session_verify.sh missing/not executable -- skipping verify"
  fi
' >> "$LOG" 2>&1

echo "[boot $(date)] done" >> "$LOG"
