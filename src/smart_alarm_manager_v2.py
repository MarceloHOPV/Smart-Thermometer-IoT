"""
Smart Alarm Management System - VERSÃO ULTRA SIMPLIFICADA COM COOLDOWN
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
        
        # Sistema de cooldown para evitar spam de alarmes (mas permitir novos alarmes)
        self.last_alarm_time = {}  # Rastrear último alarme por tipo
        self.alarm_cooldown = 3.0  # 3 segundos entre alarmes do mesmo tipo
        
        # Configuração atual do alarme (apenas UM tipo ativo)
        # INICIAR SEM ALARME ATIVO POR PADRÃO
        self.current_alarm_config = {
            'mode': None,  # Sem alarme por padrão
            'temperature_threshold': 95.0,
            'time_duration': 300,
            'boiling_offset': 0.0,
            'is_active': False  # Desativado por padrão
        }
        
        # Estado para boiling_then_time
        self.boiling_state = {
            'has_boiled': False,
            'time_started': None,
            'waiting_for_boiling': False
        }        
        logger.info("Smart Alarm Manager initialized - NO alarm active by default")
    
    def configure_alarm(self, mode, **kwargs):
        """Configura alarme com modo exclusivo"""
        # Só limpar alarmes se for um modo DIFERENTE
        current_mode = self.current_alarm_config.get('mode')
        if current_mode != mode:
            self.clear_all_alarms()
            logger.info(f"Mudando modo de {current_mode} para {mode} - alarmes limpos")
        else:
            logger.info(f"Reconfigurando mesmo modo {mode} - mantendo alarmes existentes")
        
        # RESETAR cooldown ao reconfigurar para permitir alarmes imediatos
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
        logger.info(f"Alarme configurado: {mode} com parâmetros {kwargs} - cooldown resetado")
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
        """Verifica alarmes - VERSÃO COM COOLDOWN"""
        try:
            if not self.current_alarm_config.get('is_active', False):
                logger.debug("Sistema de alarmes não está ativo")
                return []
            
            mode = self.current_alarm_config.get('mode')
            if not mode:
                logger.debug("Nenhum modo de alarme configurado")
                return []
            
            current_temp = temperature_data.get('temperature', 0) if temperature_data else 0
            triggered_alarms = []
            
            logger.debug(f"Verificando alarmes: modo={mode}, temp={current_temp:.1f}°C")
            
            # Alarme de temperatura
            if mode == 'temperature_only':
                threshold = self.current_alarm_config.get('temperature_threshold', 95.0)
                logger.debug(f"Verificando alarme de temperatura: {current_temp:.1f}°C >= {threshold}°C")
                
                if current_temp >= threshold:
                    if self._can_trigger_alarm('temperature'):
                        # Usar timestamp com milissegundos para IDs únicos
                        timestamp_ms = int(time.time() * 1000)
                        alarm_id = f"temp_{timestamp_ms}"
                        
                        alarm = {
                            'id': alarm_id,
                            'type': 'TEMPERATURE',
                            'message': f"🌡️ Temperatura atingiu {current_temp:.1f}°C (limite: {threshold}°C)",
                            'priority': 'HIGH',
                            'timestamp': time.time(),
                            'current_value': current_temp,
                            'threshold': threshold
                        }
                        self.active_alarms[alarm_id] = alarm
                        triggered_alarms.append(alarm)
                        self._play_alarm_sound()
                        logger.info(f"🚨 ALARME TEMPERATURA DISPARADO: {current_temp:.1f}°C >= {threshold}°C")
                        
                        # Limitar o número de alarmes ativos
                        if len(self.active_alarms) > 50:
                            oldest_key = min(self.active_alarms.keys())
                            del self.active_alarms[oldest_key]
                    else:
                        logger.debug(f"Alarme temperatura em cooldown")
                        
            # Alarme de ebulição
            elif mode == 'boiling_only':
                if boiling_point:  # Verificar se temos o ponto de ebulição
                    boiling_threshold = boiling_point + self.current_alarm_config.get('boiling_offset', 0.0)
                    logger.debug(f"Verificando alarme de fervura: {current_temp:.1f}°C >= {boiling_threshold:.1f}°C")
                    
                    if current_temp >= boiling_threshold:
                        if self._can_trigger_alarm('boiling'):
                            # Usar timestamp com milissegundos para IDs únicos
                            timestamp_ms = int(time.time() * 1000)
                            alarm_id = f"boiling_{timestamp_ms}"
                            
                            alarm = {
                                'id': alarm_id,
                                'type': 'BOILING',
                                'message': f"💧 Líquido está FERVENDO! {current_temp:.1f}°C ≥ {boiling_threshold:.1f}°C",
                                'priority': 'CRITICAL',
                                'timestamp': time.time(),
                                'current_value': current_temp,
                                'boiling_point': boiling_point,
                                'boiling_threshold': boiling_threshold
                            }
                            self.active_alarms[alarm_id] = alarm
                            triggered_alarms.append(alarm)
                            self._play_alarm_sound()
                            logger.info(f"🚨 ALARME FERVURA DISPARADO: {current_temp:.1f}°C >= {boiling_threshold:.1f}°C")
                            
                            # Limitar o número de alarmes ativos para evitar sobrecarga
                            if len(self.active_alarms) > 50:
                                oldest_key = min(self.active_alarms.keys())
                                del self.active_alarms[oldest_key]
                        else:
                            logger.debug(f"Alarme fervura em cooldown")
                else:
                    logger.debug("Ponto de ebulição não calculado ainda")
            
            # Outros modos (time_only, boiling_then_time) podem ser implementados depois
            
            return triggered_alarms
        except Exception as e:
            logger.error(f"Erro em check_alarms: {e}")
            return []
    
    def get_status(self):
        """Retorna status completo do sistema de alarmes"""
        try:
            mode = self.current_alarm_config.get('mode', None)
            is_active = self.current_alarm_config.get('is_active', False)
            alarms_copy = dict(self.active_alarms)
            
            status = {
                'alarm_mode': mode,
                'is_active': is_active,
                'active_alarms_count': len(alarms_copy),
                'active_alarms': []
            }
            
            # Serializar alarmes para JSON
            for alarm_id, alarm in alarms_copy.items():
                try:
                    serialized_alarm = {
                        'id': alarm['id'],
                        'type': alarm['type'],
                        'message': alarm['message'],
                        'priority': alarm['priority'],
                        'timestamp': alarm['timestamp']
                    }
                    status['active_alarms'].append(serialized_alarm)
                except Exception as e:
                    logger.warning(f"Erro ao serializar alarme {alarm_id}: {e}")
            
            # Adicionar informações específicas do modo
            if mode == 'temperature_only':
                status['temperature_threshold'] = self.current_alarm_config.get('temperature_threshold', 95.0)
            elif mode == 'time_only':
                status['time_duration'] = self.current_alarm_config.get('time_duration', 300)
            elif mode == 'boiling_only':
                status['boiling_offset'] = self.current_alarm_config.get('boiling_offset', 0.0)
            elif mode == 'boiling_then_time':
                status['boiling_offset'] = self.current_alarm_config.get('boiling_offset', 0.0)
                status['time_duration'] = self.current_alarm_config.get('time_duration', 300)
                status['boiling_state'] = self.boiling_state.copy()
                if self.boiling_state.get('time_started'):
                    status['boiling_state']['elapsed_time'] = time.time() - self.boiling_state['time_started']
            
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
        """Limpa todos os alarmes ativos E DESATIVA COMPLETAMENTE o sistema"""
        cleared_count = len(self.active_alarms)
        self.active_alarms.clear()
        
        # DESATIVAR COMPLETAMENTE o sistema após limpar
        self.current_alarm_config['is_active'] = False
        self.current_alarm_config['mode'] = None
        
        # RESETAR cooldown para permitir novos alarmes imediatamente
        self.last_alarm_time.clear()
        
        self.boiling_state = {
            'has_boiled': False,
            'time_started': None,
            'waiting_for_boiling': False
        }
        logger.info(f"Cleared {cleared_count} active alarms - system DEACTIVATED - cooldown reset")
    
    def _play_alarm_sound(self):
        """Toca som de alarme"""
        if self.sound_enabled:
            try:
                print("\a")  # Beep do sistema
                logger.info("🔊 ALARME DISPARADO!")
            except Exception as e:
                logger.warning(f"Não foi possível tocar alarme: {e}")
    
    def start_monitoring(self):
        """Inicia monitoramento de alarmes"""
        self.is_monitoring = True
        logger.info("Smart alarm monitoring started")
    
    def stop_monitoring(self):
        """Para monitoramento de alarmes"""
        self.is_monitoring = False
        self.clear_all_alarms()
        logger.info("Smart alarm monitoring stopped")
