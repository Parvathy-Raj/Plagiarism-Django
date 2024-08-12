from django.http import HttpResponse
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from googlesearch import search
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import json  
from requests.exceptions import ReadTimeout
import sqlite3
from plag.models import PlagData

def fetch_data_from_database():
    conn = sqlite3.connect('journal.db')  # Connect database
    cursor = conn.cursor()
    # Retrieve content from a table named 'journalDB'
    cursor.execute("SELECT content , paper_name , author FROM journalDB")
    rows = cursor.fetchall()
    # Extract content from database rows
    database_data = [{'content': row[0], 'paper_name': row[1], 'author': row[2]} for row in rows]
    conn.close()
    
    return database_data 

def search_and_similarity(line, user_id):
    unique_domains = {}
    report = {}
    distinct_domains = set()
    print("Search started")
    report['query'] = line
    lines_source = []
    report['lines_source'] = []
    line_part = line.split('.')

    for url in search(line, num_results=2):
        if url.strip():  # Check if URL is not empty or whitespace
            print(url)
            parsed_url = urlparse(url)
            domain = parsed_url.netloc
            
            for line_part in line.split('.'):   #split the text into parts
                line_source_entry = {"line_part": line_part , "url": url}
                lines_source.append(line_source_entry)
                report['lines_source'].append(line_source_entry)
                
            unique_domains[domain] = unique_domains.get(domain, 0) + 1
            distinct_domains.add(domain) 
            print(domain)
            lines_source.append({"line": line, "url": url})
            report['urls'] = report.get('urls', [])
            report['urls'].append(url)
            report['domains'] = [{'domain': domain, 'count': count} for domain, count in unique_domains.items()]
            try :
                r = requests.get(url , timeout=30 )  # Search in Google
                soup = BeautifulSoup(r.content, "html.parser")
                paragraphs = soup.find_all("p")
                report['corpus_data'] = ' '.join([paragraph.get_text() for paragraph in paragraphs])
            except ReadTimeout:
                report['corpus_data'] = ""
        else:
            print("No plagiarism found")
           
    report['distinct_domain_count'] = len(distinct_domains)
    text1 = (report['corpus_data'])

    database_data = fetch_data_from_database()
    # Calculating similarity with database 
    max_similarity = 0
    for data in database_data:
        text3 = data['content']  #'content' is the field in the database
        text2 = line
        vectorizer = CountVectorizer()
        tf_matrix = vectorizer.fit_transform([text3, text2])
        cosine_sim = cosine_similarity(tf_matrix[0], tf_matrix[1])[0][0]
        max_similarity = max(max_similarity, cosine_sim)
        if max_similarity != 0 :
            report['paper_name'] = data['paper_name']
            report['author'] = data['author']
        
    db_similarity = max_similarity * 100

    print("similarity checking")

    text2 = line
    print(text2)
        # Create a TF-IDF vectorizer    
    vectorizer = CountVectorizer()
        # Fit and transform the documents into TF vectors
    tf_matrix = vectorizer.fit_transform([text1, text2])
        # Compute cosine similarity between the TF vectors
    cosine_sim = cosine_similarity(tf_matrix[0], tf_matrix[1])[0][0]
        # Calculating plagiarism percentage
    sim_percent = cosine_sim * 100

#calcaluting overall plagiarism percentage
    if db_similarity == 0 :
        plag_percent = sim_percent
    elif sim_percent == 0 :
        plag_percent = db_similarity
    else :
        plag_percent = (sim_percent+db_similarity)/2
        

    report['plag_percent'] = plag_percent

    plag_data = PlagData(
        user_id=user_id,
        plag_percentage=plag_percent,
        number_of_words=len(line.split()),
        similarity_score=cosine_sim,
        text=line
    )
    plag_data.save()
    
    return report 


