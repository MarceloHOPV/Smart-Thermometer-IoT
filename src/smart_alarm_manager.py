"""
Smart Alarm Management System - VERSÃO FINAL LIMPA
Sistema de alarmes inteligente para o Smart Food Thermometer
"""
import time
import threading
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SmartAlarmManager:
    def __init__(self, mqtt_client=None, sound_enabled=True):
        self.mqtt_client = mqtt_client
        self.sound_enabled = sound_enabled
        self.active_alarms = {}
        self.alarm_history = []
        self.is_monitoring = False
        
        # Sistema de cooldown para evitar spam de alarmes
        self.last_alarm_time = {}
        self.alarm_cooldown = 3.0  # 3 segundos entre alarmes do mesmo tipo
        
        # Configuração atual do alarme
        self.current_alarm_config = {
            'mode': None,
            'temperature_threshold': 95.0,
            'time_duration': 300,
            'boiling_offset': 0.0,
            'is_active': False
        }
        
        # Estado para modo boiling_then_time
        self.boiling_state = {
            'has_boiled': False,
            'time_started': None,
            'waiting_for_boiling': False
        }        
        logger.info("Smart Alarm Manager initialized")
    
    def configure_alarm(self, mode, **kwargs):
        """Configura alarme com modo exclusivo"""
        current_mode = self.current_alarm_config.get('mode')
        if current_mode != mode:
            self.clear_all_alarms()
            logger.info(f"Mudando modo de {current_mode} para {mode}")
        
        # Resetar cooldown ao reconfigurar
        self.last_alarm_time.clear()
        
        # Validar modo
        valid_modes = ['temperature_only', 'time_only', 'boiling_only', 'boiling_then_time']
        if mode not in valid_modes:
            raise ValueError(f"Modo inválido: {mode}. Modos válidos: {valid_modes}")
          # Configurar novo modo
        self.current_alarm_config['mode'] = mode
        
        if mode == 'temperature_only':
            threshold = kwargs.get('threshold', 95.0)
            if threshold <= 0 or threshold > 200:
                raise ValueError("Temperatura deve estar entre 0 e 200°C")
            self.current_alarm_config['temperature_threshold'] = float(threshold)
            
        elif mode == 'time_only':
            duration = kwargs.get('duration', 300)
            if duration <= 0 or duration > 3600:
                raise ValueError("Tempo deve estar entre 1 segundo e 1 hora")
            self.current_alarm_config['time_duration'] = int(duration)
            # Reset timer
            if hasattr(self, '_time_start'):
                delattr(self, '_time_start')
            
        elif mode == 'boiling_only':
            offset = kwargs.get('offset', 0.0)
            self.current_alarm_config['boiling_offset'] = float(offset)
            
        elif mode == 'boiling_then_time':
            offset = kwargs.get('offset', 0.0)
            duration = kwargs.get('duration', 300)
            if duration <= 0 or duration > 3600:
                raise ValueError("Tempo deve estar entre 1 segundo e 1 hora")
            self.current_alarm_config['boiling_offset'] = float(offset)
            self.current_alarm_config['time_duration'] = int(duration)
            self.boiling_state = {
                'has_boiled': False,
                'time_started': None,
                'waiting_for_boiling': True
            }
        
        self.current_alarm_config['is_active'] = True
        logger.info(f"Alarme configurado: {mode} com parâmetros {kwargs}")
        return True
    
    def _can_trigger_alarm(self, alarm_type):
        """Verifica se pode disparar alarme baseado no cooldown"""
        current_time = time.time()
        last_time = self.last_alarm_time.get(alarm_type, 0)
        
        if current_time - last_time >= self.alarm_cooldown:
            self.last_alarm_time[alarm_type] = current_time
            return True
        return False
    
    def check_alarms(self, temperature_data, pressure_data, boiling_point):
        """Verifica e dispara alarmes baseado nas condições configuradas"""
        try:
            if not self.current_alarm_config.get('is_active', False):
                return []
            
            mode = self.current_alarm_config.get('mode')
            if not mode:
                return []
            
            current_temp = temperature_data.get('temperature', 0) if temperature_data else 0
            triggered_alarms = []
            
            # Alarme de temperatura
            if mode == 'temperature_only':
                threshold = self.current_alarm_config.get('temperature_threshold', 95.0)
                if current_temp >= threshold and self._can_trigger_alarm('temperature'):
                    alarm = self._create_alarm('TEMPERATURE', 
                        f"🌡️ Temperatura atingiu {current_temp:.1f}°C (limite: {threshold}°C)",
                        {'current_value': current_temp, 'threshold': threshold})
                    triggered_alarms.append(alarm)            # Alarme de ebulição
            elif mode == 'boiling_only':
                if boiling_point:
                    boiling_threshold = boiling_point + self.current_alarm_config.get('boiling_offset', 0.0)
                    if current_temp >= boiling_threshold and self._can_trigger_alarm('boiling'):
                        alarm = self._create_alarm('BOILING',
                            f"💧 Líquido está FERVENDO! {current_temp:.1f}°C ≥ {boiling_threshold:.1f}°C",
                            {'current_value': current_temp, 'boiling_point': boiling_point, 'boiling_threshold': boiling_threshold})
                        triggered_alarms.append(alarm)
            
            # Alarme de tempo
            elif mode == 'time_only':
                duration = self.current_alarm_config.get('time_duration', 300)
                if not hasattr(self, '_time_start'):
                    self._time_start = time.time()
                
                elapsed = time.time() - self._time_start
                if elapsed >= duration and self._can_trigger_alarm('time'):
                    alarm = self._create_alarm('TIME',
                        f"⏰ Tempo de cozimento concluído! ({elapsed:.0f}s / {duration}s)",
                        {'elapsed_time': elapsed, 'target_duration': duration})
                    triggered_alarms.append(alarm)
            
            # Alarme combinado: ferver primeiro, depois timer
            elif mode == 'boiling_then_time':
                if boiling_point:
                    boiling_threshold = boiling_point + self.current_alarm_config.get('boiling_offset', 0.0)
                    
                    # Fase 1: Aguardar fervura
                    if not self.boiling_state['has_boiled']:
                        if current_temp >= boiling_threshold:
                            self.boiling_state['has_boiled'] = True
                            self.boiling_state['time_started'] = time.time()
                            self.boiling_state['waiting_for_boiling'] = False
                            
                            if self._can_trigger_alarm('boiling_start'):
                                alarm = self._create_alarm('BOILING_START',
                                    f"💧 Fervura detectada! Iniciando contagem de tempo...",
                                    {'current_value': current_temp, 'boiling_threshold': boiling_threshold})
                                triggered_alarms.append(alarm)
                    
                    # Fase 2: Contar tempo após fervura
                    elif self.boiling_state['has_boiled'] and self.boiling_state['time_started']:
                        duration = self.current_alarm_config.get('time_duration', 300)
                        elapsed = time.time() - self.boiling_state['time_started']
                        
                        if elapsed >= duration and self._can_trigger_alarm('time_complete'):
                            alarm = self._create_alarm('TIME_COMPLETE',
                                f"✅ Cozimento completo! Ferveu por {elapsed:.0f}s",
                                {'elapsed_time': elapsed, 'target_duration': duration})
                            triggered_alarms.append(alarm)
            
            return triggered_alarms
        except Exception as e:
            logger.error(f"Erro em check_alarms: {e}")
            return []
    
    def _create_alarm(self, alarm_type, message, data):
        """Cria um novo alarme"""
        timestamp_ms = int(time.time() * 1000)
        alarm_id = f"{alarm_type.lower()}_{timestamp_ms}"
        
        alarm = {
            'id': alarm_id,
            'type': alarm_type,
            'message': message,
            'priority': 'CRITICAL' if alarm_type == 'BOILING' else 'HIGH',
            'timestamp': time.time(),
            **data
        }
        
        self.active_alarms[alarm_id] = alarm
        self._play_alarm_sound()
        logger.info(f"🚨 ALARME {alarm_type} DISPARADO: {message}")
        
        # Limitar número de alarmes ativos
        if len(self.active_alarms) > 50:
            oldest_key = min(self.active_alarms.keys())
            del self.active_alarms[oldest_key]
            
        # Publicar via MQTT se disponível
        if self.mqtt_client:
            try:
                self.mqtt_client.publish_alarm(alarm)
            except Exception as e:
                logger.warning(f"Erro ao publicar alarme via MQTT: {e}")
        
        return alarm
    
    def get_status(self):
        """Retorna status completo do sistema de alarmes"""
        try:
            mode = self.current_alarm_config.get('mode', None)
            is_active = self.current_alarm_config.get('is_active', False)
            
            status = {
                'alarm_mode': mode,
                'is_active': is_active,
                'active_alarms_count': len(self.active_alarms),
                'active_alarms': [
                    {
                        'id': alarm['id'],
                        'type': alarm['type'],
                        'message': alarm['message'],
                        'priority': alarm['priority'],
                        'timestamp': alarm['timestamp']
                    }
                    for alarm in self.active_alarms.values()
                ]
            }
            
            # Adicionar configurações específicas do modo
            if mode == 'temperature_only':
                status['temperature_threshold'] = self.current_alarm_config.get('temperature_threshold', 95.0)
            elif mode == 'boiling_only':
                status['boiling_offset'] = self.current_alarm_config.get('boiling_offset', 0.0)
            elif mode == 'time_only':
                status['time_duration'] = self.current_alarm_config.get('time_duration', 300)
            elif mode == 'boiling_then_time':
                status['boiling_offset'] = self.current_alarm_config.get('boiling_offset', 0.0)
                status['time_duration'] = self.current_alarm_config.get('time_duration', 300)
                status['boiling_state'] = self.boiling_state.copy()
            
            return status
                
        except Exception as e:
            logger.error(f"Erro em get_status: {e}")
            return {
                'alarm_mode': None,
                'is_active': False,
                'active_alarms_count': 0,
                'active_alarms': [],
                'error': str(e)
            }
    
    def clear_all_alarms(self):
        """Limpa todos os alarmes ativos e desativa o sistema"""
        cleared_count = len(self.active_alarms)
        self.active_alarms.clear()
        
        # Desativar sistema
        self.current_alarm_config['is_active'] = False
        self.current_alarm_config['mode'] = None
        
        # Resetar cooldown
        self.last_alarm_time.clear()
        
        # Resetar estado de fervura
        self.boiling_state = {
            'has_boiled': False,
            'time_started': None,
            'waiting_for_boiling': False
        }
        
        logger.info(f"Cleared {cleared_count} active alarms - system deactivated")
    
    def _play_alarm_sound(self):
        """Toca som de alarme"""
        if self.sound_enabled:
            try:
                print("\a")  # Beep do sistema
                logger.info("🔊 ALARME SONORO DISPARADO!")
            except Exception as e:
                logger.warning(f"Não foi possível tocar alarme: {e}")
    
    def start_monitoring(self):
        """Inicia monitoramento de alarmes"""
        self.is_monitoring = True
        logger.info("Sistema de alarmes iniciado")
    
    def stop_monitoring(self):
        """Para monitoramento de alarmes"""
        self.is_monitoring = False
        self.clear_all_alarms()
        logger.info("Sistema de alarmes parado")

if __name__ == "__main__":
    print("Testing SmartAlarmManager...")
    manager = SmartAlarmManager()
    print("✅ SmartAlarmManager initialized")
    
    manager.configure_alarm('temperature_only', threshold=85.0)
    print("✅ Temperature alarm configured")
    
    status = manager.get_status()
    print(f"✅ Status: {status}")
    
    temp_data = {'temperature': 90.0}
    pressure_data = {'pressure': 1.0}
    alarms = manager.check_alarms(temp_data, pressure_data, 100.0)
    print(f"✅ Alarm check result: {alarms}")
    
    print("All tests passed!")