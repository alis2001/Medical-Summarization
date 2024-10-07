import pinecone
from sentence_transformers import SentenceTransformer

PINECONE_KEY = '90984d77-7754-4bb6-9c65-254df9459676'
#PINECONE_KEY =  'f388dcc0-9f94-48aa-81a4-10a6c873141d'
pinecone.init(api_key=PINECONE_KEY, environment='us-west1-gcp')

index_name = 'example-index'
if index_name not in pinecone.list_indexes():
    pinecone.create_index(index_name, dimension=768, metric='cosine', pod_type='p1')

index = pinecone.Index(index_name)

model = SentenceTransformer('all-MiniLM-L6-v2')

texts = [
    "Climate change refers to long-term shifts in temperatures and weather patterns. These changes may be natural, such as through variations in the solar cycle. However, since the 1800s, human activities have been the main driver of climate change, primarily due to burning fossil fuels like coal, oil, and gas.",
    "Artificial Intelligence (AI) is the simulation of human intelligence in machines that are programmed to think and learn. It involves machine learning, where algorithms use data to improve. AI is used in various applications including speech recognition, image processing, and autonomous vehicles.",
    "Renewable energy comes from sources that are naturally replenishing such as sunlight, wind, rain, tides, and geothermal heat. This energy is sustainable and can be used to produce electricity, heat, and transportation fuels, thus reducing reliance on fossil fuels.",
    "Space exploration is the investigation of outer space through manned and unmanned spacecraft. It includes the study of celestial bodies and the universe beyond Earth's atmosphere. Notable milestones include the moon landing in 1969 and the ongoing Mars exploration missions."
]

for i, text in enumerate(texts):
    embedding = model.encode(text).tolist()
    index.upsert([{
        'id': f'id-{i}',
        'values': embedding,
        'metadata': {'text': text}
    }])

def chatbot(query):
    query_embedding = model.encode(query).tolist()
    result = index.query(queries=[query_embedding], top_k=1, include_metadata=True)
    return result['matches'][0]['metadata']['text']

query = "Tell me about climate change"
response = chatbot(query)
print(response)
