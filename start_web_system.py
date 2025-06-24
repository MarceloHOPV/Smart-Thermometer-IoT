#!/usr/bin/env python3
"""
Script para inicializar o sistema web com todas as dependências
"""
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.web_app import app, initialize_systems, start_data_collection
from src.config import Config

def start_web_system():
    """Inicializa o sistema completo e inicia o servidor"""
    try:
        print("🚀 Iniciando sistema IoT Smart Thermometer...")
        
        # Initialize all systems
        print("🔧 Inicializando sistemas...")
        initialize_systems()
        
        # Start data collection
        print("📊 Iniciando coleta de dados...")
        start_data_collection()
        
        # Run Flask app
        print(f"🌐 Iniciando servidor web em http://{Config.WEB_HOST}:{Config.WEB_PORT}")
        app.run(host=Config.WEB_HOST, port=Config.WEB_PORT, debug=Config.WEB_DEBUG)
        
    except KeyboardInterrupt:
        print("\n🛑 Parando sistema...")
    except Exception as e:
        print(f"❌ Erro ao iniciar sistema: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    start_web_system()
