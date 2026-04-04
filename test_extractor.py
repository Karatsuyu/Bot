"""
Script de prueba para el extractor de enlaces mejorado
"""
from feature.scanner.extractor import extract_links

# Textos de prueba basados en las imágenes que mostraste
test_texts = [
    # Texto 1: Enlaces tradicionales
    """
    Únete a nuestro canal: https://t.me/+abc123xyz
    También en: t.me/canal_publico
    Y en telegram.me/otro_canal
    """,
    
    # Texto 2: Menciones @username (como en tu primera imagen)
    """
    @Mila_News @China_Y_Tecno
    @kanal_de_noticias @recursos_abc
    Más contenido en @otro_canal_oficial
    """,
    
    # Texto 3: Enlaces a mensajes específicos
    """
    Mira este mensaje: https://t.me/canal/12345
    Otro ejemplo: t.me/otro_canal/999
    """,
    
    # Texto 4: Enlaces de invitación privados
    """
    Únete aquí: https://t.me/+AbCdEfGhIjKlMnOp
    O aquí: t.me/joinchat/AbCdEfGhIjKl
    """,
    
    # Texto 5: Mezcla de todos los formatos (como en tus imágenes)
    """
    📢 Canales recomendados:
    @kanal_1 @kanal_2 @kanal_3
    
    🔗 Enlaces directos:
    https://t.me/+PrivateCode123
    t.me/canal_publico
    
    💬 Grupos:
    @grupo_oficial @comunidad_abc
    
    ✉️ Contacto: t.me/admin_personal (este debería filtrarse)
    """,
]

print("="*60)
print("🧪 PRUEBA DE EXTRACTOR DE ENLACES")
print("="*60)

for i, text in enumerate(test_texts, 1):
    print(f"\n📝 Prueba {i}:")
    print("-" * 40)
    
    links = extract_links(text)
    
    print(f"Enlaces encontrados: {len(links)}")
    for link in links:
        print(f"  • {link}")

print("\n" + "="*60)
print("✅ Pruebas completadas")
print("="*60)

# Prueba específica con los formatos de tus imágenes
print("\n📸 PRUEBA CON FORMATOS DE TUS IMÁGENES:")
print("-" * 60)

image_text = """
@Mila_News @China_Y_Tecno @kanal_de_noticias
@recursos_abc @otro_canal @mas_canales
https://t.me/+PrivateInvite123
t.me/canal_publico
@grupo_oficial @comunidad_test
"""

links = extract_links(image_text)
print(f"\nEnlaces extraídos del texto de la imagen: {len(links)}")
for link in links:
    print(f"  ✅ {link}")

print("\n💡 NOTA: Los enlaces @username se convierten a t.me/username")
print("   El bot intentará unirse como canales/grupos públicos")
