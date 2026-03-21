"""
Robust Educational Content Scraper (2026)
Uses multiple sources and fallbacks to ensure data is collected
"""

import requests
from bs4 import BeautifulSoup
import json
import sys
import datetime


import re

def _scrape_youtube_playlists(topic):
    """
    Scrape YouTube search results for playlists without using an API key
    """
    print(f"  🔍 Scraping YouTube for '{topic}' playlists...")
    playlists = []
    try:
        search_query = f"{topic.replace(' ', '+')}+playlist"
        url = f"https://www.youtube.com/results?search_query={search_query}&sp=EgIQAw%253D%253D" # sp=EgIQAw%3D%3D filters for playlists
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            return []
            
        # YouTube embeds data in a JSON object in the source
        html = response.text
        json_str = re.search(r'var ytInitialData = (\{.*?\});', html)
        if not json_str:
            return []
            
        data = json.loads(json_str.group(1))
        
        # Traverse the complex YouTube JSON structure to find playlist items
        contents = data.get('contents', {}).get('twoColumnBrowseResultsRenderer', {}).get('tabs', [{}])[0].get('content', {}).get('sectionListRenderer', {}).get('contents', [])
        if not contents:
            # Try alternative path
            contents = data.get('contents', {}).get('twoColumnSearchResultsRenderer', {}).get('primaryContents', {}).get('sectionListRenderer', {}).get('contents', [])
            
        for section in contents:
            items = section.get('itemSectionRenderer', {}).get('contents', [])
            for item in items:
                playlist_data = item.get('playlistRenderer')
                if playlist_data:
                    p_id = playlist_data.get('playlistId')
                    title = playlist_data.get('title', {}).get('runs', [{}])[0].get('text', 'Unknown Playlist')
                    channel = playlist_data.get('longBylineText', {}).get('runs', [{}])[0].get('text', 'Unknown Channel')
                    
                    playlists.append({
                        'url': f"https://www.youtube.com/playlist?list={p_id}",
                        'title': title,
                        'channel': channel,
                        'source': 'youtube_search'
                    })
                    
                    if len(playlists) >= 10:
                        break
            if len(playlists) >= 10:
                break
                
    except Exception as e:
        print(f"  ✗ YouTube scraping failed: {e}")
        
    return playlists

def get_tutorials_from_multiple_sources(topic):
    """
    Get tutorials from multiple reliable sources
    """
    print(f"Scraping {topic} tutorials from multiple sources...")
    tutorials = []
    
    # Source 1: Curated educational sites (always works)
    curated_sites = {
        'python': [
            {'url': 'https://docs.python.org/3/tutorial/', 'title': 'Official Python Tutorial', 'source': 'python.org'},
            {'url': 'https://www.w3schools.com/python/', 'title': 'W3Schools Python', 'source': 'w3schools'},
            {'url': 'https://realpython.com/', 'title': 'Real Python', 'source': 'realpython'},
            {'url': 'https://www.learnpython.org/', 'title': 'Learn Python', 'source': 'learnpython.org'},
            {'url': 'https://www.programiz.com/python-programming', 'title': 'Programiz Python', 'source': 'programiz'},
        ],
        'javascript': [
            {'url': 'https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide', 'title': 'MDN JavaScript Guide', 'source': 'MDN'},
            {'url': 'https://javascript.info/', 'title': 'The Modern JavaScript Tutorial', 'source': 'javascript.info'},
            {'url': 'https://www.w3schools.com/js/', 'title': 'W3Schools JavaScript', 'source': 'w3schools'},
        ],
        'data science': [
            {'url': 'https://www.kaggle.com/learn', 'title': 'Kaggle Learn', 'source': 'kaggle'},
            {'url': 'https://www.datacamp.com/courses', 'title': 'DataCamp Courses', 'source': 'datacamp'},
            {'url': 'https://www.coursera.org/browse/data-science', 'title': 'Coursera Data Science', 'source': 'coursera'},
        ],
        'machine learning': [
            {'url': 'https://www.coursera.org/learn/machine-learning', 'title': 'Andrew Ng ML Course', 'source': 'coursera'},
            {'url': 'https://www.kaggle.com/learn/intro-to-machine-learning', 'title': 'Kaggle ML', 'source': 'kaggle'},
            {'url': 'https://developers.google.com/machine-learning/crash-course', 'title': 'Google ML Crash Course', 'source': 'google'},
        ],
        'web development': [
            {'url': 'https://www.freecodecamp.org/', 'title': 'freeCodeCamp', 'source': 'freecodecamp'},
            {'url': 'https://www.theodinproject.com/', 'title': 'The Odin Project', 'source': 'theodinproject'},
            {'url': 'https://developer.mozilla.org/en-US/docs/Learn', 'title': 'MDN Web Docs', 'source': 'MDN'},
        ]
    }
    
    # Check if we have curated content for this topic
    topic_lower = topic.lower()
    for key in curated_sites:
        if key in topic_lower or topic_lower in key:
            tutorials.extend(curated_sites[key])
            print(f"  ✓ Added {len(curated_sites[key])} curated tutorials")
            break
    
    # Source 2: Try to scrape from FreeCodeCamp
    try:
        search_url = f"https://www.freecodecamp.org/news/search/?query={topic.replace(' ', '%20')}"
        response = requests.get(
            search_url,
            timeout=10,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        )
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Try multiple selectors
            articles = soup.find_all('article', limit=5)
            if not articles:
                articles = soup.find_all('a', class_='post-card', limit=5)
            
            for article in articles:
                try:
                    link = article.find('a')
                    if link:
                        href = link.get('href', '')
                        title = link.get_text(strip=True) or article.get_text(strip=True)[:100]
                        
                        if href and title:
                            full_url = f"https://www.freecodecamp.org{href}" if href.startswith('/') else href
                            tutorials.append({
                                'url': full_url,
                                'title': title,
                                'source': 'freecodecamp'
                            })
                except:
                    continue
            
            if articles:
                print(f"  ✓ Scraped {len(articles)} articles from FreeCodeCamp")
    except Exception as e:
        print(f"  ✗ FreeCodeCamp scraping failed: {e}")
    
    # Source 3: Generic educational sites
    generic_sites = [
        {'url': f'https://www.tutorialspoint.com/{topic.replace(" ", "-").lower()}/index.htm', 
         'title': f'TutorialsPoint {topic}', 'source': 'tutorialspoint'},
        {'url': f'https://www.geeksforgeeks.org/{topic.replace(" ", "-").lower()}/', 
         'title': f'GeeksforGeeks {topic}', 'source': 'geeksforgeeks'},
    ]
    
    for site in generic_sites:
        try:
            response = requests.head(site['url'], timeout=5)
            if response.status_code == 200:
                tutorials.append(site)
        except:
            pass
    
    print(f"  ✓ Total tutorials found: {len(tutorials)}")
    return tutorials


def get_youtube_playlists(topic):
    """
    Get YouTube playlists - provides curated lists and API instructions
    """
    print(f"Getting {topic} YouTube playlists...")
    
    playlists = []
    
    # Curated playlists for common topics
    curated_playlists = {
        'python': [
            {'url': 'https://www.youtube.com/playlist?list=PLu0W_9lII9agiCUZYRsvtGTXdxkzPyItg', 
             'title': 'Python Tutorial - CodeWithHarry', 'channel': 'CodeWithHarry'},
            {'url': 'https://www.youtube.com/playlist?list=PL-osiE80TeTt2d9bfVyTiXJA-UTHn6WwU', 
             'title': 'Python Tutorial - Corey Schafer', 'channel': 'Corey Schafer'},
            {'url': 'https://www.youtube.com/playlist?list=PLWKjhJtqVAbnqBxcdjVGgT3uVR10bzTEB', 
             'title': 'Python for Everybody', 'channel': 'freeCodeCamp'},
        ],
        'javascript': [
            {'url': 'https://www.youtube.com/playlist?list=PLu0W_9lII9ahR1blWXxgSlL4y9iQBnLpR', 
             'title': 'JavaScript Tutorial', 'channel': 'CodeWithHarry'},
            {'url': 'https://www.youtube.com/playlist?list=PL4cUxeGkcC9haFPT7J25Q9GRB_ZkFrQAc', 
             'title': 'JavaScript Tutorial for Beginners', 'channel': 'The Net Ninja'},
        ],
        'data science': [
            {'url': 'https://www.youtube.com/playlist?list=PLeo1K3hjS3us_ELKYSj_Fth2tIEkdKXvV', 
             'title': 'Data Science Full Course', 'channel': 'codebasics'},
            {'url': 'https://www.youtube.com/playlist?list=PLZoTAELRMXVPBTrWtJkn3wWQxZkmTXGwe', 
             'title': 'Data Science Tutorial', 'channel': 'Krish Naik'},
        ],
        'machine learning': [
            {'url': 'https://www.youtube.com/playlist?list=PLZoTAELRMXVPBTrWtJkn3wWQxZkmTXGwe', 
             'title': 'Machine Learning Tutorial', 'channel': 'Krish Naik'},
            {'url': 'https://www.youtube.com/playlist?list=PLeo1K3hjS3uvCeTYTeyfe0-rN5r8zn9rw', 
             'title': 'Machine Learning Full Course', 'channel': 'codebasics'},
        ],
        'web development': [
            {'url': 'https://www.youtube.com/playlist?list=PLu0W_9lII9agiCUZYRsvtGTXdxkzPyItg', 
             'title': 'Web Development Tutorial', 'channel': 'CodeWithHarry'},
            {'url': 'https://www.youtube.com/playlist?list=PL4cUxeGkcC9ivBf_eKCPIAYXWzLlPAm6G', 
             'title': 'Full Stack Web Development', 'channel': 'The Net Ninja'},
        ]
    }
    
    # Check for curated playlists
    topic_lower = topic.lower()
    for key in curated_playlists:
        if key in topic_lower or topic_lower in key:
            playlists.extend(curated_playlists[key])
            print(f"  ✓ Added {len(curated_playlists[key])} curated playlists")
            break
    
    # If no curated playlists, scrape YouTube search results
    if not playlists:
        scraped_playlists = _scrape_youtube_playlists(topic)
        if scraped_playlists:
            playlists.extend(scraped_playlists)
            print(f"  ✓ Scraped {len(scraped_playlists)} playlists from YouTube search")
            
    # Final Fallback: Provide Google/YouTube search URLs if still nothing (unlikely)
    if not playlists:
        print(f"  ℹ No playlists found for '{topic}', providing search links")
        # Add generic search URL
        playlists.append({
            'url': f'https://www.youtube.com/results?search_query={topic.replace(" ", "+")}+playlist',
            'title': f'Search YouTube: {topic} playlists',
            'channel': 'YouTube Search'
        })
    
    print(f"  ✓ Total playlists found: {len(playlists)}")
    return playlists


def get_qa_content(topic):
    """
    Get Q&A content from Stack Overflow and Reddit
    """
    print(f"Getting {topic} Q&A content...")
    qa_content = []
    
    # Stack Overflow
    try:
        tag = topic.lower().replace(' ', '-')
        response = requests.get(
            'https://api.stackexchange.com/2.3/questions',
            params={
                'order': 'desc',
                'sort': 'votes',
                'tagged': tag,
                'site': 'stackoverflow',
                'pagesize': 10
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            for item in data.get('items', []):
                qa_content.append({
                    'title': item.get('title'),
                    'url': item.get('link'),
                    'score': item.get('score'),
                    'source': 'stackoverflow'
                })
            print(f"  ✓ Got {len(data.get('items', []))} Stack Overflow questions")
    except Exception as e:
        print(f"  ✗ Stack Overflow failed: {e}")
    
    # Reddit
    try:
        # Try topic-specific subreddit first
        subreddits = ['learnprogramming', 'programming', 'coding']
        
        for subreddit in subreddits:
            try:
                response = requests.get(
                    f'https://www.reddit.com/r/{subreddit}/search.json',
                    params={'q': topic, 'limit': 5, 'sort': 'top', 't': 'month'},
                    headers={'User-Agent': 'EducationalBot/1.0'},
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    posts = data.get('data', {}).get('children', [])
                    
                    for post in posts:
                        post_data = post.get('data', {})
                        qa_content.append({
                            'title': post_data.get('title'),
                            'url': f"https://www.reddit.com{post_data.get('permalink')}",
                            'score': post_data.get('score'),
                            'source': f'reddit-{subreddit}'
                        })
                    
                    if posts:
                        print(f"  ✓ Got {len(posts)} Reddit posts from r/{subreddit}")
                        break
            except:
                continue
                
    except Exception as e:
        print(f"  ✗ Reddit failed: {e}")
    
    print(f"  ✓ Total Q&A items found: {len(qa_content)}")
    return qa_content


def save_results(topic):
    """Save all scraped content"""
    print(f"\n{'='*60}")
    print(f"Scraping content for: {topic}")
    print(f"{'='*60}\n")
    
    tutorials = get_tutorials_from_multiple_sources(topic)
    playlists = get_youtube_playlists(topic)
    qa_content = get_qa_content(topic)
    
    # Save to files
    with open('../Articles/articles.txt', 'w', encoding='utf-8') as f:
        f.write(f"# {topic.title()} Tutorials\n")
        f.write(f"# Scraped: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        for item in tutorials:
            f.write(f"{item['url']}\n")
            f.write(f"  Title: {item['title']}\n")
            f.write(f"  Source: {item['source']}\n\n")
    
    with open('../Videos/playlist.txt', 'w', encoding='utf-8') as f:
        f.write(f"# {topic.title()} YouTube Playlists\n")
        f.write(f"# Scraped: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        for item in playlists:
            f.write(f"{item['url']}\n")
            f.write(f"  Title: {item['title']}\n")
            f.write(f"  Channel: {item.get('channel', 'N/A')}\n\n")
    
    with open('../Answers/answers.txt', 'w', encoding='utf-8') as f:
        f.write(f"# {topic.title()} Q&A\n")
        f.write(f"# Scraped: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        for item in qa_content:
            f.write(f"{item['title']}\n")
            f.write(f"  URL: {item['url']}\n")
            f.write(f"  Score: {item['score']}\n")
            f.write(f"  Source: {item['source']}\n\n")
    
    # Save JSON
    with open('../scraped_data.json', 'w', encoding='utf-8') as f:
        json.dump({
            'topic': topic,
            'tutorials': tutorials,
            'playlists': playlists,
            'qa_content': qa_content,
            'scraped_at': datetime.datetime.now().isoformat(),
            'summary': {
                'total_tutorials': len(tutorials),
                'total_playlists': len(playlists),
                'total_qa': len(qa_content)
            }
        }, f, indent=2)
    
    print(f"\n{'='*60}")
    print(f"✓ Saved {len(tutorials)} tutorials")
    print(f"✓ Saved {len(playlists)} playlists")
    print(f"✓ Saved {len(qa_content)} Q&A items")
    print(f"{'='*60}")
    print("\nFiles created:")
    print("  - Articles/articles.txt")
    print("  - Videos/playlist.txt")
    print("  - Answers/answers.txt")
    print("  - scraped_data.json")


if __name__ == "__main__":
    print("=" * 60)
    print("Robust Educational Content Scraper (2026)")
    print("=" * 60)
    print("\nFeatures:")
    print("  ✓ Multiple data sources")
    print("  ✓ Curated content for popular topics")
    print("  ✓ Fallback mechanisms")
    print("  ✓ Works even if some sources fail")
    print("\n" + "=" * 60 + "\n")
    
    # Get topic
    if len(sys.argv) > 1:
        topic = " ".join(sys.argv[1:])
    else:
        topic = input("Enter topic (e.g., 'Python', 'Machine Learning', 'Web Development'): ").strip()
        if not topic:
            topic = "Python"
    
    try:
        save_results(topic)
        print("\n✓ Scraping completed successfully!")
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
