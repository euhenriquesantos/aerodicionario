from django.db import migrations


def create_trgm_indexes(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS glossario_termo_trgm_titulo ON glossario_termo USING gin (titulo gin_trgm_ops);"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS glossario_termo_trgm_en ON glossario_termo USING gin (decod_en gin_trgm_ops);"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS glossario_termo_trgm_pt ON glossario_termo USING gin (decod_pt gin_trgm_ops);"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS glossario_sinonimo_trgm ON glossario_termosinonimo USING gin (nome gin_trgm_ops);"
        )


def drop_trgm_indexes(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("DROP INDEX IF EXISTS glossario_termo_trgm_titulo;")
        cursor.execute("DROP INDEX IF EXISTS glossario_termo_trgm_en;")
        cursor.execute("DROP INDEX IF EXISTS glossario_termo_trgm_pt;")
        cursor.execute("DROP INDEX IF EXISTS glossario_sinonimo_trgm;")


class Migration(migrations.Migration):
    dependencies = [
        ("glossario", "0008_termohistory"),
    ]

    operations = [
        migrations.RunPython(create_trgm_indexes, reverse_code=drop_trgm_indexes),
    ]
