import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()


class CosmeticPipeline:
    def __init__(self):
        self.connection = psycopg2.connect(
            host='127.0.0.1',
            port='5432',
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASS'),
            dbname=os.getenv('DB_NAME')
        )

        self.cur = self.connection.cursor()
        ## Create table if none exists
        self.cur.execute("""
                CREATE TABLE IF NOT EXISTS cosmetics (
                product_name TEXT,
                brand TEXT,
                ingredients text[],
                product_category TEXT,
                product_detail TEXT,
                page_url TEXT PRIMARY KEY,
                article_number TEXT,
                parse_date TIMESTAMP
            );
            """)

    def process_item(self, item, spider):
        try:
            # Execute SQL command on database to insert data in table
            self.cur.execute("""
                INSERT INTO cosmetics (
                    product_name,
                    brand,
                    ingredients,
                    product_category,
                    product_detail,
                    page_url,
                    article_number,
                    parse_date
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (page_url) DO NOTHING;
            """, (
                item['product_name'],
                item['brand'],
                item['ingredients'],  # Must be a Python list for text[]
                item['product_category'],
                item['product_detail'],
                item['page_url'],
                item['article_number'],
                item['parse_date']  # Should be a datetime.datetime object
            ))
            self.connection.commit()
        except:
            self.connection.rollback()
            raise
        return item

    def close_spider(self, spider):
        self.cur.close()
        self.connection.close()
