import os
import csv

# --- Functions to Test (Copied from ingest_teacher_data.py) ---

def init_csv():
    # Check if file exists, if not create with headers
    if not os.path.exists('question_bank.csv'):
        with open('question_bank.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['book_name', 'difficulty', 'question', 'opt_a', 'opt_b', 'opt_c', 'opt_d', 'answer'])

def save_batch_to_csv(questions, book_name):
    # Determine if we need to write headers (in case file was deleted)
    file_exists = os.path.exists('question_bank.csv')
    
    with open('question_bank.csv', 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # If file didn't exist, we just created it in append mode, but it might be empty if we didn't use init_csv properly before.
        # However, init_csv is called at startup. If deleted mid-run, this handles it partially, but let's rely on init_csv.
        if not file_exists:
            writer.writerow(['book_name', 'difficulty', 'question', 'opt_a', 'opt_b', 'opt_c', 'opt_d', 'answer'])
            
        count = 0
        for q in questions:
            if 'question' in q and 'answer' in q:
                writer.writerow([
                    book_name, 
                    q.get('difficulty', 'Medium'), 
                    q['question'], 
                    q.get('opt_a', ''), 
                    q.get('opt_b', ''), 
                    q.get('opt_c', ''), 
                    q.get('opt_d', ''), 
                    q['answer']
                ])
                count += 1
    print(f"      ✅ Saved {count} questions to CSV.")

# --- End of Functions ---

def test_csv_creation_and_saving():
    # Cleanup previous run
    if os.path.exists("question_bank.csv"):
        os.remove("question_bank.csv")
        print("Removed existing question_bank.csv")

    # 1. Initialize CSV
    print("Initializing CSV...")
    init_csv()
    
    if not os.path.exists("question_bank.csv"):
        print("❌ FAILED: question_bank.csv was not created.")
        return

    # 2. Save a batch of questions
    print("Saving a batch of questions...")
    dummy_questions = [
        {
            "question": "What is 2+2?",
            "opt_a": "1", "opt_b": "2", "opt_c": "3", "opt_d": "4",
            "answer": "D",
            "difficulty": "Easy"
        },
        {
            "question": "What is the capital of France?",
            "opt_a": "London", "opt_b": "Berlin", "opt_c": "Paris", "opt_d": "Madrid",
            "answer": "C",
            "difficulty": "Medium"
        }
    ]
    
    save_batch_to_csv(dummy_questions, "Test Book")
    
    # 3. Verify content
    print("Verifying content...")
    with open("question_bank.csv", "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        rows = list(reader)
        
        # Check header
        expected_header = ['book_name', 'difficulty', 'question', 'opt_a', 'opt_b', 'opt_c', 'opt_d', 'answer']
        if rows[0] != expected_header:
            print(f"❌ FAILED: Header mismatch.\nExpected: {expected_header}\nGot: {rows[0]}")
            return
            
        # Check data count
        if len(rows) != 3: # Header + 2 data rows
            print(f"❌ FAILED: Expected 3 rows, got {len(rows)}")
            return
            
        # Check specific data
        if rows[1][0] != "Test Book" or rows[1][2] != "What is 2+2?":
            print(f"❌ FAILED: Data mismatch in row 1: {rows[1]}")
            return
            
        if rows[2][7] != "C":
             print(f"❌ FAILED: Data mismatch in row 2 (answer): {rows[2]}")
             return

    print("✅ SUCCESS: CSV creation and saving verified!")

if __name__ == "__main__":
    test_csv_creation_and_saving()
