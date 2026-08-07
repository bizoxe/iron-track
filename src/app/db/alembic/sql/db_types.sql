DO $$
BEGIN
    -- 1. force_enum
    -- Used in: exercises.force
    BEGIN
        CREATE TYPE force_enum AS ENUM ('pull', 'push', 'static');
    EXCEPTION WHEN duplicate_object THEN NULL; END;

    -- 2. difficulty_level_enum
    -- Used in: exercises.difficulty_level, training_plans.difficulty_level
    BEGIN
        CREATE TYPE difficulty_level_enum AS ENUM ('beginner', 'intermediate', 'expert');
    EXCEPTION WHEN duplicate_object THEN NULL; END;

    -- 3. mechanic_enum
    -- Used in: exercises.mechanic
    BEGIN
        CREATE TYPE mechanic_enum AS ENUM ('compound', 'isolation');
    EXCEPTION WHEN duplicate_object THEN NULL; END;

    -- 4. category_enum
    -- Used in: exercises.category
    BEGIN
        CREATE TYPE category_enum AS ENUM ('strength', 'stretching', 'plyometrics', 'strongman', 'powerlifting', 'cardio', 'olympic weightlifting');
    EXCEPTION WHEN duplicate_object THEN NULL; END;

    -- 5. exercise_mode_enum
    -- Used in: unit_exercises.mode, session_exercises.mode_snapshot
    BEGIN
        CREATE TYPE exercise_mode_enum AS ENUM ('reps', 'time', 'distance', 'sets only');
    EXCEPTION WHEN duplicate_object THEN NULL; END;

    -- 6. sharing_status_enum
    -- Used in: training_units.sharing_status, training_plans.sharing_status
    BEGIN
        CREATE TYPE sharing_status_enum AS ENUM ('private', 'shared', 'public');
    EXCEPTION WHEN duplicate_object THEN NULL; END;
END $$;