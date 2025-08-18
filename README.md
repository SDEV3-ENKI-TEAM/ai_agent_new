# ai_agent_new
AI agent test

.env 파일은 다음과 같이 설정하면 됩니다.
# OpenAI
OPENAI_API_KEY=sk~
CHAT_MODEL=gpt-4o
EMBED_MODEL=text-embedding-3-small

# OpenSearch
OPENSEARCH_HOST=search-eventagentservice-px5xppytlfm2nbijkhrd2z7lp4.ap-northeast-2.es.amazonaws.com
OPENSEARCH_PORT=443
OPENSEARCH_USER=admin
OPENSEARCH_PASS=admin123  # (AWS IAM 연동이면 제거하고 SigV4 인증으로 가야 함)

# Chroma (벡터DB)
CHROMA_HOST=localhost
CHROMA_PORT=8000
CHROMA_COLLECTION=my_log_db
CHROMA_OPENAI_API_KEY=sk~

# Kafka
### 도커 내부에서 실행 시: kafka:9092
### 로컬에서 실행 시: localhost:9092
KAFKA_BOOTSTRAP=kafka:9092

RAW_TOPIC=raw_trace
SUMMARY_TOPIC=trace_summary   

### Trace 처리 parameter
TRACE_INACTIVITY_SEC=5        
TRACE_MAX_EVENTS=500          
FLUSH_TICK_SEC=1.0            


실행시 -> python3 kafka_trace_consumer.py 
