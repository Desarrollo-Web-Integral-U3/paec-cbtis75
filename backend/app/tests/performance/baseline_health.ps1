$URL = "https://paec-cbtis75-production.up.railway.app/api/v1/health"
$TIMES = @()

for ($i = 1; $i -le 20; $i++) {
    $measure = Measure-Command {
        Invoke-WebRequest -Uri $URL -UseBasicParsing -ErrorAction SilentlyContinue | Out-Null
    }
    $T = [math]::Round($measure.TotalSeconds, 4)
    Write-Host "Iteracion $($i): $T s"
    $TIMES += $T
}

Write-Host "---"
Write-Host "Total: $($TIMES.Length) iteraciones"
