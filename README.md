# 🌡️ Smart Food Thermometer - Sistema IoT Inteligente

Sistema completo de monitoramento de temperatura para alimentos com sensores inteligentes, alarmes personalizáveis e interface web responsiva.

## 🚀 Execução Rápida

```bash
# 1. Ativar ambiente virtual (se necessário)
.venv\Scripts\activate

# 2. Instalar dependências
pip install -r requirements.txt

# 3. Iniciar sistema
python src/web_app.py
```

**Acesse:** http://localhost:5000

## 📋 Índice

- [🏗️ Arquitetura do Sistema](#️-arquitetura-do-sistema)
- [🔧 Instalação e Configuração](#-instalação-e-configuração)
- [🌐 Interface Web](#-interface-web)
- [📡 API REST](#-api-rest)
- [📨 Tópicos MQTT](#-tópicos-mqtt)
- [🚨 Sistema de Alarmes](#-sistema-de-alarmes)
- [🛠️ Troubleshooting](#️-troubleshooting)

## 🏗️ Arquitetura do Sistema

```
Smart Food Thermometer/
├── src/
│   ├── web_app.py                           # 🌐 Aplicação Flask principal
│   ├── smart_alarm_manager.py               # 🚨 Sistema de alarmes inteligente
│   ├── simple_temperature_sensor_precision.py # 🌡️ Sensor de temperatura preciso
│   ├── pressure_sensor.py                  # 📊 Sensor de pressão
│   ├── mqtt_client.py                     # 📡 Cliente MQTT
│   └── config.py                          # ⚙️ Configurações do sistema
├── frontend/                              # 🎨 Interface web
│   ├── index.html                         # 📄 Página principal
│   ├── css/                              # 🎨 Estilos
│   └── js/                               # ⚡ Scripts JavaScript
└── README.md                             # 📖 Documentação
```

### 🔄 Fluxo de Dados

```
Sensores → web_app.py → Processamento → Alarmes → MQTT/Web Interface
```

1. **Sensores** coletam dados de temperatura e pressão independentemente
2. **web_app.py** centraliza coleta via thread `collect_sensor_data()` (a cada 3 segundos)
3. **Algoritmo inteligente** calcula ponto de ebulição baseado na pressão
4. **Sistema de alarmes** monitora condições personalizáveis
5. **MQTT Client** publica dados processados (temperatura + pressão) automaticamente
6. **Interface web** exibe dados em tempo real via WebSocket/AJAX

### 📡 Integração MQTT

- **Sensor de Temperatura**: Dados publicados via `mqtt_client.publish_temperature_data()`
- **Sensor de Pressão**: Dados publicados via `mqtt_client.publish_pressure_data()`  
- **Alarmes**: Notificações via `mqtt_client.publish_alarm_data()`
- **Centralização**: Toda publicação MQTT feita pelo `web_app.py`

## 🔧 Instalação e Configuração

### 📋 Pré-requisitos

- Python 3.8+
- pip
- Conexão com internet (para MQTT)

### 🛠️ Instalação

```bash
# Clone o repositório
git clone <repository-url>
cd smart-food-thermometer

# Crie ambiente virtual
python -m venv .venv

# Ative o ambiente virtual
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# Instale dependências
pip install -r requirements.txt
```

### ⚙️ Configuração

As configurações principais estão em `src/config.py`:

```python
# Configurações MQTT
MQTT_BROKER = "test.mosquitto.org"
MQTT_PORT = 1883

# Configurações do dispositivo
DEVICE_ID = "smart_thermometer_001"
DEVICE_NAME = "Smart Food Thermometer"

# Intervalos de atualização
SENSOR_UPDATE_INTERVAL = 3  # segundos
```

## 🌐 Interface Web

### 📊 Dashboard Principal

Acesse `http://localhost:5000` para visualizar:

- **Temperatura atual** em tempo real
- **Pressão atmosférica** 
- **Ponto de ebulição** calculado automaticamente
- **Status dos alarmes** ativos
- **Controles do sistema** (iniciar/parar aquecimento)
- **Configuração de alarmes** personalizáveis

### 🎛️ Controles Disponíveis

- **🔥 Start System**: Inicia aquecimento
- **🛑 Stop System**: Para aquecimento
- **🚨 Configure Alarms**: Configura alarmes personalizados
- **🧹 Clear Alarms**: Limpa todos os alarmes

## 📡 API REST

### 🌡️ Dados dos Sensores

```http
GET /api/sensor_data
```

**Resposta:**
```json
{
  "temperature": {
    "temperature": 22.5,
    "unit": "celsius",
    "sensor_id": "smart_thermometer_001",
    "is_heating": false,
    "heating_power": 0.0,
    "status": "stable",
    "timestamp": 1750449326.219
  },
  "pressure": {
    "pressure": 1.013,
    "unit": "bar",
    "altitude": 0,
    "sensor_id": "web_pressure_sensor"
  },
  "boiling_point": 100.0,
  "timestamp": "2025-06-20T16:55:26.219"
}
```

### 🚨 Sistema de Alarmes

#### Obter Status dos Alarmes
```http
GET /api/alarms
```

#### Configurar Alarme
```http
POST /api/alarms/configure
Content-Type: application/json

{
  "mode": "temperature_only",
  "threshold": 85.0
}
```

#### Modos de Alarme Disponíveis

1. **`temperature_only`**: Alarme por temperatura
   ```json
   {
     "mode": "temperature_only",
     "threshold": 85.0
   }
   ```

2. **`time_only`**: Alarme por tempo (Feature Futura)
   ```json
   {
     "mode": "time_only", 
     "duration": 300
   }
   ```

3. **`boiling_only`**: Alarme por ebulição
   ```json
   {
     "mode": "boiling_only",
     "offset": 0.0
   }
   ```

4. **`boiling_then_time`**: Aguarda ebulição, depois conta tempo (Feature Futura)
   ```json
   {
     "mode": "boiling_then_time",
     "offset": 0.0,
     "duration": 600
   }
   ```

#### Limpar Alarmes
```http
POST /api/alarms/clear
```

### 🎛️ Controle do Sistema

#### Iniciar Sistema
```http
POST /api/system/start
```

#### Parar Sistema  
```http
POST /api/system/stop
```

#### Status do Sistema
```http
GET /api/system/status
```

## 📨 Tópicos MQTT

### 📡 Broker

- **Host**: `test.mosquitto.org`
- **Porta**: `1883`
- **Cliente ID**: `web_dashboard`

### 📨 Tópicos de Publicação

```
# Dados de temperatura
smart_thermometer/data/smart_thermometer_001/temperature

# Dados de pressão  
smart_thermometer/data/smart_thermometer_001/pressure

# Alarmes disparados
smart_thermometer/alarms/smart_thermometer_001
```

### 📬 Tópicos de Subscrição

```
# Configurações do dispositivo
smart_thermometer/config/smart_thermometer_001

# Comandos de controle específicos
smart_thermometer/control/smart_thermometer_001

# Comandos para todos os dispositivos
smart_thermometer/control/all
```

### 📋 Exemplos de Payloads

#### Dados de Temperatura
```json
{
  "device_id": "smart_thermometer_001",
  "temperature": 22.5,
  "unit": "celsius",
  "is_heating": false,
  "heating_power": 0.0,
  "timestamp": 1750449326.219
}
```

#### Dados de Pressão
```json
{
  "device_id": "web_pressure_sensor",
  "timestamp": "2024-01-20T15:30:45.123456",
  "pressure": 1.0135,
  "pressure_unit": "atm",
  "altitude_meters": 0.0,
  "estimated_altitude": -112.5,
  "sensor_status": "active",
  "weather_trend": 0.0
}
```

#### Alarme Disparado
```json
{
  "id": "temperature_1750449326247",
  "type": "TEMPERATURE", 
  "message": "🌡️ Temperatura atingiu 85.5°C (limite: 85.0°C)",
  "priority": "HIGH",
  "timestamp": 1750449326.247,
  "current_value": 85.5,
  "threshold": 85.0
}
```

## 🚨 Sistema de Alarmes

### 🧠 Algoritmo Inteligente

- **Cooldown**: 3 segundos entre alarmes do mesmo tipo
- **Persistência**: Alarmes mantidos até serem limpos
- **Prioridades**: CRITICAL para ebulição, HIGH para temperatura/tempo
- **Som**: Beep automático quando alarme dispara

### 📋 Classes de Alarmes

#### 🌡️ PrecisionTemperatureSensor
- `get_data(pressure=None)`: Dados completos do sensor
- `set_target_temperature(temp)`: Define temperatura alvo
- `start_system()`: Inicia aquecimento
- `set_heating(enable)`: Liga/desliga aquecimento

#### 🚨 SmartAlarmManager
- `configure_alarm(mode, **kwargs)`: Configura alarmes
- `check_alarms(temp_data, pressure_data, boiling_point)`: Verifica condições
- `get_status()`: Status completo dos alarmes
- `clear_all_alarms()`: Limpa todos os alarmes

#### 📊 PressureSensor
- `get_sensor_data()`: Dados de pressão e altitude
- `set_altitude(altitude)`: Define altitude manualmente

#### 📡 MQTTClient  
- `publish_temperature_data(data)`: Publica dados de temperatura
- `publish_pressure_data(data)`: Publica dados de pressão  
- `publish_alarm_data(alarm)`: Publica alarmes
- `is_connected`: Status da conexão

### 🔄 Integração MQTT dos Sensores

- **Sensor de Temperatura**: Integração direta via `publish_temperature_data()`
- **Sensor de Pressão**: Integração indireta via `web_app.py` usando `publish_pressure_data()`
- **Alarmes**: Publicação automática via `SmartAlarmManager` quando disparados
- **Frequência**: Dados publicados a cada 3 segundos durante coleta ativa

## 🛠️ Troubleshooting

### ❌ Problemas Comuns

#### "Porta 5000 já está em uso"
```bash
# Verificar processos usando a porta
netstat -ano | findstr :5000

# Encerrar processos Python
taskkill /F /IM python.exe
```

#### "MQTT connection failed"
- Verifique conexão com internet
- O broker `test.mosquitto.org` é público e pode ter instabilidade
- Sistema continua funcionando sem MQTT

#### "Module not found"
```bash
# Instalar dependências
pip install flask flask-cors paho-mqtt plotly
```

#### "Template not found"
- Sistema usa arquivos estáticos em `frontend/`
- Verifique se `frontend/index.html` existe

### 🔍 Debug Mode

Para ativar logs detalhados, edite `src/web_app.py`:
```python
app.run(host='localhost', port=5000, debug=True)
```

### 📊 Verificar Status

```bash
# Testar sensor individualmente
python src/simple_temperature_sensor_precision.py

# Testar alarmes
python src/smart_alarm_manager.py

# Verificar APIs
curl http://localhost:5000/api/sensor_data
```

### 🔧 Reset Completo

```bash
# Parar todos os processos
taskkill /F /IM python.exe

# Aguardar 5 segundos
timeout /t 5

# Reiniciar sistema
python src/web_app.py
```

## 📈 Performance

- **Coleta de dados**: 3 segundos
- **Atualização web**: Tempo real via JavaScript
- **MQTT**: Publish automático a cada coleta
- **Alarmes**: Verificação contínua com cooldown

## 🔒 Segurança

- **CORS configurado** para localhost
- **Validação de entrada** nas APIs
- **Error handling** completo
- **Timeouts** em conexões MQTT

## 📝 Logs

Logs são exibidos no console durante execução:
- **INFO**: Operações normais
- **WARNING**: Problemas não críticos (ex: MQTT disconnect)
- **ERROR**: Problemas que requerem atenção

---

## 📞 Suporte

Sistema desenvolvido e testado para o curso de **Dispositivos Conectados**.

**Status**: ✅ **TOTALMENTE FUNCIONAL**
**Última atualização**: 21 de Junho de 2025

### 🎯 Recursos Implementados
- ✅ Interface web responsiva
- ✅ Sistema de sensores simulados realistas
- ✅ 4 modos de alarmes inteligentes
- ✅ Comunicação MQTT completa
- ✅ API REST documentada
- ✅ Cálculo automático do ponto de ebulição
- ✅ Sistema de aquecimento controlável
- ✅ Logs detalhados e troubleshooting
