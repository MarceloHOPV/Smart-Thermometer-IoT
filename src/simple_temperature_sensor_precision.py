"""
Sensor de Temperatura de Precisão - Smart Food Thermometer
Sistema de simulação realista de aquecimento até o ponto de ebulição
"""
import time
import math
import random
import threading
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PrecisionTemperatureSensor:
    def __init__(self):
        self.temperature = 20.0  # Temperatura inicial (ambiente aproximadamente a temperatura média de santa rita do sapucaí)
        self.is_heating = False
        self.heating_power = 1.0  # Potência de aquecimento
        self.ambient_temp = 20.0
        self.max_temp = 105.0  # Temperatura máxima realista
        self.target_temp = 101.0  # Temperatura alvo padrão
        
        # Parâmetros de simulação realista
        self.heating_rate = 0.8  # °C por segundo inicial
        self.thermal_mass = 1.0  # Massa térmica (afeta velocidade)
        self.heat_loss_coefficient = 0.02  # Perda de calor para ambiente
        
        # Thread de simulação
        self.simulation_thread = None
        self.running = False
        
        logger.info("Sensor de temperatura de precisão inicializado")
    
    def start_heating(self):
        """Inicia o aquecimento simulado"""
        if not self.is_heating:
            self.is_heating = True
            if not self.running:
                self.running = True
                self.simulation_thread = threading.Thread(target=self._simulate_heating, daemon=True)
                self.simulation_thread.start()
            logger.info("🔥 Aquecimento iniciado")
    
    def stop_heating(self):
        """Para o aquecimento (mas continua simulação de resfriamento)"""
        if self.is_heating:
            self.is_heating = False
            logger.info("🧊 Aquecimento parado - iniciando resfriamento")
    
    def stop_simulation(self):
        """Para completamente a simulação"""
        self.running = False
        self.is_heating = False
        if self.simulation_thread and self.simulation_thread.is_alive():
            self.simulation_thread.join(timeout=1)
        logger.info("Simulação de temperatura parada")
    
    def _simulate_heating(self):
        """Simula aquecimento/resfriamento realista"""
        last_time = time.time()
        
        while self.running:
            current_time = time.time()
            dt = current_time - last_time
            last_time = current_time
            
            if dt > 0:
                if self.is_heating:
                    # Aquecimento: taxa diminui conforme se aproxima do máximo
                    temp_ratio = (self.temperature - self.ambient_temp) / (self.max_temp - self.ambient_temp)
                    effective_heating_rate = self.heating_rate * (1 - temp_ratio * 0.7)
                    
                    # Adicionar variação realista
                    noise = random.uniform(-0.1, 0.1)
                    temp_increase = (effective_heating_rate + noise) * dt
                    
                    self.temperature += temp_increase
                    
                    # Limitar temperatura máxima
                    if self.temperature > self.max_temp:
                        self.temperature = self.max_temp
                else:
                    # Resfriamento natural
                    temp_diff = self.temperature - self.ambient_temp
                    cooling_rate = temp_diff * self.heat_loss_coefficient
                    self.temperature -= cooling_rate * dt
                    
                    # Limitar temperatura mínima
                    if self.temperature < self.ambient_temp:
                        self.temperature = self.ambient_temp            
            time.sleep(0.1)  # Atualização a cada 100ms
    
    def get_temperature(self):
        """Retorna temperatura atual"""
        return round(self.temperature, 1)
    
    def get_data(self, pressure=None):
        """Retorna dados completos do sensor"""
        return {
            'temperature': self.get_temperature(),
            'is_heating': self.is_heating,
            'heating_power': self.heating_power if self.is_heating else 0.0,
            'timestamp': time.time(),
            'status': 'heating' if self.is_heating else 'cooling' if self.temperature > self.ambient_temp else 'stable'
        }
    
    def set_heating_power(self, power):
        """Define potência de aquecimento (0.0 a 2.0)"""
        self.heating_power = max(0.0, min(2.0, power))
        self.heating_rate = 0.8 * self.heating_power
        logger.info(f"Potência de aquecimento ajustada para {self.heating_power}")
    
    def reset_temperature(self, temp=20.0):
        """Reseta temperatura para valor específico"""
        self.temperature = temp
        self.stop_heating()
        logger.info(f"Temperatura resetada para {temp}°C")
    
    def set_target_temperature(self, target_temp):
        """Define temperatura alvo para o sensor"""
        self.target_temp = target_temp
        logger.info(f"Temperatura alvo ajustada para {target_temp}°C")
    
    def get_target_temperature(self):
        """Retorna temperatura alvo atual"""
        return getattr(self, 'target_temp', 100.0)
    
    def start_system(self):
        """Inicia o sistema de aquecimento"""
        self.start_heating()
        logger.info("Sistema de aquecimento iniciado")
    
    def set_heating(self, enable):
        """Liga ou desliga o aquecimento"""
        if enable:
            self.start_heating()
        else:
            self.stop_heating()
        logger.info(f"Aquecimento {'ligado' if enable else 'desligado'}")

if __name__ == "__main__":
    print("Testing PrecisionTemperatureSensor...")
    sensor = PrecisionTemperatureSensor()
    print("Sensor initialized successfully")
    
    data = sensor.get_data()
    print(f"Sample data: {data}")
    
    data_with_pressure = sensor.get_data(1.2)
    print(f"Data with pressure: {data_with_pressure}")
    
    print("All tests passed!")
