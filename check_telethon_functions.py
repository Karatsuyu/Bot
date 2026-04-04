"""
Script para verificar qué funciones de Telegram están disponibles en esta versión de Telethon
"""
from telethon import functions
import telethon

print(f"Telethon version: {telethon.__version__}")
print("\n" + "="*60)

# Verificar módulos disponibles
print("\n📦 Módulos en functions:")
for attr in dir(functions):
    if not attr.startswith('_'):
        print(f"  - {attr}")

# Verificar si existe CreateForumTopicRequest en diferentes módulos
print("\n" + "="*60)
print("🔍 Buscando CreateForumTopicRequest...")

modules_to_check = [
    functions.channels,
    functions.messages,
    functions.account,
    functions.phone,
]

for module in modules_to_check:
    module_name = module.__name__.split('.')[-1]
    if hasattr(module, 'CreateForumTopicRequest'):
        print(f"✅ ENCONTRADO en functions.{module_name}")
    else:
        print(f"❌ NO está en functions.{module_name}")

# Listar todas las clases disponibles en channels
print("\n" + "="*60)
print("📋 Funciones en functions.channels:")
if hasattr(functions, 'channels'):
    for attr in dir(functions.channels):
        if not attr.startswith('_') and 'Topic' in attr:
            print(f"  - {attr}")
else:
    print("  (no disponible)")

# Listar todas las clases disponibles en messages
print("\n📋 Funciones en functions.messages (relacionadas con Forum/Topic):")
if hasattr(functions, 'messages'):
    for attr in dir(functions.messages):
        if not attr.startswith('_') and ('Topic' in attr or 'Forum' in attr):
            print(f"  - {attr}")
else:
    print("  (no disponible)")

print("\n" + "="*60)
