"""
Test direct API call to debug the issue
"""
import requests
import time

def test_api_directly():
    """Test API directly without using PowerShell"""
    print("🔧 Direct API test:")
    
    for i in range(10):
        try:
            response = requests.get("http://localhost:5000/api/sensor_data", timeout=5)
            data = response.json()
            temp = data['temperature']['temperature']
            print(f"Test {i+1}: {temp:.1f}°C")
            time.sleep(1)
        except Exception as e:
            print(f"Error in test {i+1}: {e}")

if __name__ == "__main__":
    test_api_directly()
