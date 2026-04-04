"""
Prueba para crear temas usando la API raw de Telegram
"""
from telethon import TelegramClient, functions
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")

async def main():
    client = TelegramClient('session_test', API_ID, API_HASH)
    await client.start()
    
    print("🔍 Prob métodos para crear temas...\n")
    
    # Método 1: functions.messages.CreateForumTopicRequest
    print("1️⃣ functions.messages.CreateForumTopicRequest")
    try:
        # Verificar si existe
        if hasattr(functions.messages, 'CreateForumTopicRequest'):
            print("   ✅ EXISTE")
        else:
            print("   ❌ NO EXISTE")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Método 2: functions.channels.CreateForumTopicRequest
    print("\n2️⃣ functions.channels.CreateForumTopicRequest")
    try:
        if hasattr(functions.channels, 'CreateForumTopicRequest'):
            print("   ✅ EXISTE")
        else:
            print("   ❌ NO EXISTE")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Método 3: Buscar cualquier función con "Topic" o "Forum"
    print("\n3️⃣ Buscando funciones relacionadas con Topics/Forums...")
    found = []
    
    for module_name in dir(functions):
        if module_name.startswith('_'):
            continue
        
        try:
            module = getattr(functions, module_name)
            if hasattr(module, '__dict__'):
                for attr in dir(module):
                    if 'Topic' in attr or 'Forum' in attr:
                        found.append(f"functions.{module_name}.{attr}")
        except:
            pass
    
    if found:
        print("   ✅ Encontrados:")
        for item in found:
            print(f"      - {item}")
    else:
        print("   ❌ No se encontraron funciones relacionadas")
    
    # Método 4: Usar InvokeWithLayerRequest (método de bajo nivel)
    print("\n4️⃣ Método alternativo: TL Schema")
    print("   Si no existe CreateForumTopicRequest, podemos usar:")
    print("   await client(functions.messages.CreateForumTopicRequest(...))")
    print("   O crear el tema manualmente y obtener el topic_id")
    
    await client.disconnect()
    
    print("\n" + "="*60)
    print("✅ Prueba completada")

if __name__ == "__main__":
    asyncio.run(main())
