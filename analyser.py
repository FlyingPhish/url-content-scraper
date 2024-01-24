import argparse
import aiohttp
import asyncio
import chardet
import csv
import os
from typing import List
from aiohttp import ClientSession

COMMON_ENCODINGS = ['utf-8', 'iso-8859-1', 'windows-1252', 'utf-16', 'utf-16' 'ascii']

# COMMON_ENCODINGS = [
#     'utf-8',
#     'iso-8859-1',
#     'iso-8859-2',
#     'iso-8859-5',
#     'iso-8859-7',
#     'iso-8859-9',
#     'iso-8859-15',
#     'windows-1250',
#     'windows-1251',
#     'windows-1252',
#     'windows-1253',
#     'windows-1254',
#     'windows-1255',
#     'windows-1256',
#     'windows-1257',
#     'windows-1258',
#     'koi8-r',
#     'koi8-u',
#     'macintosh',
#     'utf-16',
#     'utf-32',
#     'ascii'
# ]

# Function to parse arguments
def parse_arguments():
    parser = argparse.ArgumentParser(description='Process URL and keyword files.')
    parser.add_argument('-u', '--url', required=True, help='File with URLs')
    parser.add_argument('-kw', '--keywords', required=True, help='File with keywords')
    parser.add_argument('-o', '--output', required=True, help='Output CSV file path')
    return parser.parse_args()

# Function to validate files
def validate_file(file_path):
    return os.path.exists(file_path) and os.path.isfile(file_path)

# Function to read lines from a file
def read_lines(file_path) -> List[str]:
    with open(file_path, 'r') as file:
        return [line.strip() for line in file.readlines()]

# Asynchronous function to process URLs
async def process_urls(urls, keywords, session):
    results = []
    for url in urls:
        print("Analysing: " + url)
        try:
            async with session.get(url, ssl=False) as response:
                content = await response.read()
                decoded_content = None
                
                # Try decoding with common encodings
                for encoding in COMMON_ENCODINGS:
                    try:
                        decoded_content = content.decode(encoding)
                        break
                    except UnicodeDecodeError:
                        continue
                
                # If none of the common encodings worked, use chardet
                if decoded_content is None:
                    detected_encoding = chardet.detect(content)['encoding']
                    if detected_encoding:
                        decoded_content = content.decode(detected_encoding, errors='replace')
                    else:
                        # If chardet could not detect encoding, decode with utf-8 and replace errors
                        decoded_content = content.decode('utf-8', errors='replace')

                result = {'URL': url, 'Filetype': response.headers.get('Content-Type', 'Unknown')}
                result['Category'] = 'readable' if 'text' in result['Filetype'] or 'pdf' in result['Filetype'] else 'non_readable'
                
                for keyword in keywords:
                    result[keyword] = decoded_content.count(keyword)
                    
                result['Error'] = 'No'
                result['Error Details'] = ''
                
        except Exception as e:
            result = {'URL': url, 'Filetype': 'Unknown', 'Category': 'Unknown', 'Error': 'Yes', 'Error Details': str(e)}
            for keyword in keywords:
                result[keyword] = 0

        results.append(result)
    return results

# Function to write results to CSV
def write_to_csv(file_path, results, keywords):
    with open(file_path, 'w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=['URL', 'Category', 'Filetype', *keywords, 'Error', 'Error Details'])
        writer.writeheader()
        writer.writerows(results)

# Main async function
async def main():
    args = parse_arguments()
    
    if not validate_file(args.url) or not validate_file(args.keywords):
        print("URL or Keyword file not found or is not readable.")
        return
    
    urls = read_lines(args.url)
    keywords = read_lines(args.keywords)
    timeout = aiohttp.ClientTimeout(total=15)

    # Pass the timeout to the ClientSession
    async with ClientSession(timeout=timeout) as session:
        results = await process_urls(urls, keywords, session)
        write_to_csv(args.output, results, keywords)

# Run the async main function
if __name__ == '__main__':
    asyncio.run(main())
