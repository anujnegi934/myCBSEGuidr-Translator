from bs4 import BeautifulSoup

def analyze():
    print("Reading debug_page.html...")
    with open("debug_page.html", "r", encoding="utf-8") as f:
        html = f.read()
    
    soup = BeautifulSoup(html, 'html.parser')
    
    print("\n--- Textareas ---")
    for tag in soup.find_all('textarea'):
        print(f"ID: {tag.get('id')} | Name: {tag.get('name')}")
        print(f"Content: {tag.get_text()[:100]}...\n")
        
    print("\n--- Iframes ---")
    for tag in soup.find_all('iframe'):
        print(f"ID: {tag.get('id')} | Class: {tag.get('class')} | Title: {tag.get('title')}")

if __name__ == "__main__":
    analyze()
