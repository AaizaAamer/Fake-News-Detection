# Fake-News-Detection (English + Urdu)

Classifies news articles as Fake or Real in English and Urdu using TF-IDF + a classical ML voting ensemble, with a Streamlit web app for predictions.

Features

- Automatic language detection (English vs Urdu)
- TF-IDF + Logistic Regression / Naive Bayes / SVM / Random Forest voting ensemble per language
- Optional transformer fine-tuning (DistilBERT for English, mBERT for Urdu) for comparison
- Trust score (0–100) with a human-readable reliability label
- LIME explainability for predictions
- Streamlit UI with light/dark theme


## Technologies Used

- Python
- Streamlit
- Scikit-learn
- Pandas
- NumPy
- SciPy
- Joblib
- Pickle
- TF-IDF Vectorizer
- Voting Classifier


# Datasets

## English Dataset

The English fake news dataset can be downloaded from Kaggle:

https://www.kaggle.com/datasets/razanaqvi14/real-and-fake-news

## Urdu Dataset

The Urdu dataset is already included in this repository.


# Create a Virtual Environment

## Windows

```bash
python -m venv .venv
```

Activate the environment

```bash
.venv\Scripts\activate
```

---

## macOS / Linux

```bash
python3 -m venv .venv
```

Activate

```bash
source .venv/bin/activate
```

---

# Install Dependencies

```bash
pip install -r requirements.txt
```

---

# Running the Application

Run the Streamlit application:

```bash
streamlit run streamlit_app.py
```


# Training the Model

Model training is performed in

```
FakeNewsDetection.ipynb
```

The notebook includes:

- Data loading
- Data cleaning
- Text preprocessing
- Language-specific preprocessing
- Stopword removal
- TF-IDF feature extraction
- Model training
- Model evaluation
- Saving trained models as `.pkl` files

After running the notebook successfully, the following files will be generated automatically:

```
en_voting_model.pkl
en_tfidf_vectorizer.pkl
ur_voting_model.pkl
ur_tfidf_vectorizer.pkl
```

# How the System Works

1. The user enters a news article in English or Urdu.
2. The application automatically detects the language (or uses the manually selected language).
3. The input text is cleaned and preprocessed using language-specific preprocessing techniques.
4. The processed text is converted into numerical representations using the appropriate feature extraction method (e.g., TF-IDF for traditional machine learning models or tokenization for transformer-based models).
5. The selected trained model (such as a Voting Classifier or Transformer model) analyzes the processed input and predicts whether the news is **Real** or **Fake**.
6. The application displays:
   - Prediction
   - Confidence Score
   - Trust Score
   - Reliability Category
   - Processed Text

---


# Important Notes

- The application predicts news credibility based on patterns learned during training.
- It does **not** verify news from live internet sources.
- Very recent news may not always be classified accurately unless the model is retrained with updated datasets.
- The application supports both English and Urdu news articles.

---

# Future Improvements

- Live news verification using News APIs
- Additional language support


