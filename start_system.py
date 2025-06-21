#!/usr/bin/env python3
"""
Script de Inicialização Completa do Sistema IoT Smart Thermometer
"""
import subprocess
import time
import sys
import os
import threading
import signal

# Adicionar o diretório src ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def start_backend():
    """Iniciar o servidor Flask backend"""
    print("🚀 Iniciando servidor Flask backend...")
    try:
        # Navegar para o diretório src e executar
        os.chdir('src')
        subprocess.run([sys.executable, 'web_app.py'], check=True)
    except Exception as e:
        print(f"❌ Erro ao iniciar backend: {e}")
        
def start_frontend():
    """Iniciar o servidor frontend"""
    print("🌐 Iniciando servidor frontend...")
    try:
        # Voltar para o diretório raiz
        os.chdir('..')
        subprocess.run([sys.executable, 'serve_frontend.py', '8080'], check=True)
    except Exception as e:
        print(f"❌ Erro ao iniciar frontend: {e}")

def main():
    """Função principal"""
    print("=" * 60)
    print("🌡️  IoT SMART THERMOMETER - INICIALIZAÇÃO COMPLETA")
    print("=" * 60)
    
    # Verificar se estamos no diretório correto
    if not os.path.exists('src/web_app.py'):
        print("❌ Execute este script do diretório raiz do projeto!")
        return
    
    print("📋 Configuração do sistema:")
    print("   - Backend Flask: http://localhost:5000")
    print("   - Frontend: http://localhost:8080")
    print("   - Alarme padrão: BOILING (fervura) ativado")
    print()
    
    # Criar threads para executar os servidores
    backend_thread = threading.Thread(target=start_backend, daemon=True)
    frontend_thread = threading.Thread(target=start_frontend, daemon=True)
    
    try:
        # Iniciar backend
        print("1️⃣ Iniciando backend...")
        backend_thread.start()
        time.sleep(3)  # Aguardar backend inicializar
        
        # Iniciar frontend
        print("2️⃣ Iniciando frontend...")
        frontend_thread.start()
        time.sleep(2)  # Aguardar frontend inicializar
        
        print()
        print("✅ Sistema iniciado com sucesso!")
        print("🔗 Acesse: http://localhost:8080")
        print("📊 API: http://localhost:5000/api/alarms/status")
        print()
        print("Press Ctrl+C para parar o sistema...")
        
        # Manter o script rodando
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Parando sistema...")
        
    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    main()
