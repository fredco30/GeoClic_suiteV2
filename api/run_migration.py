"""
Script pour exécuter la migration d'ajout de project_id à la table lexique.
Usage: python run_migration.py
"""

import asyncio
import os
import sys

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/geoclic")

async def run_migration():
    print("🔄 Connexion à la base de données...")
    engine = create_async_engine(DATABASE_URL)

    async with engine.begin() as conn:
        print("📦 Exécution de la migration...")

        # 1. Ajouter la colonne project_id
        print("  - Ajout de la colonne project_id...")
        try:
            await conn.execute(text("ALTER TABLE lexique ADD COLUMN IF NOT EXISTS project_id UUID"))
            print("    ✅ Colonne ajoutée")
        except Exception as e:
            print(f"    ⚠️ {e}")

        # 2. Supprimer la contrainte unique sur code seul
        print("  - Suppression de la contrainte unique sur code...")
        try:
            await conn.execute(text("ALTER TABLE lexique DROP CONSTRAINT IF EXISTS lexique_code_key"))
            print("    ✅ Contrainte supprimée")
        except Exception as e:
            print(f"    ⚠️ {e}")

        # 3. Créer l'index sur project_id
        print("  - Création de l'index sur project_id...")
        try:
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_lexique_project ON lexique (project_id)"))
            print("    ✅ Index créé")
        except Exception as e:
            print(f"    ⚠️ {e}")

        # 4. Supprimer les anciennes entrées sans project_id
        print("  - Suppression des entrées sans project_id...")
        try:
            result = await conn.execute(text("DELETE FROM lexique WHERE project_id IS NULL"))
            count = result.rowcount
            print(f"    ✅ {count} entrée(s) supprimée(s)")
        except Exception as e:
            print(f"    ⚠️ {e}")

        print("\n✅ Migration terminée avec succès!")
        print("\n📝 Redémarre l'API et rafraîchis la page du navigateur.")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(run_migration())
