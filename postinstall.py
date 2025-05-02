import os

def patch_django_fernet_fields():
    path = "venv/Lib/site-packages/fernet_fields/fields.py"
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as file:
            content = file.read()
        content = content.replace(
            "from django.utils.encoding import force_bytes, force_text",
            "from django.utils.encoding import force_bytes, force_str as force_text"
        )
        with open(path, "w", encoding="utf-8") as file:
            file.write(content)
    else:
        print("⚠️ No se encontró fernet_fields. ¿Seguro que está instalado?")

if __name__ == "__main__":
    patch_django_fernet_fields()
