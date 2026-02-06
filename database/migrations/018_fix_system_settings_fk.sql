-- ═══════════════════════════════════════════════════════════════════════════════
-- Migration 018: Correction FK system_settings.updated_by
-- Description: La FK référençait l'ancienne table 'users' au lieu de 'geoclic_users'
--              Cela causait une erreur 500 lors de la sauvegarde des paramètres
-- ═══════════════════════════════════════════════════════════════════════════════

-- 1. Supprimer l'ancienne contrainte FK (si elle existe)
DO $$
BEGIN
    -- Chercher et supprimer la FK existante sur updated_by
    IF EXISTS (
        SELECT 1 FROM information_schema.table_constraints tc
        JOIN information_schema.constraint_column_usage ccu ON tc.constraint_name = ccu.constraint_name
        WHERE tc.table_name = 'system_settings'
          AND tc.constraint_type = 'FOREIGN KEY'
          AND ccu.column_name = 'id'
    ) THEN
        -- Trouver le nom de la contrainte dynamiquement
        EXECUTE (
            SELECT 'ALTER TABLE system_settings DROP CONSTRAINT ' || tc.constraint_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name
            WHERE tc.table_name = 'system_settings'
              AND tc.constraint_type = 'FOREIGN KEY'
              AND kcu.column_name = 'updated_by'
            LIMIT 1
        );
        RAISE NOTICE 'Ancienne FK supprimée sur system_settings.updated_by';
    END IF;
END $$;

-- 2. Ajouter la nouvelle FK vers geoclic_users
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'geoclic_users') THEN
        ALTER TABLE system_settings
            ADD CONSTRAINT fk_system_settings_updated_by
            FOREIGN KEY (updated_by) REFERENCES geoclic_users(id)
            ON DELETE SET NULL;
        RAISE NOTICE 'Nouvelle FK créée: system_settings.updated_by -> geoclic_users.id';
    ELSE
        -- Si geoclic_users n'existe pas, supprimer simplement la colonne FK
        -- (ne devrait pas arriver en production)
        RAISE WARNING 'Table geoclic_users non trouvée - FK non créée';
    END IF;
END $$;

-- 3. Vérification
SELECT
    tc.constraint_name,
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage ccu ON tc.constraint_name = ccu.constraint_name
WHERE tc.table_name = 'system_settings'
  AND tc.constraint_type = 'FOREIGN KEY';
