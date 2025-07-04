## Scraping data from the website https://cosmetic.de/.
Parsing data for all products on the site.

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

