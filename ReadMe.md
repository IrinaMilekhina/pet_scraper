## Scraping data from the website https://cosmetic.de/.
Parsing data for all products on the site using scrapy.

## Start
Installations:
- docker installed
- python 3.7+ (written on 3.12)

Preparation:
- install requirements from requirements.txt
- create and up docker container (DB section for details)
- make .env file in the project root directory (envs section for details)

Run:
- run runner.py

### Data
- Name of the product
- Brand
- Ingredients (separated into list[str])
- Category of the product, based on breadcrumbs
- All details about the product from product page 
- Page url
- Article number

### DB
The collected data is saved to the **PostgreSQL** which is containerized in docker-compose.

To create docker run command from project directory:
`docker-compose up`

## envs
Environments located in .env file
DB_PASS
DB_USER
DB_NAME

## TODO
- description section scrapping ways
- move cleaning data to pipelines
- add duplicates check
- check other empty fields
- add next resource
- add excel
- ingredients on "https://cosmetic.de/gesicht/ampullen/3246/alessandro-arctic-hand-nail-care-elixir-set-3x2ml"