from psycopg2.extensions import connection as _connection


class PostgresSaver:
    """Класс для сохранения данных в бд
    Принимает словарь из sqllite_loader.py со значениями из dataclasses
    проходит циклом, каждые 100 записей добавляет в postgres.
    В postgres добавляются данные из методов, mogrify + соответствующие названия таблиц
    """

    def __init__(self, pg_conn: _connection):
        self.conn = pg_conn
        self.cursor = self.conn.cursor()
        self.counter = 0
        self.tables = ''
        self.methods = {
            'film_work': self.mogrify_film_work,
            'genre': self.mogrify_genre,
            'genre_film_work': self.mogrify_genre_film_work,
            'person': self.mogrify_person,
            'person_film_work': self.mogrify_person_film_work,
        }

    def mogrify_film_work(self, data) -> list:
        args = ','.join(self.cursor.mogrify(
            "('{}', '{}', {}, {}, {}, '{}', '{}', '{}', {}, '{}')".format(
                item.title.replace("'", '"'),
                str(item.description).replace("'", '"') if item.description else 'null',
                item.creation_date if item.file_path else 'null',
                item.certificate if item.file_path else 'null',
                item.file_path if item.file_path else 'null',
                item.type,
                item.created_at,
                item.updated_at,
                item.rating if item.rating else 'null',
                item.id
            )).decode() for item in data)
        return args

    def mogrify_genre(self, data) -> list:
        args = ','.join(self.cursor.mogrify(
            "('{}', {}, '{}', '{}', '{}')".format(
                item.name,
                str(item.description).replace("'", '"').replace("None", 'null'),
                item.created_at,
                item.updated_at,
                item.id
            )).decode() for item in data)
        return args

    def mogrify_genre_film_work(self, data) -> list:
        args = ','.join(self.cursor.mogrify(
            "('{}', '{}', '{}', '{}')".format(
                item.film_work_id,
                item.genre_id,
                item.created_at,
                item.id
            )).decode() for item in data)
        return args

    def mogrify_person(self, data) -> list:
        args = ','.join(self.cursor.mogrify(
            "('{}', {}, '{}', '{}', '{}')".format(
                item.full_name.replace("'", '"'),
                item.birth_date if item.birth_date else 'null',
                item.created_at,
                item.updated_at,
                item.id
            )).decode() for item in data)
        return args

    def mogrify_person_film_work(self, data) -> list:
        args = ','.join(self.cursor.mogrify(
            "('{}', '{}', '{}', '{}', '{}')".format(
                item.film_work_id,
                item.person_id,
                item.role,
                item.created_at,
                item.id,
            )).decode() for item in data)
        return args

    def save_all_data(self, data: dict) -> bool:  # убрал try, except, так как rollback срабатывает автоматом.
        for table in data:
            method = self.methods[table]
            batch = 100
            for i in range(0, len(data[table]) + batch, batch):
                data_save = data[table][i: i + batch]
                if data_save:
                    self.cursor.execute(f"""
                        INSERT INTO content.{table} ({', '.join(i for i in data[table][0].__annotations__)})
                        VALUES {method(data_save)}
                        ON CONFLICT (id) DO NOTHING
                        """)
                    self.conn.commit()
        return True
