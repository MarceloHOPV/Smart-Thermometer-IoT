# Script para Monitorar Temperatura em Tempo Real
# Execute: .\monitor_temp.ps1

Write-Host "=== Monitor de Temperatura IoT Smart Thermometer ===" -ForegroundColor Cyan
Write-Host "Pressione Ctrl+C para parar" -ForegroundColor Yellow
Write-Host ""

while ($true) {
    try {
        $data = Invoke-RestMethod -Uri "http://localhost:5000/api/sensor_data" -ErrorAction Stop
          $temp = [math]::Round($data.temperature.temperature, 1)
        $pressure = [math]::Round($data.pressure.pressure, 3)
        $boiling = [math]::Round($data.boiling_point, 1)
        $heating = if ($data.temperature.is_heating) { "AQUECENDO" } else { "Parado" }
        $timestamp = Get-Date -Format "HH:mm:ss"
        
        # Cores baseadas na temperatura
        $tempColor = if ($temp -lt 50) { "Blue" } 
                    elseif ($temp -lt 80) { "Yellow" } 
                    elseif ($temp -lt 95) { "DarkYellow" } 
                    else { "Red" }
        
        Write-Host "[$timestamp] " -NoNewline -ForegroundColor Gray
        Write-Host "Temp: " -NoNewline
        Write-Host "$temp°C " -NoNewline -ForegroundColor $tempColor
        Write-Host "| Pressão: $pressure atm " -NoNewline
        Write-Host "| Ebulição: $boiling°C " -NoNewline
        Write-Host "| Status: $heating" -ForegroundColor Green
          # Alerta quando próximo da ebulição
        if ($temp -gt ($boiling - 5)) {
            Write-Host "ATENCAO: Próximo ao ponto de ebulição!" -ForegroundColor Red
        }
        
    }    catch {
        Write-Host "ERRO ao conectar com a API: $($_.Exception.Message)" -ForegroundColor Red
    }
    
    Start-Sleep 2
}
