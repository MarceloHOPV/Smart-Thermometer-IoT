#!/usr/bin/env python3
"""
Teste de integração do sistema de alarmes
"""
import sys
import os
sys.path.append('src')

from smart_alarm_manager import SmartAlarmManager

def test_alarm_integration():
    print("🔍 Testando integração do sistema de alarmes...")
    
    # Criar alarm manager
    alarm_manager = SmartAlarmManager()
    alarm_manager.start_monitoring()
    print(f"✅ Monitoring ativo: {alarm_manager.is_monitoring}")
    
    # Configurar alarme de temperatura
    success = alarm_manager.configure_alarm('temperature_only', threshold=80.0)
    print(f"✅ Alarme configurado: {success}")
    
    # Verificar status
    status = alarm_manager.get_status()
    print(f"📊 Status: {status}")
    
    # Simular dados que devem disparar alarme
    temp_data = {'temperature': 95.0}
    pressure_data = {'pressure': 1.0}
    boiling_point = 100.0
    
    print(f"🌡️ Testando com temp: {temp_data['temperature']}°C (limite: 80°C)")
    
    # Verificar alarmes
    triggered = alarm_manager.check_alarms(temp_data, pressure_data, boiling_point)
    print(f"🚨 Alarmes disparados: {len(triggered)}")
    
    if triggered:
        for alarm in triggered:
            print(f"   - {alarm['type']}: {alarm['message']}")
        print("✅ Sistema de alarmes funcionando!")
    else:
        print("❌ Nenhum alarme foi disparado")
        
    return len(triggered) > 0

if __name__ == "__main__":
    test_alarm_integration()
