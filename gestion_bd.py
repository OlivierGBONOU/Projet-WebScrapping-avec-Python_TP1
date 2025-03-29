import psycopg2

def check_database_exists():
    """Vérifie si la base de données existe déjà."""
    try:
        conn = psycopg2.connect(dbname='postgres', user='postgres', password='root', host='db')
        conn.autocommit = True
        cursor = conn.cursor()
        
        cursor.execute("SELECT 1 FROM pg_database WHERE datname='db_youtube_scrapper'")
        exists = cursor.fetchone()
        
        cursor.close()
        conn.close()
        return bool(exists)
    except psycopg2.Error as e:
        print(f"Erreur lors de la vérification de la base de données : {e}")
        return False

def create_database():
    """Crée la base de données si elle n'existe pas."""
    try:
        conn = psycopg2.connect(dbname='postgres', user='postgres', password='root', host='db')
        conn.autocommit = True
        cursor = conn.cursor()
        
        cursor.execute("SELECT 1 FROM pg_database WHERE datname='db_youtube_scrapper'")
        exists = cursor.fetchone()
        
        if exists:
            print("La base de données 'db_youtube_scrapper' existe déjà, aucune action effectuée.")
        else:
            cursor.execute('CREATE DATABASE db_youtube_scrapper')
            print("Base de données 'db_youtube_scrapper' créée.")
        
    except psycopg2.Error as e:
        print(f"Erreur lors de la création de la base de données : {e}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

def create_tables():
    """Crée les tables dans la base de données."""
    try:
        conn = psycopg2.connect(dbname='db_youtube_scrapper', user='postgres', password='root', host='db')
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS videos (
                id SERIAL PRIMARY KEY,
                artist_name TEXT,
                artist_photo TEXT,
                banner_photo TEXT,
                subscribers_count TEXT,
                videos_count TEXT,
                title TEXT,
                link TEXT,
                video_image TEXT,
                views TEXT,
                posted_since TEXT
            )
        ''')
        
        conn.commit()
        print("Table 'videos' créée ou déjà existante.")
        
    except psycopg2.Error as e:
        print(f"Erreur lors de la création des tables : {e}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

def delete_artist(artist):
    """Supprime la ligne correspondant à l'artiste si elle existe déja."""
    try:
        conn = psycopg2.connect(dbname='db_youtube_scrapper', user='postgres', password='root', host='db')
        cursor = conn.cursor()
        
        cursor.execute(f"SELECT COUNT(*) FROM videos WHERE artist_name = '{artist}'")
        count = cursor.fetchone()[0]
        
        if count > 0:
            cursor.execute(f"DELETE FROM videos WHERE artist_name = '{artist}'")
            conn.commit()
            print(f"{count} ligne(s) correspondant à l'artiste '{artist}' supprimée(s).")
        else:
            print(f"Aucune ligne pour l'artiste '{artist}' n'a été trouvée.")
        
    except psycopg2.Error as e:
        print(f"Erreur lors de la suppression de la ligne : {e}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    if not check_database_exists():
        create_database()
    create_tables()