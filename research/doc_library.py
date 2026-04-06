"""内置技术文档库，提供主题匹配搜索。"""

# 文档库：key 为标识符，value 包含名称、URL、标签
DOCS_LIBRARY = {
    # 深度学习框架
    "pytorch": {
        "name": "PyTorch",
        "url": "https://pytorch.org/docs/stable/index.html",
        "tags": ["深度学习", "神经网络", "机器学习", "deep learning", "neural network"],
    },
    "tensorflow": {
        "name": "TensorFlow",
        "url": "https://www.tensorflow.org/api_docs",
        "tags": ["深度学习", "机器学习", "deep learning", "machine learning"],
    },
    "keras": {
        "name": "Keras",
        "url": "https://keras.io/api/",
        "tags": ["深度学习", "神经网络", "deep learning"],
    },
    "jax": {
        "name": "JAX",
        "url": "https://jax.readthedocs.io/",
        "tags": ["深度学习", "自动微分", "deep learning", "autodiff"],
    },

    # LLM 工具链
    "langchain": {
        "name": "LangChain",
        "url": "https://python.langchain.com/docs/",
        "tags": ["llm", "大模型", "agent", "rag", "链式调用"],
    },
    "llamaindex": {
        "name": "LlamaIndex",
        "url": "https://docs.llamaindex.ai/",
        "tags": ["llm", "rag", "检索增强", "索引", "retrieval"],
    },
    "huggingface": {
        "name": "Hugging Face Transformers",
        "url": "https://huggingface.co/docs/transformers/",
        "tags": ["llm", "transformer", "预训练模型", "nlp"],
    },
    "openai": {
        "name": "OpenAI API",
        "url": "https://platform.openai.com/docs/",
        "tags": ["gpt", "llm", "api", "chatgpt"],
    },
    "anthropic": {
        "name": "Anthropic Claude API",
        "url": "https://docs.anthropic.com/",
        "tags": ["claude", "llm", "api"],
    },

    # 强化学习
    "stable-baselines3": {
        "name": "Stable-Baselines3",
        "url": "https://stable-baselines3.readthedocs.io/",
        "tags": ["强化学习", "rl", "reinforcement learning", "policy"],
    },
    "ray-rllib": {
        "name": "Ray RLlib",
        "url": "https://docs.ray.io/en/latest/rllib/",
        "tags": ["强化学习", "rl", "分布式", "reinforcement learning"],
    },
    "gymnasium": {
        "name": "Gymnasium (OpenAI Gym)",
        "url": "https://gymnasium.farama.org/",
        "tags": ["强化学习", "rl", "环境", "environment"],
    },

    # 计算机视觉
    "opencv": {
        "name": "OpenCV",
        "url": "https://docs.opencv.org/",
        "tags": ["计算机视觉", "图像处理", "computer vision", "cv"],
    },
    "mmdetection": {
        "name": "MMDetection",
        "url": "https://mmdetection.readthedocs.io/",
        "tags": ["目标检测", "计算机视觉", "detection", "cv"],
    },

    # NLP
    "spacy": {
        "name": "spaCy",
        "url": "https://spacy.io/api",
        "tags": ["nlp", "自然语言处理", "分词", "命名实体识别"],
    },
    "nltk": {
        "name": "NLTK",
        "url": "https://www.nltk.org/",
        "tags": ["nlp", "自然语言处理", "文本分析"],
    },

    # 向量数据库
    "faiss": {
        "name": "Faiss",
        "url": "https://faiss.ai/",
        "tags": ["向量检索", "相似度搜索", "embedding", "vector search"],
    },
    "chromadb": {
        "name": "ChromaDB",
        "url": "https://docs.trychroma.com/",
        "tags": ["向量数据库", "embedding", "rag"],
    },
    "pinecone": {
        "name": "Pinecone",
        "url": "https://docs.pinecone.io/",
        "tags": ["向量数据库", "embedding", "云服务"],
    },
    "weaviate": {
        "name": "Weaviate",
        "url": "https://weaviate.io/developers/weaviate",
        "tags": ["向量数据库", "图数据库", "embedding"],
    },

    # 数据处理
    "pandas": {
        "name": "Pandas",
        "url": "https://pandas.pydata.org/docs/",
        "tags": ["数据分析", "数据处理", "dataframe"],
    },
    "numpy": {
        "name": "NumPy",
        "url": "https://numpy.org/doc/",
        "tags": ["数值计算", "矩阵运算", "科学计算"],
    },
    "scikit-learn": {
        "name": "scikit-learn",
        "url": "https://scikit-learn.org/stable/",
        "tags": ["机器学习", "分类", "回归", "聚类"],
    },

    # Web 框架
    "fastapi": {
        "name": "FastAPI",
        "url": "https://fastapi.tiangolo.com/",
        "tags": ["web", "api", "异步", "python"],
    },
    "flask": {
        "name": "Flask",
        "url": "https://flask.palletsprojects.com/",
        "tags": ["web", "api", "python"],
    },

    # 其他工具
    "streamlit": {
        "name": "Streamlit",
        "url": "https://docs.streamlit.io/",
        "tags": ["可视化", "web应用", "数据应用"],
    },
    "gradio": {
        "name": "Gradio",
        "url": "https://www.gradio.app/docs",
        "tags": ["ui", "demo", "机器学习界面"],
    },
    "mlflow": {
        "name": "MLflow",
        "url": "https://mlflow.org/docs/latest/index.html",
        "tags": ["mlops", "实验跟踪", "模型管理", "机器学习"],
    },
    "wandb": {
        "name": "Weights & Biases",
        "url": "https://docs.wandb.ai/",
        "tags": ["mlops", "实验跟踪", "可视化", "机器学习"],
    },
    "dvc": {
        "name": "DVC (Data Version Control)",
        "url": "https://dvc.org/doc",
        "tags": ["mlops", "数据版本控制", "模型版本控制", "机器学习"],
    },
}


def search_docs(topic: str, max_results: int = 10) -> list[dict]:
    """根据主题搜索相关文档。

    Args:
        topic: 搜索主题（支持中英文）
        max_results: 最多返回条数

    Returns:
        匹配的文档列表，每项包含 name, url, tags, relevance_score
    """
    topic_lower = topic.lower()
    results = []

    for key, doc in DOCS_LIBRARY.items():
        score = 0

        # 精确匹配框架名（key 或 name）
        if topic_lower in key.lower() or topic_lower in doc["name"].lower():
            score += 10

        # 标签匹配
        for tag in doc["tags"]:
            if topic_lower in tag.lower():
                score += 3
            # 部分匹配（如搜"学习"能匹配"强化学习"）
            elif topic_lower in tag.lower() or tag.lower() in topic_lower:
                score += 1

        if score > 0:
            results.append({
                "name": doc["name"],
                "url": doc["url"],
                "tags": doc["tags"],
                "relevance_score": score,
            })

    # 按相关度降序排列
    results.sort(key=lambda x: x["relevance_score"], reverse=True)
    return results[:max_results]
