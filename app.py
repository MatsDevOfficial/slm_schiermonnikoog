import requests
from bs4 import BeautifulSoup
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# URLs over Schiermonnikoog
default_urls = [
    "https://www.vvvschiermonnikoog.nl/",
    "https://www.np-schiermonnikoog.nl/",
    "https://nl.wikipedia.org/wiki/Schiermonnikoog",
    "https://www.waddenvereniging.nl/eilanden/schiermonnikoog"
]

def get_paragraphs_from_url(url):
    try:
        resp = requests.get(url, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')
        paras = [p.get_text().strip() for p in soup.find_all('p') if p.get_text().strip()]
        return paras
    except Exception as e:
        print(f"Fout bij scrapen van {url}: {e}")
        return []

def build_corpus_list(urls):
    corpus = []
    print("Scrapen van websites, dit kan even duren...")
    for url in urls:
        paras = get_paragraphs_from_url(url)
        for para in paras:
            corpus.append((url, para))
    print(f"Klaar met scrapen, verzamelde {len(corpus)} paragrafen.")
    return corpus

def retrieve_relevant_info(question, corpus, top_k=3):
    if not corpus:
        return []
    texts = [t for (_, t) in corpus]
    vectorizer = TfidfVectorizer().fit(texts + [question])
    vectors = vectorizer.transform(texts + [question])
    sims = cosine_similarity(vectors[-1], vectors[:-1])[0]
    top_indices = sims.argsort()[-top_k:][::-1]
    relevant = [corpus[idx][1] for idx in top_indices if sims[idx] > 0.1]
    return relevant

# Laad GPT-2 lokaal
tokenizer = AutoTokenizer.from_pretrained("gpt2")
model = AutoModelForCausalLM.from_pretrained("gpt2")
generator = pipeline(
    "text-generation",
    model=model,
    tokenizer=tokenizer,
    device=-1  # CPU (pas aan als je GPU hebt)
)

def generate_answer(context, question):
    prompt = (
        f"Je bent een AI die alleen in het Nederlands antwoordt. "
        f"Gebruik deze informatie:\n{context}\n\n"
        f"Vraag: {question}\nAntwoord:"
    )
    output = generator(
        prompt,
        max_new_tokens=256,
        num_return_sequences=1,
        temperature=0.2,
        pad_token_id=tokenizer.eos_token_id,
        truncation=True,
    )
    text = output[0]['generated_text']
    if "Antwoord:" in text:
        antwoord = text.split("Antwoord:")[1].split("\n")[0].strip()
    else:
        antwoord = text.strip()
    return antwoord


def chat():
    corpus = build_corpus_list(default_urls)
    print("🤖 Schiermonnikoog AI gestart. Typ 'stop' om te stoppen.")
    while True:
        vraag = input("Jij: ")
        if vraag.lower() in ('stop', 'exit', 'quit'):
            print("👋 Tot ziens!")
            break
        relevante_passages = retrieve_relevant_info(vraag, corpus)
        if not relevante_passages:
            print("Bot: Sorry, ik kon geen relevante info vinden.\n")
            continue
        context = " ".join(relevante_passages)
        antwoord = generate_answer(context, vraag)
        print(f"Bot: {antwoord}\n")

if __name__ == "__main__":
    chat()
