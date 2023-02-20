import os
import time
from typing import Any, Dict, List
import mysql.connector
from mysql.connector.errors import Error

import requests
from bs4 import BeautifulSoup


def scrape_zenn(item_count: int, page_count: int = 1) -> List[Dict[str, Any]]:
    """
    Zennの記事をスクレイピングする関数。

    Args:
        item_count (int): スクレイピングしたい記事数。
        page_count (int, optional): スクレイピングしたいページ数。デフォルトは1。

    Returns:
        list[dict]: スクレイピングした記事のリスト。各記事は辞書型でtitle, author, linkをキーとして持つ。
    """

    zenn_url = f"https://zenn.dev/topics/{os.environ['ZENN_SEARCH_KEYWORD']}"
    zenn_articles: List[Dict[str, Any]] = []

    for page in range(1, page_count + 1):
        params = {"page": page}
        r = requests.get(zenn_url, params=params, headers={"User-Agent": "Mozilla/5.0"})
        if r.ok:
            soup = BeautifulSoup(r.text, "html.parser")
            contents = soup.find_all("div", class_="ArticleList_itemContainer__xlBMc")
            time.sleep(3)
            n = 0
            for content in contents:
                if n < item_count:
                    link = "https://zenn.dev" + content.a.get("href")
                    title = content.find("h2").text
                    author = content.find("div", class_="ArticleList_userName__GWXDx").text
                    d = {"title": title, "author": author, "link": link}
                    zenn_articles.append(d)
                    n += 1
                elif n == item_count:
                    break
        else:
            r.raise_for_status()
    print('Zenn記事のスクレイピング : ', zenn_articles)
    return zenn_articles


def scrape_qiita(item_count: int, page_count: int = 1) -> List[Dict[str, Any]]:
    """
    Qiitaの記事をスクレイピングする関数。

    Args:
        item_count (int): スクレイピングしたい記事数。
        page_count (int, optional): スクレイピングしたいページ数。デフォルトは1。

    Returns:
        list[dict]: スクレイピングした記事のリスト。各記事は辞書型でtitle, author, linkをキーとして持つ。
    """

    qiita_url = f"https://qiita.com/search"
    qiita_articles: List[Dict[str, Any]] = []

    for page in range(1, page_count):
        params = {"q": os.environ["QIITA_SEARCH_KEYWORD"], "sort": "created", "page": page}
        r = requests.get(qiita_url, params=params, headers={"User-Agent": "Mozilla/5.0"})
        if r.ok:
            soup = BeautifulSoup(r.text, "html.parser")
            contents = soup.find_all('article', class_='style-omc3xd')
            time.sleep(3)
            n = 0
            for content in contents:
                if n < item_count:
                    link = 'https://qiita.com' + content.find('h2', class_='style-1qj67q5').find('a').get(
                        'href')
                    title = content.find('h2', class_='style-1qj67q5').find('a').text
                    author = content.find('a', class_='style-506wqi').text
                    d = {
                        'title': title,
                        'author': author,
                        'link': link,
                    }
                    qiita_articles.append(d)
                    n += 1
                elif n == item_count:
                    break
        else:
            r.raise_for_status()
    print('Qiita記事のスクレイピング ; ', qiita_articles)
    return qiita_articles


def get_db_connection():
    try:
        cnx = mysql.connector.connect(
            user=os.environ['DB_USER'],
            password=os.environ['DB_PASSWORD'],
            host=os.environ['DB_HOST'],
            database=os.environ['DB_NAME'],
            charset='utf8mb4',
            collation='utf8mb4_unicode_ci',
            auth_plugin='mysql_native_password'
        )

        return cnx
    except Error as e:
        print(f"Error while connecting to database: {e}")
        raise e


def create_table(table_name: str) -> None:
    """
    指定されたテーブルが存在しなかった場合に作成する関数。

    Args:
        table_name (str): 挿入先のテーブル名。
    """
    cnx = None
    cursor = None
    try:
        cnx = get_db_connection()
        cursor = cnx.cursor()
        create_table_query = f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                id INT(11) NOT NULL AUTO_INCREMENT PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                author VARCHAR(255) NOT NULL,
                link VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """

        cursor.execute(create_table_query)
        cnx.commit()
    except Error as e:
        print(f"Error while Creating {table_name}: {e}")
    finally:
        if cursor is not None:
            cursor.close()
        if cnx is not None:
            cnx.close()


def insert_articles(articles: List[Dict[str, Any]], table_name: str) -> None:
    """
    指定されたテーブルに記事を挿入する関数。

    Args:
        articles (list[dict]): 挿入する記事データのリスト。各記事は辞書型でtitle, author, linkをキーとして持つ。
        table_name (str): 挿入先のテーブル名。
    """
    cnx = None
    cursor = None
    try:
        cnx = get_db_connection()
        cursor = cnx.cursor()

        # 記事挿入のSQLを生成
        insert_articles_sql = f"""
            INSERT INTO {table_name} (title, author, link) VALUES (%s, %s, %s)
        """

        # 記事を挿入
        for article in articles:
            data = (article['title'], article['author'], article['link'])
            cursor.execute(insert_articles_sql, data)
        cnx.commit()
    except Error as e:
        print(f"Error while inserting into {table_name}: {e}")
        raise e
    finally:
        if cursor is not None:
            cursor.close()
        if cnx is not None:
            cnx.close()


def select_all_articles(table_name: str) -> None:
    """
    指定されたテーブルのレコードを全取得する関数。

    Args:
        table_name (str): 取得先のテーブル名。
    """
    cnx = None
    cursor = None
    try:
        cnx = get_db_connection()
        cursor = cnx.cursor()

        select_articles_query = f"""
            SELECT * FROM {os.environ['DB_NAME']}.{table_name};
        """

        cursor.execute(select_articles_query)
        result = cursor.fetchall()
        for row in result:
            print(row)
    except Error as e:
        print(f'Error while select from {table_name}: {e}')
        raise e
    finally:
        if cursor is not None:
            cursor.close()
        if cnx is not None:
            cnx.close()


def main() -> None:
    site_list = [
        {'name': 'zenn', 'scrape_function': scrape_zenn, 'item_count': 5, 'page_count': 2,
         'table_name': 'zenn_articles'},
        {'name': 'qiita', 'scrape_function': scrape_qiita, 'item_count': 5, 'page_count': 2,
         'table_name': 'qiita_articles'}
    ]

    all_articles: List[Dict[str, Any]] = []
    for site in site_list:
        print(f'{"---"*10} Create {site["table_name"]} table {"---"*10} \n')
        create_table(site['table_name'])
        print(f'{"---"*10} Scraping {site["name"]} ... {"---"*10} \n')
        articles = site["scrape_function"](site["item_count"], site["page_count"])
        all_articles.extend(articles)

        # テーブル作成と記事の挿入
        insert_articles(articles, site['table_name'])

    for article in all_articles:
        print(article, '\n')

    for site in site_list:
        print(f'{"---"*10} Select all from {site["table_name"]} {"---"*10} \n')
        select_all_articles(site['table_name'])
    print(f'{"---"*10} finished queries {"---"*10}')


if __name__ == '__main__':
    main()
    print("all finished")
