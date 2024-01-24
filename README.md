# URL-Content-Scraper
Smol python script that scrapes content from provided URLs to count the occurance of provided keywords to generate a csv that contains url, category content-type, filetype, column for each keyword, error, error details. 

![image](https://github.com/FlyingPhish/url-content-scraper/assets/46652779/32717e64-5283-4f15-90d2-00e4bc296ce7)

## Usage
python .\analyser -u url_file.txt -kw keywords_file.txt -o output.csv

## Setup
python -m venv .venv
[enter your venv]
pip install -r requirements.txt
