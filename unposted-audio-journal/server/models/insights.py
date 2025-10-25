from transformers import pipeline

print("Loading summarizer...")
summarizer = pipeline("summarization", model="facebook/bart-large-cnn", device=-1)

def generate_insights(text):
    sentences = [s.strip() + '.' for s in text.split('.') if len(s.strip()) > 20][:3]

    if len(sentences) < 3 and len(text) > 100:
        summary = summarizer(text, max_length=100, min_length=30)
        s_text = summary[0]['summary_text']
        sentences = [s.strip() + '.' for s in s_text.split('.') if s.strip()][:3]

    while len(sentences) < 3:
        sentences.append("Reflect on your day.")
    
    return sentences[:3]
