import chromadb, json
from tqdm import tqdm


if __name__ == "__main__":
    data_path = "data/stocks_labelled.json"
    database_path = "chromadb"
    batch_size = 10


    chroma_client = chromadb.PersistentClient(path=database_path)
    try:
        chroma_client.delete_collection("posts")
        chroma_client.delete_collection("comments")
    except:
        print("No existing collection found.")
    collection_posts = chroma_client.create_collection(name="posts")
    collection_comments = chroma_client.create_collection(name="comments")

    with open(data_path, "r", encoding="utf-8") as f:
        posts_json = json.load(f)

    
    for i in tqdm(range(0, len(posts_json), batch_size)):
        batch_posts = posts_json[i:i + batch_size]
        
        post_documents = []
        post_ids = []
        post_metadatas = []
        
        comment_documents = []
        comment_ids = []
        comment_metadatas = []
        
        for post in batch_posts:
            # Ingest post data into the ChromaDB collections
            post_id = post["id"]
            post_title = post["title"]
            post_text = post["text"]
            post_date = post["date"]
            post_score = post["score"]
            post_url = post["url"]
            post_upvotes = post["upvotes"]
            post_downvotes = post["downvotes"]
            post_num_comments = post["num_comments"]
            post_comment_ids = ",".join([comment["id"] for comment in post["comments"]])
            post_tickers = ",".join(post["tickers"])
            post_bullish_count = post["bullish_count"]
            post_neutral_count = post["neutral_count"]
            post_bearish_count = post["bearish_count"]
            post_comments = post["comments"]

            # Prepare post data for batch addition
            post_documents.append(post_title + " " + post_text)
            post_ids.append(post_id)
            post_metadatas.append({
                "title": post_title,
                "text": post_text,
                "date": post_date,
                "score": post_score,
                "url": post_url,
                "upvotes": post_upvotes,
                "downvotes": post_downvotes,
                "num_comments": post_num_comments,
                "comment_ids": post_comment_ids,
                "tickers": post_tickers,
                "bullish_count": post_bullish_count,
                "neutral_count": post_neutral_count,
                "bearish_count": post_bearish_count
            })

            # Prepare comments data for batch addition
            for comment in post_comments:
                comment_id = comment["id"]
                comment_text = comment["text"]
                comment_score = comment["score"]
                comment_sentiment = comment["sentiment"]
                
                comment_documents.append(comment_text)
                comment_ids.append(comment_id)
                comment_metadatas.append({
                    "post_id": post_id,
                    "score": comment_score,
                    "sentiment": comment_sentiment,
                    "text": comment_text
                })
        
        # Add posts to the posts collection with metadata in batch
        collection_posts.add(
            documents=post_documents,
            ids=post_ids,
            metadatas=post_metadatas
        )
        
        # Add comments to the comments collection with metadata in batch
        collection_comments.add(
            documents=comment_documents,
            ids=comment_ids,
            metadatas=comment_metadatas
        )