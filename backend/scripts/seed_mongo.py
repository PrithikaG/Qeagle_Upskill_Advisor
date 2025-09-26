import os, json
from pymongo import MongoClient, UpdateOne
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
load_dotenv()

HERE = os.path.dirname(__file__)
APP_DIR = os.path.abspath(os.path.join(HERE, "..", "app"))
DATA_DIR = os.path.join(APP_DIR, "data")

MONGO_URI = os.getenv("MONGODB_ATLAS_URI")
DB_NAME = os.getenv("MONGODB_DB", "upskill")
COLL_NAME = os.getenv("MONGODB_COURSES_COLL", "courses")


def load_courses():
    p = os.path.join(DATA_DIR, "courses.json")
    with open(p, "r", encoding="utf-8") as f:
        raw = json.load(f)
        if not isinstance(raw, list): return []
        return raw

def course_text(c):
    return " ".join([
        c.get("title",""),
        " ".join(c.get("skills",[]) or []),
        " ".join(c.get("outcomes",[]) or [])
    ]).strip()

def main():
    if not MONGO_URI:
        raise SystemExit("MONGO_URI not set in environment")
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    coll = db[COLL_NAME]

    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

    courses = load_courses()
    if not courses:
        print("No courses to seed.")
        return

    ops = []
    for c in courses:
        text = course_text(c)
        emb = model.encode(text).tolist()
        doc = {**c, "embedding": emb}
        ops.append(
            UpdateOne({"course_id": c["course_id"]}, {"$set": doc}, upsert=True)
        )

    if ops:
        res = coll.bulk_write(ops, ordered=False)
        print("Upserted:", res.upserted_count, "Modified:", res.modified_count)
    else:
        print("No operations.")

if __name__ == "__main__":
    main()
