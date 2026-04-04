"""
Prueba rápida del extractor - Ejecutar directamente
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from feature.scanner.extractor import extract_links

print("="*60)
print("🧪 PRUEBA DE EXTRACTOR DE ENLACES")
print("="*60)

# Prueba 1: Enlaces tradicionales
print("\n📝 Prueba 1: Enlaces tradicionales")
text1 = "Únete a: https://t.me/+abc123xyz y t.me/canal_publico"
links1 = extract_links(text1)
print(f"Texto: {text1}")
print(f"Encontrados: {links1}")

# Prueba 2: Menciones @username (como en tu imagen)
print("\n📝 Prueba 2: Menciones @username")
text2 = "@Mila_News @China_Y_Tecno @kanal_de_noticias"
links2 = extract_links(text2)
print(f"Texto: {text2}")
print(f"Encontrados: {links2}")

# Prueba 3: Mezcla de formatos
print("\n📝 Prueba 3: Mezcla de formatos")
text3 = """
Canales: @kanal_1 @kanal_2
Enlaces: https://t.me/+PrivateCode123 t.me/publico
"""
links3 = extract_links(text3)
print(f"Texto: {text3.strip()}")
print(f"Encontrados: {links3}")

# Prueba 4: Enlaces a mensajes
print("\n📝 Prueba 4: Enlaces a mensajes específicos")
text4 = "https://t.me/canal/12345 t.me/otro/999"
links4 = extract_links(text4)
print(f"Texto: {text4}")
print(f"Encontrados: {links4}")

# Prueba 5: Lo que debería filtrarse
print("\n📝 Prueba 5: Enlaces que se filtran")
text5 = "@ab @addlist/xyz123"
links5 = extract_links(text5)
print(f"Texto: {text5}")
print(f"Encontrados: {links5} (debería estar vacío o casi vacío)")

print("\n" + "="*60)
print("✅ Pruebas completadas")
print("="*60)

print("\n📊 RESUMEN:")
print(f"  Prueba 1 (tradicionales): {len(links1)} enlaces")
print(f"  Prueba 2 (@username): {len(links2)} enlaces")
print(f"  Prueba 3 (mezcla): {len(links3)} enlaces")
print(f"  Prueba 4 (mensajes): {len(links4)} enlaces")
print(f"  Prueba 5 (filtrados): {len(links5)} enlaces")

print("\n💡 Los enlaces @username se convierten a t.me/username")
print("   El bot intentará unirse como canales/grupos públicos")
