import os
import sys
from unittest import TestCase, mock

# from unittest.mock import patch, MagicMock
# import mysql.connector
# from mysql.connector.errors import Error

sys.path.append('..')
from app.scraper import get_db_connection


class TestDb(TestCase):
    @mock.patch.dict(os.environ, {'DB_HOST': os.environ['DB_HOST'], 'DB_PORT': os.environ['DB_PORT'],
                                  'DB_NAME': os.environ['DB_NAME'], 'DB_USER': os.environ['DB_USER'],
                                  'DB_PASSWORD': os.environ['DB_PASSWORD']})
    def test_get_db_connection(self):
        conn = get_db_connection()
        self.assertIsNotNone(conn)
        self.assertEqual(conn.user, os.environ['DB_USER'])
        self.assertEqual(conn._host, os.environ['DB_HOST'])
        self.assertEqual(conn.database, os.environ['DB_NAME'])
        self.assertEqual(conn.charset, 'utf8mb4')


print("this is test_db.py ... \n")

if __name__ == '__main__':
    test = TestDb()
    test.test_get_db_connection()
    print("test_db.py is finished ! \n")
