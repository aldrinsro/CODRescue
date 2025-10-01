Param(
  [string]$LocalUrl = "http://localhost:8000",
  [string]$Wrangler = "$env:APPDATA\npm\wrangler.cmd",
  [string]$Cloudflared = "cloudflared",
  [string]$LogFile = "$env:TEMP\cloudflared_quick_tunnel.log",
  [string]$WorkerName = "yz-tunnel-redirect"
)

# Vérifs préalables
if (-not (Get-Command $Cloudflared -ErrorAction SilentlyContinue)) {
  Write-Host "cloudflared introuvable dans le PATH. Renseigne -Cloudflared avec le chemin complet de cloudflared.exe" -ForegroundColor Yellow
  exit 1
}
if (-not (Test-Path $Wrangler)) {
  Write-Host "wrangler introuvable: $Wrangler. Corrige le paramètre -Wrangler (wrangler.cmd)." -ForegroundColor Yellow
  exit 1
}

# 1) Démarre cloudflared en arrière-plan avec log vers fichier
if (Test-Path $LogFile) { Remove-Item $LogFile -Force }
$cfArgs = @("tunnel","--url",$LocalUrl,"--logfile",$LogFile)
$cfProc = Start-Process -FilePath $Cloudflared -ArgumentList $cfArgs -PassThru -WindowStyle Normal

# 2) Attend l’URL trycloudflare dans le log
$regex = 'https://[a-z0-9-]+\.trycloudflare\.com'
$tryUrl = $null
for ($i=0; $i -lt 120; $i++) {
  Start-Sleep -Seconds 1
  if (Test-Path $LogFile) {
    try {
      $txt = Get-Content $LogFile -Raw -ErrorAction Stop
      if ($txt -match $regex) { $tryUrl = $Matches[0]; break }
    } catch { }
  }
}
if (-not $tryUrl) {
  Write-Host "Impossible de détecter l’URL du tunnel. Arrêt." -ForegroundColor Yellow
  if ($cfProc) { $cfProc | Stop-Process -Force }
  exit 1
}

# 3) Met à jour le secret Worker
try {
  $null = $tryUrl | & $Wrangler secret put TUNNEL_URL --name $WorkerName
  Write-Host "Secret TUNNEL_URL mis à jour -> $tryUrl" -ForegroundColor Green
  Write-Host "URL stable: https://yz-tunnel-redirect.yzrescue.workers.dev/" -ForegroundColor Green
} catch {
  Write-Host "Echec de mise à jour du secret TUNNEL_URL. Vérifie wrangler et ton login." -ForegroundColor Red
}

# 4) Suit les logs pour info (Ctrl+C pour quitter le script; le tunnel reste tant que cloudflared tourne)
Write-Host "Tunnel actif (garde cette fenêtre cloudflared ouverte)." -ForegroundColor Cyan
try {
  Get-Content -Path $LogFile -Wait
} finally {
  # Laisser cloudflared vivant, ne pas tuer le process ici
}


