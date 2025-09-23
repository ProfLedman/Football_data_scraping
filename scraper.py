import requests
from bs4 import BeautifulSoup

url = "https://fbref.com/en/matches/"
headers = {"User-Agent": "Mozilla/5.0"}
fixtures = []

try:
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()  # raise error for bad responses
    soup = BeautifulSoup(response.content, "html.parser")
except requests.RequestException as e:
    print(f"Error fetching {url}: {e}")
    fixtures = []

# Loop through each competition section
for header in soup.find_all("h2"):
    competition = header.get_text(strip=True).replace(" Scores & Fixtures", "")
    table = header.find_next("table")
    if not table:
        continue

    # Extract headers from the table
    try:
        headers_row = [th.get_text(strip=True) for th in table.find("thead").find_all("th")]
    except AttributeError:
        print(f"No headers found for {competition}, skipping...")
        continue

    tbody = table.find("tbody")
    if not tbody:
        continue

    for row in tbody.find_all("tr"):
        cells = row.find_all("td")
        if not cells:
            continue  # skip header/separator rows

        row_data = {"Competition": competition}

        # Map cells to their respective headers
        for i, cell in enumerate(cells):
            col_name = headers_row[i+1] if i+1 < len(headers_row) else f"Col_{i}"
            row_data[col_name] = cell.get_text(strip=True) if cell else None

            # Capture match link if available
            link = cell.find("a")
            if link and "href" in link.attrs:
                row_data[f"{col_name}_URL"] = "https://fbref.com" + link["href"]

        fixtures.append(row_data)

# Preview results
print(f"Collected {len(fixtures)} fixtures")
if fixtures:
    for fix in fixtures[:5]:
        print(fix)
