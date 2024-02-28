import argparse
import aiohttp
import asyncio
import chardet
import csv
import os
import re
from typing import List
from aiohttp import ClientSession

# Fixed typo in the COMMON_ENCODINGS list
COMMON_ENCODINGS = ['utf-8', 'iso-8859-1', 'windows-1252', 'utf-16', 'ascii']

def parse_arguments():
    parser = argparse.ArgumentParser(description='Process URL and keyword files.')
    parser.add_argument('-u', '--url', required=True, help='File with URLs')
    parser.add_argument('-kw', '--keywords', required=True, help='File with keywords')
    parser.add_argument('-o', '--output', required=True, help='Output CSV file path')
    return parser.parse_args()

def validate_file(file_path):
    return os.path.exists(file_path) and os.path.isfile(file_path)

def read_lines(file_path) -> List[str]:
    with open(file_path, 'r') as file:
        return [line.strip() for line in file.readlines()]

async def process_urls(urls, keywords, session):
    results = []
    for url in urls:
        print("Analysing: " + url)
        result = {}
        try:
            async with session.get(url, ssl=True, allow_redirects=False) as response:
                content = await response.read()
                decoded_content = None
                
                for encoding in COMMON_ENCODINGS:
                    try:
                        decoded_content = content.decode(encoding)
                        break
                    except UnicodeDecodeError:
                        continue
                
                if decoded_content is None:
                    detected_encoding = chardet.detect(content)['encoding']
                    decoded_content = content.decode(detected_encoding, errors='replace') if detected_encoding else content.decode('utf-8', errors='replace')

                result = {'URL': url, 'Filetype': response.headers.get('Content-Type', 'Unknown')}
                result['Category'] = 'readable' if 'text' in result['Filetype'] else 'non_readable'
                
                for keyword in keywords:
                    pattern = r'\b' + re.escape(keyword) + r'\b'
                    result[keyword] = len(re.findall(pattern, decoded_content, re.IGNORECASE))
                
                result['Error'] = 'No'
                result['Error Details'] = ''
                
        except Exception as e:
            result = {'URL': url, 'Filetype': 'Unknown', 'Category': 'Unknown', 'Error': 'Yes', 'Error Details': str(e)}
            # Initialize keyword counts to 0 in case of error
            for keyword in keywords:
                result[keyword] = 0

        results.append(result)
    return results

def write_to_csv(file_path, results, keywords):
    with open(file_path, 'w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=['URL', 'Category', 'Filetype', *keywords, 'Error', 'Error Details'])
        writer.writeheader()
        writer.writerows(results)

async def main():
    args = parse_arguments()
    
    if not validate_file(args.url) or not validate_file(args.keywords):
        print("URL or Keyword file not found or is not readable.")
        return
    
    urls = read_lines(args.url)
    keywords = read_lines(args.keywords)
    timeout = aiohttp.ClientTimeout(total=15)

    async with ClientSession(timeout=timeout) as session:
        results = await process_urls(urls, keywords, session)
        write_to_csv(args.output, results, keywords)

if __name__ == '__main__':
    asyncio.run(main())
