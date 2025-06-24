#!/usr/bin/env python3
"""
Script de debug para verificar o estado dos alarmes
"""
import time
import requests
import json

def test_alarm_status():
    """Testa o status atual dos alarmes"""
    try:
        # Verificar status dos alarmes
        response = requests.get('http://localhost:5000/api/alarms/status')
        if response.status_code == 200:
            status = response.json()
            print("🔧 Status atual dos alarmes:")
            print(json.dumps(status, indent=2))
        else:
            print(f"❌ Erro ao obter status: {response.status_code}")
            
        # Verificar dados de sensores
        response = requests.get('http://localhost:5000/api/sensor_data')
        if response.status_code == 200:
            data = response.json()
            print("\n📊 Dados atuais dos sensores:")
            print(f"   Temperatura: {data.get('temperature', 'N/A')}°C")
            print(f"   Pressão: {data.get('pressure', 'N/A')} hPa")
            print(f"   Ponto de ebulição: {data.get('boiling_point', 'N/A')}°C")
        else:
            print(f"❌ Erro ao obter dados: {response.status_code}")
            
        # Verificar alarmes ativos
        response = requests.get('http://localhost:5000/api/alarms')
        if response.status_code == 200:
            alarms = response.json()
            print(f"\n🚨 Alarmes ativos: {len(alarms) if isinstance(alarms, list) else 'Formato inválido'}")
            if isinstance(alarms, list):
                for alarm in alarms:
                    print(f"   - {alarm.get('type', 'UNKNOWN')}: {alarm.get('message', 'No message')}")
            else:
                print(f"   Response: {alarms}")
        else:
            print(f"❌ Erro ao obter alarmes: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Erro na conexão: {e}")

def configure_temperature_alarm():
    """Configura um alarme de temperatura baixo para teste"""
    try:        # Primeiro, obter a temperatura atual
        response = requests.get('http://localhost:5000/api/sensor_data')
        if response.status_code == 200:
            data = response.json()
            # data.get('temperature') retorna um dict, precisamos pegar o valor correto
            temp_data = data.get('temperature', {})
            if isinstance(temp_data, dict):
                current_temp = temp_data.get('temperature', 30)
            else:
                current_temp = 30
            
            # Configurar alarme de temperatura 5°C abaixo da atual
            test_threshold = current_temp - 5
            
            alarm_config = {
                'mode': 'temperature_only',
                'temperature_threshold': test_threshold,
                'is_active': True
            }
            
            print(f"\n🔧 Configurando alarme de temperatura com threshold: {test_threshold}°C")
            
            response = requests.post('http://localhost:5000/api/alarms/configure', 
                                   json=alarm_config,
                                   headers={'Content-Type': 'application/json'})
            
            if response.status_code == 200:
                print("✅ Alarme configurado com sucesso!")
                return True
            else:
                print(f"❌ Erro ao configurar alarme: {response.status_code}")
                print(f"Response: {response.text}")
                return False
        else:
            print(f"❌ Erro ao obter temperatura atual: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao configurar alarme: {e}")
        return False

if __name__ == "__main__":
    print("🔍 DIAGNÓSTICO DO SISTEMA DE ALARMES")
    print("=" * 50)
    
    # 1. Verificar status atual
    print("\n1️⃣ Status atual:")
    test_alarm_status()
    
    # 2. Configurar alarme de teste
    print("\n2️⃣ Configurando alarme de teste:")
    if configure_temperature_alarm():
        print("⏳ Aguardando 10 segundos para verificar se o alarme dispara...")
        time.sleep(10)
        
        print("\n3️⃣ Verificando se alarme disparou:")
        test_alarm_status()
