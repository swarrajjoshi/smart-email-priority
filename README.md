# Smart Email Priority Sorter

### Quick Start
```bash
python -m venv .venv && source .venv/bin/activate 
pip install -r requirements.txt
python -m nltk.downloader punkt stopwords
python -m pip install joblib
python -m src.train_classifier          
streamlit run app.py                   